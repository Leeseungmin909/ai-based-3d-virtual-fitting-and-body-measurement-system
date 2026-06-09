import os, cv2, numpy as np
import mediapipe as mp
from core.utils import imread_safe, imwrite_safe

def analyze_photo(photo_path: str, job_id: str, face_photo_path: str = None) -> dict:
    """전신 사진에서 체형 + 얼굴 랜드마크 추출. 얼굴 사진 별도 제공 시 고해상도 분석."""

    img = imread_safe(photo_path)
    if img is None:
        raise RuntimeError(f"사진을 읽을 수 없습니다: {photo_path}")

    h, w = img.shape[:2]
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    # ── 1. 전신 포즈 추출 ──────────────────────────────
    body_data = extract_body(img_rgb, h, w)

    # ── 2. 얼굴 랜드마크 추출 ─────────────────────────
    if face_photo_path:
        face_data = extract_face_from_photo(face_photo_path)
        if face_data is None:
            print("[Step1] 얼굴 사진 감지 실패 — 전신 사진으로 재시도")
            face_data = extract_face(img_rgb, h, w, body_data)
    else:
        face_data = extract_face(img_rgb, h, w, body_data)

    # ── 3. 체형 파라미터 추정 ─────────────────────────
    betas = estimate_betas(body_data, h, w)

    # ── 4. 디버그 이미지 저장 ─────────────────────────
    debug_dir = f"outputs/debug/{job_id}"
    os.makedirs(debug_dir, exist_ok=True)
    save_debug(img.copy(), body_data, face_data, f"{debug_dir}/analysis.jpg")

    print(f"[Step1] 분석 완료: body={body_data is not None}, face={face_data is not None}, betas={betas[:3]}")

    return {
        "job_id":          job_id,
        "img_h":           h,
        "img_w":           w,
        "body_data":       body_data,
        "face_data":       face_data,
        "betas":           betas.tolist(),
        "photo_path":      photo_path,
        "face_photo_path": face_photo_path,
    }


def extract_face_from_photo(face_photo_path: str) -> dict:
    """얼굴 근접 사진에서 고해상도 FaceMesh 추출 + 상세 계측"""
    img = imread_safe(face_photo_path)
    if img is None:
        return None
    h, w = img.shape[:2]
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    mp_face = mp.solutions.face_mesh
    with mp_face.FaceMesh(static_image_mode=True, max_num_faces=1,
                          refine_landmarks=True, min_detection_confidence=0.3) as fm:
        res = fm.process(img_rgb)

    if not res.multi_face_landmarks:
        return None

    lms = res.multi_face_landmarks[0].landmark

    key_indices = {
        "nose_tip":        4,   "chin":           152,
        "left_eye_outer":  33,  "right_eye_outer": 263,
        "left_eye_inner":  133, "right_eye_inner": 362,
        "left_eye_top":    159, "left_eye_bottom": 145,
        "right_eye_top":   386, "right_eye_bottom":374,
        "left_mouth":      61,  "right_mouth":     291,
        "forehead":        10,  "left_cheek":      234,
        "right_cheek":     454, "nose_bridge":     6,
        "upper_lip":       13,  "lower_lip":       14,
        "left_jaw":        172, "right_jaw":       397,
        "nose_left":       129, "nose_right":      358,
    }

    landmarks = {}
    for name, idx in key_indices.items():
        l = lms[idx]
        landmarks[name] = [float(l.x * w), float(l.y * h), float(l.z)]

    face_w   = abs(landmarks["left_cheek"][0]      - landmarks["right_cheek"][0])
    face_h   = abs(landmarks["forehead"][1]         - landmarks["chin"][1])
    eye_dist = abs(landmarks["left_eye_outer"][0]   - landmarks["right_eye_outer"][0])
    nose_len = abs(landmarks["nose_bridge"][1]       - landmarks["nose_tip"][1])
    nose_w   = abs(landmarks["nose_left"][0]         - landmarks["nose_right"][0])
    mouth_w  = abs(landmarks["left_mouth"][0]        - landmarks["right_mouth"][0])
    eye_h    = (abs(landmarks["left_eye_top"][1]  - landmarks["left_eye_bottom"][1]) +
                abs(landmarks["right_eye_top"][1] - landmarks["right_eye_bottom"][1])) / 2
    jaw_w    = abs(landmarks["left_jaw"][0]          - landmarks["right_jaw"][0])
    lip_h    = abs(landmarks["upper_lip"][1]         - landmarks["lower_lip"][1])

    print(f"[Step1] 얼굴 사진 분석: face_w={face_w:.0f}px, eye_dist={eye_dist:.0f}px")

    return {
        "landmarks":    landmarks,
        "face_width":   float(face_w),
        "face_height":  float(face_h),
        "eye_dist":     float(eye_dist),
        "nose_len":     float(nose_len),
        "nose_width":   float(nose_w),
        "mouth_width":  float(mouth_w),
        "eye_height":   float(eye_h),
        "jaw_width":    float(jaw_w),
        "lip_height":   float(lip_h),
        "face_ratio":   float(face_h / (face_w + 1e-6)),
        "nose_w_ratio": float(nose_w  / (face_w + 1e-6)),
        "eye_ratio":    float(eye_dist / (face_w + 1e-6)),
        "mouth_ratio":  float(mouth_w  / (face_w + 1e-6)),
        "jaw_ratio":    float(jaw_w    / (face_w + 1e-6)),
        "nose_len_ratio": float(nose_len / (face_h + 1e-6)),
        "eye_openness": float(eye_h / (eye_dist / 2 + 1e-6)),
        "photo_path":   face_photo_path,
        "photo_h":      h,
        "photo_w":      w,
    }


