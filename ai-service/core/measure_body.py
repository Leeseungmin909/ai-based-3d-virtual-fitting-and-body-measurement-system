"""
SMPL-X 메쉬 → 실제 cm 단위 신체 치수 추출.
Java 서버 ERD(user_measurements / clothes)의 *_cm 필드와 1:1 매핑.

좌표계: step2_smplx 출력(1.7m 정규화, Y-up, 발=0). 사용자 실제 키(height_cm)로
정규화 좌표를 실측 cm로 환산한다.
"""
import numpy as np
from core.config import SMPLX_DIR

# SMPL-X body joint indices
J_PELVIS, J_LHIP, J_RHIP = 0, 1, 2
J_LKNEE, J_RKNEE         = 4, 5
J_NECK                   = 12
J_LSHO, J_RSHO           = 16, 17
J_LELB, J_RELB           = 18, 19
J_LWRI, J_RWRI           = 20, 21


def _measure_pose_mesh(betas, gender):
    """
    같은 betas로 '측정 포즈'(팔을 수평으로 벌린 T-포즈) 메쉬를 생성.
    A-포즈에선 팔이 옆구리에 붙어 몸통 폭 측정이 불가 → 팔을 벌려 분리.
    반환: (vertices, joints) — 1.7m 정규화, 발=0.
    """
    import smplx, torch
    model = smplx.create(
        str(SMPLX_DIR), model_type="smplx", gender=gender,
        num_betas=len(betas), use_pca=False, flat_hand_mean=True, ext="npz",
    )
    body_pose = torch.zeros(1, 63, dtype=torch.float32)
    # 어깨 관절(L=16→pose[45:48], R=17→pose[48:51]) Z축 회전으로 팔 수평(T-포즈) 벌림.
    # 1.6rad(~92°): 팔이 가슴/허리에서 완전히 벗어나 몸통 폭 측정 정확.
    body_pose[0, 47] = -1.6   # 왼팔 수평
    body_pose[0, 50] =  1.6   # 오른팔 수평
    with torch.no_grad():
        out = model(betas=torch.tensor(np.asarray(betas), dtype=torch.float32).unsqueeze(0),
                    body_pose=body_pose, return_verts=True)
    v = out.vertices[0].numpy().astype(np.float64)
    j = out.joints[0].numpy().astype(np.float64)
    fy = v[:, 1].min(); v[:, 1] -= fy; j[:, 1] -= fy
    s = 1.7 / v[:, 1].max(); v *= s; j *= s
    return v, j


def _central_width(xs, gap=0.025):
    """
    x=0(중심축)에서 좌우로 확장하며 첫 큰 간격(gap)에서 멈춰 '몸통 중앙 클러스터' 폭 반환.
    옆구리에 붙은 팔(몸통과 빈틈으로 분리)을 자동 제외.
    """
    xs = np.sort(np.asarray(xs))
    pos = xs[xs >= 0]
    neg = xs[xs <= 0][::-1]            # 0 → 음수 방향
    r, prev = 0.0, 0.0
    for x in pos:
        if x - prev > gap:
            break
        r, prev = x, x
    l, prev = 0.0, 0.0
    for x in neg:
        if prev - x > gap:
            break
        l, prev = x, x
    return r - l


def _xwidth(verts, y_lo, y_hi, central=True):
    """y_lo~y_hi 밴드의 정면 너비. central=True면 몸통 중앙 클러스터만(팔 제외)."""
    m = (verts[:, 1] >= y_lo) & (verts[:, 1] <= y_hi)
    if m.sum() < 5:
        return 0.0
    xs = verts[m, 0]
    return _central_width(xs) if central else float(xs.max() - xs.min())


