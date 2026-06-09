import os, numpy as np, torch
from core.config import SMPLX_DIR

# SMPL-X joint indices
_JOINT_JAW  = 22   # jaw (chin 근처)
_JOINT_LEYE = 23   # left eyeball center
_JOINT_REYE = 24   # right eyeball center

# 51개 정적 face landmark 중 주요 인덱스 (lmk_faces_idx 기준)
# template 좌표계: positive X = person's left side
_LMK_LEYE_OUTER = 28   # x=+0.045 → left eye outer corner
_LMK_REYE_OUTER = 19   # x=-0.045 → right eye outer corner
_LMK_FACE_L     = 9    # x=+0.061 → leftmost face (left eyebrow outer)
_LMK_FACE_R     = 0    # x=-0.061 → rightmost face (right eyebrow outer)
_LMK_NOSE_TIP   = 16   # x=0.000 y=0.267 → nose center/base
_LMK_LMOUTH     = 37   # x=+0.024 → left mouth corner
_LMK_RMOUTH     = 31   # x=-0.024 → right mouth corner

# MediaPipe 랜드마크명 → SMPL-X joint index
_LMK_TO_JOINT = [
    ("chin",            _JOINT_JAW),
    ("left_eye_outer",  _JOINT_LEYE),
    ("left_eye",        _JOINT_LEYE),
    ("right_eye_outer", _JOINT_REYE),
    ("right_eye",       _JOINT_REYE),
]


def _apply_hw_shape(betas, height_cm, weight_kg):
    """키·체중 → 체형 beta 반영. beta[0]=키/비율, beta[1]=체중/둘레(BMI)."""
    b = betas.clone()
    if height_cm:
        # 키 편차 → 비율 (정규화로 절대크기는 1.7m 고정, 비율만 반영)
        b[0, 0] = float(np.clip((float(height_cm) - 170.0) / 12.0, -3.0, 3.0))
    if height_cm and weight_kg:
        h_m = float(height_cm) / 100.0
        bmi = float(weight_kg) / (h_m * h_m)
        # BMI 22(표준)=0, 둘레 scale 0.30, 범위 [-3,3]
        b[0, 1] = float(np.clip((bmi - 22.0) * 0.30, -3.0, 3.0))
        print(f"[Step2] BMI={bmi:.1f} → beta0(키)={b[0,0].item():+.2f} "
              f"beta1(체중)={b[0,1].item():+.2f}")
    elif height_cm:
        print(f"[Step2] 키 반영 → beta0={b[0,0].item():+.2f} (체중 미입력)")
    return b


def fit_smplx(analysis: dict, gender: str, job_id: str,
              height_cm: float | None = None, weight_kg: float | None = None) -> dict:
    import smplx

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[Step2] SMPL-X 피팅 (device={device}, gender={gender})")

    model = smplx.create(
        str(SMPLX_DIR),
        model_type="smplx",
        gender=gender,
        num_betas=10,
        num_expression_coeffs=10,
        use_pca=False,
        use_face_contour=True,
        flat_hand_mean=True,
        ext="npz",
    ).to(device)

    global_orient = torch.tensor([[0.0, 0.0, 0.0]], dtype=torch.float32).to(device)
    body_pose     = torch.zeros(1, 63, dtype=torch.float32).to(device)
    body_pose[0, 47] = -70 * np.pi / 180
    body_pose[0, 50] =  70 * np.pi / 180
    body_pose[0, 53] = -5 * np.pi / 180
    body_pose[0, 56] =  5 * np.pi / 180

    face_data = analysis.get("face_data")

    # 머리 방향 추정 → neck/head joint 적용
    _apply_head_pose(body_pose, face_data)

    # jaw(입 열림) + expression 추정
    jaw_pose   = _make_jaw_pose(face_data, device)
    expression = _make_expression(face_data, device)

    if face_data is not None and face_data.get("landmarks"):
        betas = _optimize_betas(
            model, device, analysis, face_data,
            global_orient, body_pose, expression, jaw_pose,
        )
    else:
        betas = torch.tensor(analysis["betas"], dtype=torch.float32).unsqueeze(0).to(device)

    # 키·체중(BMI)으로 체형 beta 덮어쓰기 (입력 시) → 둘레/비율 반영
    betas = _apply_hw_shape(betas, height_cm, weight_kg)

    with torch.no_grad():
        output = model(
            betas=betas,
            global_orient=global_orient,
            body_pose=body_pose,
            jaw_pose=jaw_pose,
            expression=expression,
            return_verts=True,
        )

    vertices = output.vertices[0].cpu().numpy()
    joints   = output.joints[0].cpu().numpy()
    faces    = model.faces.astype(np.int32)

    foot_y = vertices[:, 1].min()
    vertices[:, 1] -= foot_y
    joints[:, 1]   -= foot_y
    scale = 1.7 / vertices[:, 1].max()
    vertices *= scale
    joints   *= scale
    cx = (vertices[:, 0].max() + vertices[:, 0].min()) / 2
    cz = (vertices[:, 2].max() + vertices[:, 2].min()) / 2
    vertices[:, 0] -= cx
    vertices[:, 2] -= cz

    # canonical body (betas=0) — 같은 정규화 적용
    v_tmpl = model.v_template.detach().cpu().numpy().copy()
    v_tmpl[:, 1] -= foot_y
    v_tmpl *= scale
    v_tmpl[:, 0] -= cx
    v_tmpl[:, 2] -= cz

    debug_dir = f"outputs/debug/{job_id}"
    os.makedirs(debug_dir, exist_ok=True)
    _save_ply(vertices, faces, f"{debug_dir}/smplx.ply")

    print(f"[Step2] 완료: {len(vertices)}개 버텍스")
    return {
        "vertices":   vertices,
        "v_template": v_tmpl,
        "faces":      faces,
        "joints":     joints,
        "betas":      betas.detach().cpu().numpy()[0],
        "gender":     gender,
        "scale":      scale,
    }


