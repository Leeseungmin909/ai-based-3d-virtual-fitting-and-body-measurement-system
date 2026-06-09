import cv2
import numpy as np
from core.utils import imread_safe

# 1.7m 정규화 기준 Y 임계값 (meter)
_SHIRT_Y_MIN  = 0.90   # 허리 위
_SHIRT_Y_MAX  = 1.42   # 어깨 아래 (목/얼굴 제외)
_PANTS_Y_MIN  = 0.05   # 발목 위
_PANTS_Y_MAX  = 0.90   # 허리 아래

_DEFAULT_PANTS_COLOR = (45, 65, 120)   # 네이비


def compute_body_measurements(smplx_data: dict) -> dict:
    """SMPL-X 조인트·버텍스로 상의·하의 피팅용 신체 치수 계산 (1.7m 정규화 좌표)"""
    vertices = np.asarray(smplx_data["vertices"])  # [N, 3]
    joints   = np.asarray(smplx_data["joints"])    # [55, 3]

    vx, vy, vz = vertices[:, 0], vertices[:, 1], vertices[:, 2]

    # ── 주요 조인트 위치 ────────────────────────────────
    pelvis_y   = float(joints[0,  1])               # 골반 Y
    shoulder_y = float((joints[16, 1] + joints[17, 1]) / 2)   # 어깨 평균 Y
    # 어깨 X 절댓값 → 팔 제외 필터 기준
    shoulder_hw = float(max(abs(joints[16, 0]), abs(joints[17, 0])))
    # 엉덩이 X 절댓값
    hip_hw = float(max(abs(joints[1, 0]), abs(joints[2, 0])))

    # ── 상의 영역: 골반~어깨, 팔 제외(|X| < shoulder_hw * 1.15) ──
    shirt_mask = (
        (vy >= pelvis_y * 0.92) &
        (vy <= shoulder_y * 1.03) &
        (np.abs(vx) < shoulder_hw * 1.15)
    )

    # ── 하의 영역: 발~골반, 엉덩이 폭 기준(|X| < hip_hw * 1.2) ──
    pants_mask = (
        (vy >= 0.02) &
        (vy <= pelvis_y * 1.05) &
        (np.abs(vx) < hip_hw * 1.2)
    )

    def _measure(mask):
        if mask.sum() < 20:
            return None
        y_lo, y_hi = float(vy[mask].min()), float(vy[mask].max())
        return {
            "width": round(float(vx[mask].max() - vx[mask].min()), 4),
            "depth": round(float(vz[mask].max() - vz[mask].min()), 4),
            "y_min": round(y_lo, 4),
            "y_max": round(y_hi, 4),
            "y_mid": round((y_lo + y_hi) / 2, 4),
        }

    # ── 팔 캡슐 데이터 (어깨→팔꿈치→손목) ─────────────────────────────
    def _arm_radius(ja, jb):
        """팔 세그먼트 축 기준 버텍스 거리 중앙값으로 팔 두께 추정"""
        ab = jb - ja
        ab_len = np.linalg.norm(ab)
        if ab_len < 0.01:
            return 0.05
        ab_u = ab / ab_len
        t = np.clip(np.dot(vertices - ja, ab_u), 0, ab_len)
        closest = ja + t[:, None] * ab_u
        dists = np.linalg.norm(vertices - closest, axis=1)
        near = dists < 0.12
        return round(float(np.percentile(dists[near], 70)), 4) if near.sum() > 5 else 0.05

    j = joints  # 단축
    arm_joints = {
        "left_shoulder":  [round(float(v), 4) for v in j[16]],
        "left_elbow":     [round(float(v), 4) for v in j[18]],
        "left_wrist":     [round(float(v), 4) for v in j[20]],
        "right_shoulder": [round(float(v), 4) for v in j[17]],
        "right_elbow":    [round(float(v), 4) for v in j[19]],
        "right_wrist":    [round(float(v), 4) for v in j[21]],
    }
    arm_radius = {
        "left_upper":  _arm_radius(j[16], j[18]),
        "left_lower":  _arm_radius(j[18], j[20]),
        "right_upper": _arm_radius(j[17], j[19]),
        "right_lower": _arm_radius(j[19], j[21]),
    }

    result = {
        "height":     round(float(vy.max()), 4),
        "neck_y":     round(float(joints[12, 1]), 4),   # 목(neck) 조인트 Y → 카라 시작점
        "shirt":      _measure(shirt_mask),
        "pants":      _measure(pants_mask),
        "arm_joints": arm_joints,
        "arm_radius": arm_radius,
    }
    print(f"[Measure] shirt={result['shirt']}")
    print(f"[Measure] pants={result['pants']}")
    print(f"[Measure] arm_radius={arm_radius}")
    return result