def extract_body(img_rgb, h, w):
    """MediaPipe Pose로 전신 랜드마크 추출"""
    mp_pose = mp.solutions.pose
    with mp_pose.Pose(static_image_mode=True, model_complexity=2,
                      min_detection_confidence=0.5) as pose:
        res = pose.process(img_rgb)

    if not res.pose_landmarks:
        print("[Step1] ⚠️ 전신 포즈 감지 실패 - 기본값 사용")
        return None

    lm = res.pose_landmarks.landmark

    def px(idx):
        return np.array([lm[idx].x * w, lm[idx].y * h, lm[idx].z])

    return {
        "nose":           px(0).tolist(),
        "left_shoulder":  px(11).tolist(),
        "right_shoulder": px(12).tolist(),
        "left_elbow":     px(13).tolist(),
        "right_elbow":    px(14).tolist(),
        "left_wrist":     px(15).tolist(),
        "right_wrist":    px(16).tolist(),
        "left_hip":       px(23).tolist(),
        "right_hip":      px(24).tolist(),
        "left_knee":      px(25).tolist(),
        "right_knee":     px(26).tolist(),
        "left_ankle":     px(27).tolist(),
        "right_ankle":    px(28).tolist(),
    }


def extract_face(img_rgb, h, w, body_data=None):
    """MediaPipe FaceMesh로 얼굴 랜드마크 추출.
    전신 사진에서 얼굴이 작으므로 포즈 기반 크롭 후 확대해서 감지."""

    # ── 얼굴 크롭 영역 계산 ────────────────────────────
    crop, cx1, cy1, scale = _get_face_crop(img_rgb, h, w, body_data)

    mp_face = mp.solutions.face_mesh
    face_mesh_cfg = dict(
        static_image_mode=True,
        max_num_faces=1,
        refine_landmarks=True,
        min_detection_confidence=0.3,
    )

    res = None
    # 1차: 크롭 이미지로 시도
    if crop is not None:
        with mp_face.FaceMesh(**face_mesh_cfg) as fm:
            res = fm.process(crop)

    # 2차: 크롭 실패 시 전체 이미지로 재시도 (신뢰도 낮춰서)
    if res is None or not res.multi_face_landmarks:
        with mp_face.FaceMesh(**face_mesh_cfg) as fm:
            res = fm.process(img_rgb)
        cx1, cy1, scale = 0, 0, 1.0

    if not res.multi_face_landmarks:
        print("[Step1] ⚠️ 얼굴 감지 실패 - 기본값 사용")
        return None

    lms = res.multi_face_landmarks[0].landmark
    ch = crop.shape[0] if crop is not None and scale != 1.0 else h
    cw = crop.shape[1] if crop is not None and scale != 1.0 else w

    key_indices = {
        "nose_tip":    4,
        "chin":        152,
        "left_eye":    33,
        "right_eye":   263,
        "left_mouth":  61,
        "right_mouth": 291,
        "forehead":    10,
        "left_cheek":  234,
        "right_cheek": 454,
        "nose_bridge": 6,
        "upper_lip":   13,
        "lower_lip":   14,
    }

    landmarks = {}
    for name, idx in key_indices.items():
        l = lms[idx]
        # 크롭 좌표 → 원본 이미지 좌표로 역변환
        ox = l.x * cw / scale + cx1
        oy = l.y * ch / scale + cy1
        landmarks[name] = [float(ox), float(oy), float(l.z)]

    face_width  = abs(landmarks["left_cheek"][0]  - landmarks["right_cheek"][0])
    face_height = abs(landmarks["forehead"][1]    - landmarks["chin"][1])
    eye_dist    = abs(landmarks["left_eye"][0]    - landmarks["right_eye"][0])
    nose_len    = abs(landmarks["nose_bridge"][1] - landmarks["nose_tip"][1])

    print(f"[Step1] 얼굴 감지 성공: width={face_width:.1f}px, eye_dist={eye_dist:.1f}px")
    return {
        "landmarks":   landmarks,
        "face_width":  float(face_width),
        "face_height": float(face_height),
        "eye_dist":    float(eye_dist),
        "nose_len":    float(nose_len),
        "face_ratio":  float(face_height / (face_width + 1e-6)),
    }