def _apply_head_pose(body_pose, face_data):
    """랜드마크 비대칭에서 목/머리 yaw·pitch 추정 → body_pose에 직접 기록"""
    if face_data is None:
        return
    lmks = face_data.get("landmarks", {})
    lc   = lmks.get("left_cheek")
    rc   = lmks.get("right_cheek")
    ns   = lmks.get("nose_tip", lmks.get("nose_bridge"))
    fw   = face_data.get("face_width", 0.0)

    # Yaw: 코가 얼굴 좌우 중심에서 얼마나 치우쳤는지 (좌우 고개 방향)
    yaw = 0.0
    if lc and rc and ns and fw > 0:
        center_x  = (lc[0] + rc[0]) / 2.0
        yaw = float(np.clip((ns[0] - center_x) / fw * 1.2, -0.25, 0.25))

    # Pitch: forehead~chin 내에서 코 위치 비율 (고개 숙임/젖힘)
    pitch = 0.0
    fh = lmks.get("forehead")
    ch = lmks.get("chin")
    fh_h = face_data.get("face_height", 0.0)
    if fh and ch and ns and fh_h > 0:
        nose_frac = (ns[1] - fh[1]) / fh_h   # 정면 ≈ 0.55
        pitch = float(np.clip((nose_frac - 0.55) * -0.4, -0.15, 0.10))

    # Neck joint: body_pose[33:36], Head joint: body_pose[42:45]
    # Axis-angle [X=pitch, Y=yaw, Z=0]
    body_pose[0, 33] = float(pitch * 0.4)
    body_pose[0, 34] = float(yaw   * 0.4)
    body_pose[0, 42] = float(pitch * 0.6)
    body_pose[0, 43] = float(yaw   * 0.6)
    print(f"[Step2] 머리 방향: yaw={np.degrees(yaw):.1f}°, pitch={np.degrees(pitch):.1f}°")


def _make_jaw_pose(face_data, device):
    """lip_height / eye_dist 비율로 턱 열림(jaw_pose X축) 추정"""
    jaw = torch.zeros(1, 3, dtype=torch.float32).to(device)
    if face_data is None:
        return jaw
    lip_h    = face_data.get("lip_height", 0.0)
    eye_dist = face_data.get("eye_dist",   1.0)
    if eye_dist > 0:
        jaw[0, 0] = float(np.clip(lip_h / eye_dist * 0.5, 0.0, 0.25))
    print(f"[Step2] jaw_pose: {jaw[0, 0].item():.3f} rad "
          f"({np.degrees(jaw[0, 0].item()):.1f}°)")
    return jaw


def _make_expression(face_data, device):
    """눈 열림·입 너비 비율 → SMPL-X expression 10개 파라미터"""
    expr = torch.zeros(1, 10, dtype=torch.float32).to(device)
    if face_data is None:
        return expr
    eye_open = float(face_data.get("eye_openness", 1.0))
    mouth_r  = float(face_data.get("mouth_ratio",  0.45))
    expr[0, 0] = float(np.clip((eye_open - 1.0) * 0.4, -0.5, 0.5))
    expr[0, 1] = float(np.clip((mouth_r  - 0.45) * 1.5, -0.4, 0.4))
    print(f"[Step2] expression: {expr[0, :3].detach().cpu().numpy().round(3)}")
    return expr