def extract_clothing_color(photo_path: str) -> tuple | None:
    """옷 사진에서 주색상 추출 (배경 흰/검 제외, 중앙값 RGB)."""
    img = imread_safe(photo_path)
    if img is None:
        return None
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    h, w = img_rgb.shape[:2]

    y1, y2 = int(h * 0.15), int(h * 0.85)
    x1, x2 = int(w * 0.15), int(w * 0.85)
    region = img_rgb[y1:y2, x1:x2].reshape(-1, 3).astype(np.float32)

    brightness = region.mean(axis=1)
    mask = (brightness > 25) & (brightness < 245)
    if mask.sum() < 50:
        mask = np.ones(len(region), dtype=bool)

    dominant = np.median(region[mask], axis=0).astype(np.uint8)
    color = tuple(int(c) for c in dominant)
    print(f"[Step3] 옷 색상 추출: #{dominant[0]:02x}{dominant[1]:02x}{dominant[2]:02x}")
    return color


def extract_vertex_colors(
    photo_path: str,
    analysis: dict,
    smplx_data: dict,
    shirt_color: tuple | None = None,   # None = 피부색 유지
    pants_color: tuple | None = None,   # None = 피부색 유지
) -> np.ndarray:
    """Per-vertex RGB: 전신 피부색 기본, GLB 없을 때도 피부색 유지"""
    skin_color = _extract_skin_color(photo_path, analysis)
    vertices   = smplx_data["vertices"]
    n = len(vertices)
    colors = np.tile(skin_color[:3], (n, 1)).astype(np.uint8)

    vy = vertices[:, 1]

    # 하의 색 적용 (None이면 피부색 유지)
    if pants_color is not None:
        pants_mask = (vy >= _PANTS_Y_MIN) & (vy < _PANTS_Y_MAX)
        colors[pants_mask] = np.array(pants_color, dtype=np.uint8)

    # 상의 색 적용 (None이면 피부색 유지)
    if shirt_color is not None:
        shirt_mask = (vy >= _SHIRT_Y_MIN) & (vy < _SHIRT_Y_MAX)
        colors[shirt_mask] = np.array(shirt_color, dtype=np.uint8)

    print(f"[Step3] 버텍스 컬러: 피부색 #{skin_color[0]:02x}{skin_color[1]:02x}{skin_color[2]:02x}"
          + (" (상의=피부색)" if shirt_color is None else "")
          + (" (하의=피부색)" if pants_color is None else ""))
    return colors


def _extract_skin_color(photo_path: str, analysis: dict) -> np.ndarray:
    img = imread_safe(photo_path)
    if img is None:
        return np.array([210, 180, 155], dtype=np.uint8)

    img_rgb   = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    h, w      = img.shape[:2]
    body_data = analysis.get("body_data")
    if body_data is None:
        return np.array([210, 180, 155], dtype=np.uint8)

    samples = []
    for key in ["left_wrist", "right_wrist", "nose"]:
        pt = body_data.get(key)
        if pt is None:
            continue
        x = int(np.clip(pt[0], 5, w - 6))
        y = int(np.clip(pt[1], 5, h - 6))
        patch = img_rgb[y - 5:y + 5, x - 5:x + 5]
        if patch.size > 0:
            samples.append(patch.reshape(-1, 3))

    if samples:
        return np.median(np.vstack(samples), axis=0).astype(np.uint8)
    return np.array([210, 180, 155], dtype=np.uint8)