def _get_face_crop(img_rgb, h, w, body_data):
    """포즈 랜드마크 기반으로 얼굴 영역 크롭 + 확대.
    Returns: (cropped_img, x1, y1, scale) or (None, 0, 0, 1.0)"""
    if body_data is None:
        return None, 0, 0, 1.0

    nose  = body_data.get("nose")
    ls    = body_data.get("left_shoulder")
    rs    = body_data.get("right_shoulder")
    if nose is None or ls is None or rs is None:
        return None, 0, 0, 1.0

    nose  = np.array(nose)
    ls    = np.array(ls)
    rs    = np.array(rs)

    # 어깨 너비 기반으로 얼굴 크롭 크기 추정
    shoulder_w = abs(ls[0] - rs[0])
    face_size  = max(shoulder_w * 0.85, 60)  # 어깨 너비의 85% 정도
    cx         = nose[0]
    cy         = nose[1]

    x1 = int(max(cx - face_size * 0.65, 0))
    y1 = int(max(cy - face_size * 0.75, 0))
    x2 = int(min(cx + face_size * 0.65, w))
    y2 = int(min(cy + face_size * 0.85, h))

    if x2 - x1 < 20 or y2 - y1 < 20:
        return None, 0, 0, 1.0

    crop = img_rgb[y1:y2, x1:x2]

    # 최소 200px 너비가 되도록 확대
    target_w = max(300, w // 4)
    scale    = target_w / (x2 - x1)
    if scale > 1.0:
        import cv2
        nh = int(crop.shape[0] * scale)
        nw = int(crop.shape[1] * scale)
        crop = cv2.resize(crop, (nw, nh), interpolation=cv2.INTER_LINEAR)

    return crop, x1, y1, scale


def estimate_betas(body_data, h, w) -> np.ndarray:
    """체형 파라미터 추정 (SMPL-X PCA 공간 근사)"""
    betas = np.zeros(10)

    if body_data is None:
        return betas

    ls   = np.array(body_data["left_shoulder"])
    rs   = np.array(body_data["right_shoulder"])
    lh   = np.array(body_data["left_hip"])
    rh   = np.array(body_data["right_hip"])
    la   = np.array(body_data["left_ankle"])
    ra   = np.array(body_data["right_ankle"])
    nose = np.array(body_data["nose"])
    lw   = np.array(body_data.get("left_wrist",  ls))
    rw   = np.array(body_data.get("right_wrist", rs))

    ankle_y    = (la[1] + ra[1]) / 2.0
    shoulder_y = (ls[1] + rs[1]) / 2.0
    hip_y      = (lh[1] + rh[1]) / 2.0

    # 신체 높이 픽셀 (촬영 거리 정규화 기준)
    body_h_px     = abs(ankle_y - nose[1]) + 1e-6

    shoulder_w_px = abs(ls[0] - rs[0])
    hip_w_px      = abs(lh[0] - rh[0])

    shoulder_ratio = shoulder_w_px / body_h_px   # 평균≈0.27
    hip_ratio      = hip_w_px      / body_h_px   # 평균≈0.22
    torso_ratio    = abs(hip_y   - shoulder_y) / body_h_px  # 평균≈0.29
    leg_ratio      = abs(ankle_y - hip_y)      / body_h_px  # 평균≈0.51
    arm_len_ratio  = abs(lw[1]   - ls[1])      / body_h_px  # 평균≈0.35
    sh_hip         = shoulder_w_px / (hip_w_px + 1e-6)      # 평균≈1.20

    # beta[0]: 전반 풍만함 (어깨+엉덩이 평균 너비) — 가장 시각적 영향 큼
    avg_width = (shoulder_ratio + hip_ratio) / 2.0  # 평균≈0.245
    betas[0]  = float(np.clip((avg_width - 0.245) * 30.0, -3.0, 3.0))

    # beta[1]: 다리 길이 비율
    betas[1]  = float(np.clip((leg_ratio - 0.51) * 22.0, -3.0, 3.0))

    # beta[2]: 상체 길이 비율
    betas[2]  = float(np.clip((torso_ratio - 0.29) * 22.0, -2.5, 2.5))

    # beta[3]: 어깨 너비
    betas[3]  = float(np.clip((shoulder_ratio - 0.27) * 26.0, -3.0, 3.0))

    # beta[4]: 엉덩이 너비
    betas[4]  = float(np.clip((hip_ratio - 0.22) * 26.0, -3.0, 3.0))

    # beta[5]: 팔 길이
    betas[5]  = float(np.clip((arm_len_ratio - 0.35) * 18.0, -2.5, 2.5))

    # beta[6]: 어깨/엉덩이 비율 (역삼각형 vs 배모양)
    betas[6]  = float(np.clip((sh_hip - 1.20) * 6.0, -2.5, 2.5))

    # beta[7]: 하체 비중 (다리+엉덩이 조합)
    lower_ratio = (leg_ratio + hip_ratio) / 2.0
    betas[7]  = float(np.clip((lower_ratio - 0.365) * 18.0, -2.5, 2.5))

    print(f"[Step1] betas: {np.round(betas, 2).tolist()}")
    return betas


def save_debug(img, body_data, face_data, path):
    """디버그 이미지 저장"""
    if body_data:
        for name, pt in body_data.items():
            x, y = int(pt[0]), int(pt[1])
            cv2.circle(img, (x, y), 5, (0, 255, 0), -1)

    if face_data:
        for name, pt in face_data["landmarks"].items():
            x, y = int(pt[0]), int(pt[1])
            cv2.circle(img, (x, y), 3, (255, 100, 0), -1)

    imwrite_safe(path, img)