def measure_body_cm(smplx_data: dict, height_cm: float | None = None) -> dict:
    """
    user_measurements 스키마(cm)로 신체 치수 반환.
    height_cm 없으면 정규화 키(1.7m=170cm) 기준으로 환산.
    width_*는 정면 평면 너비(X extent) 기준.
    """
    # 측정용 포즈(팔 벌림) 메쉬로 측정 — 실패 시 표시 포즈로 폴백
    betas = smplx_data.get("betas")
    try:
        if betas is not None:
            v, j = _measure_pose_mesh(betas, smplx_data.get("gender", "neutral"))
        else:
            raise ValueError("no betas")
    except Exception as _e:
        print(f"[Measure] 측정 포즈 생성 실패 → 표시 포즈 사용: {_e}")
        v = np.asarray(smplx_data["vertices"], dtype=np.float64)
        j = np.asarray(smplx_data["joints"],   dtype=np.float64)

    norm_h = float(v[:, 1].max())                 # ≈1.7
    H      = float(height_cm) if height_cm else norm_h * 100.0
    to_cm  = H / max(norm_h, 1e-6)                 # 정규화 m → 실측 cm

    sho_y    = (j[J_LSHO, 1] + j[J_RSHO, 1]) / 2
    hip_y    = (j[J_LHIP, 1] + j[J_RHIP, 1]) / 2
    pelvis_y = float(j[J_PELVIS, 1])
    sho_hw   = max(abs(j[J_LSHO, 0]), abs(j[J_RSHO, 0]))
    hip_hw   = max(abs(j[J_LHIP, 0]), abs(j[J_RHIP, 0]))

    chest_y = (sho_y + (sho_y + hip_y) / 2) / 2
    waist_y = ((sho_y + hip_y) / 2 + hip_y) / 2
    thigh_y = (hip_y + (j[J_LKNEE, 1] + j[J_RKNEE, 1]) / 2) / 2

    # 몸통 중앙 클러스터 폭(옆구리에 붙은 팔 자동 제외).
    # 어깨는 팔과 연결돼 있어 클러스터 분리 불가 → 어깨 관절 폭 기반.
    shoulder_w = _xwidth(v, sho_y * 0.985, sho_y * 1.015, central=False)
    chest_w    = _xwidth(v, chest_y * 0.97, chest_y * 1.03)
    waist_w    = _xwidth(v, waist_y * 0.97, waist_y * 1.03)
    hip_w      = _xwidth(v, hip_y  * 0.97, hip_y  * 1.03)

    # 허벅지: 한쪽(좌, x>0) 폭
    mth = (v[:, 1] >= thigh_y * 0.95) & (v[:, 1] <= thigh_y * 1.05) & (v[:, 0] > 0.02)
    thigh_w = float(v[mth, 0].max() - v[mth, 0].min()) if mth.sum() > 5 else 0.0

    # 소매 길이: 어깨→팔꿈치→손목 (좌측 3D 거리 합)
    seg = lambda a, b: float(np.linalg.norm(j[a] - j[b]))
    sleeve = seg(J_LSHO, J_LELB) + seg(J_LELB, J_LWRI)

    # 가랑이 높이(바닥 기준): 엉덩이 근처 중심축 토르소 최저점(이상치 방지 위해 밴드 제한)
    mc = (np.abs(v[:, 0]) < 0.06) & (v[:, 1] > hip_y * 0.80) & (v[:, 1] < hip_y * 1.05)
    crotch_y = float(v[mc, 1].min()) if mc.sum() > 5 else pelvis_y * 0.85

    return {
        "height_cm":         round(H, 1),
        "shoulder_width_cm": round(shoulder_w * to_cm, 1),
        "chest_width_cm":    round(chest_w * to_cm, 1),
        "sleeve_length_cm":  round(sleeve * to_cm, 1),
        "waist_width_cm":    round(waist_w * to_cm, 1),
        "hip_width_cm":      round(hip_w * to_cm, 1),
        "thigh_width_cm":    round(thigh_w * to_cm, 1),
        "crotch_cm":         round(crotch_y * to_cm, 1),
    }