def _optimize_betas(model, device, analysis, face_data, global_orient, body_pose, expression, jaw_pose):
    """2D 재투영 + 얼굴 비율 최적화: betas + 카메라 파라미터 공동 최적화"""
    lmks = face_data["landmarks"]

    # 랜드마크가 어느 사진 기준인지 (얼굴 근접 사진 or 전신 사진)
    norm_w = float(face_data.get("photo_w", analysis["img_w"]))
    norm_h = float(face_data.get("photo_h", analysis["img_h"]))

    # ── 재투영 타겟 수집 (joint 기반) ─────────────────
    targets_norm, jidxs = [], []
    seen = set()
    for lmk_name, jidx in _LMK_TO_JOINT:
        if lmk_name in lmks and jidx not in seen:
            pt = lmks[lmk_name]
            targets_norm.append([pt[0] / norm_w, pt[1] / norm_h])
            jidxs.append(jidx)
            seen.add(jidx)

    if len(targets_norm) < 2:
        print("[Step2] 얼굴 랜드마크 부족 — ratio betas 사용")
        return torch.tensor(analysis["betas"], dtype=torch.float32).unsqueeze(0).to(device)

    targets_t = torch.tensor(targets_norm, dtype=torch.float32, device=device)

    # ── 얼굴 비율 타겟 ────────────────────────────────
    face_w_px   = float(face_data.get("face_width",  norm_w * 0.15))
    face_h_px   = float(face_data.get("face_height", norm_h * 0.25))
    eye_dist_px = float(face_data.get("eye_dist",    face_w_px * 0.45))
    mouth_w_px  = float(face_data.get("mouth_width", face_w_px * 0.50)) if "mouth_width" in face_data else None

    target_eye_face_ratio   = eye_dist_px   / (face_w_px + 1e-6)
    target_mouth_face_ratio = (mouth_w_px   / (face_w_px + 1e-6)) if mouth_w_px else None

    # ── 정적 face landmark 계산용 사전 준비 ──────────
    faces_t = model.faces_tensor.to(device)          # [F, 3]
    lfi_t   = model.lmk_faces_idx.to(device)         # [51]
    lbc_t   = model.lmk_bary_coords.to(device)       # [51, 3]

    # ── 최적화 변수 초기화 ────────────────────────────
    betas = torch.tensor(analysis["betas"], dtype=torch.float32, device=device).unsqueeze(0)
    betas.requires_grad_(True)

    # 카메라 초기값: face_width로 scale 추정, 얼굴 중심으로 tx/ty
    init_scale = face_w_px / norm_w / 0.18   # SMPL-X head ~0.18m wide
    if "nose_tip" in lmks:
        init_tx = lmks["nose_tip"][0] / norm_w
        init_ty_face = lmks["nose_tip"][1] / norm_h
    elif "chin" in lmks:
        init_tx = lmks["chin"][0] / norm_w
        init_ty_face = lmks["chin"][1] / norm_h
    else:
        init_tx, init_ty_face = 0.5, 0.3
    # jaw joint은 Y≈1.25m (SMPL-X 모델 공간)
    init_ty = init_ty_face + init_scale * 1.25

    cam = torch.tensor(
        [init_scale, init_tx, min(init_ty, 2.0)],
        dtype=torch.float32, device=device, requires_grad=True,
    )

    opt = torch.optim.Adam([
        {"params": [betas], "lr": 0.02},
        {"params": [cam],   "lr": 0.05},
    ])

    print(f"[Step2] 얼굴 최적화 ({len(targets_norm)}pt reproj + ratio, {device})")

    for i in range(200):
        opt.zero_grad()

        out   = model(betas=betas, global_orient=global_orient, body_pose=body_pose,
                      jaw_pose=jaw_pose, expression=expression, return_verts=True)
        verts = out.vertices[0]    # [10475, 3]
        j3d   = out.joints[0]      # [55, 3]

        # ─ 재투영 손실 ─────────────────────────────────
        sel  = j3d[jidxs]          # [N, 3]
        proj = torch.stack([
            cam[0] * sel[:, 0] + cam[1],
           -cam[0] * sel[:, 1] + cam[2],
        ], dim=1)
        loss_reproj = ((proj - targets_t) ** 2).mean()

        # ─ 얼굴 비율 손실 (3D shape space) ────────────
        lmk_verts = verts[faces_t[lfi_t]]            # [51, 3, 3]
        lmk3d = (lmk_verts * lbc_t.unsqueeze(-1)).sum(dim=1)  # [51, 3]

        face_w_3d  = (lmk3d[_LMK_FACE_L, 0] - lmk3d[_LMK_FACE_R, 0]).abs()
        eye_dist_3d = (j3d[_JOINT_LEYE, 0]  - j3d[_JOINT_REYE, 0]).abs()

        ratio_3d   = eye_dist_3d / (face_w_3d + 1e-6)
        loss_ratio = (ratio_3d - target_eye_face_ratio) ** 2

        if target_mouth_face_ratio is not None:
            mouth_w_3d  = (lmk3d[_LMK_LMOUTH, 0] - lmk3d[_LMK_RMOUTH, 0]).abs()
            loss_ratio += (mouth_w_3d / (face_w_3d + 1e-6) - target_mouth_face_ratio) ** 2

        loss_reg = (betas ** 2).mean() * 0.005

        loss = loss_reproj + loss_ratio * 0.5 + loss_reg
        loss.backward()
        opt.step()

        if i % 50 == 0:
            print(f"  iter {i:3d}: reproj={loss_reproj.item():.5f} ratio={loss_ratio.item():.5f}")

    print(f"[Step2] 최적화 완료 betas={betas.detach().cpu().numpy()[0, :5].round(2)}")
    return betas.detach()


def _save_ply(v, f, path):
    import trimesh
    trimesh.Trimesh(vertices=v, faces=f).export(path)
