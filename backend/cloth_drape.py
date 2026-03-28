"""
cloth_drape.py
==============
SMPL-X 메시 위에 의상 메시를 드레이핑(입히기)하는 모듈.

실제 물리 시뮬레이션(ClothSim/NVIDIA PhysX)이 없으면
- SMPL-X vertex segmentation 으로 상의/하의 영역 분리
- 각 영역 vertex를 cloth color로 재색칠
- 약간 바깥쪽으로 offset (의상 두께 표현)
- 주름 displacement 추가

진짜 cloth simulation이 필요하면:
  pip install diffsim  or  open3d + cloth sim
"""

from __future__ import annotations

import math
import numpy as np
from pathlib import Path

# SMPL-X vertex segmentation JSON (패키지에 포함되어 있음)
# smplx 설치 후: smplx/smplx_vertex_segmentation.json
try:
    import json, smplx
    _SMPLX_PKG_DIR = Path(smplx.__file__).parent
    _SEG_PATH = _SMPLX_PKG_DIR / "smplx_vert_segmentation.json"
    if _SEG_PATH.exists():
        with open(_SEG_PATH) as f:
            SMPLX_SEGMENTATION = json.load(f)
    else:
        SMPLX_SEGMENTATION = None
except Exception:
    SMPLX_SEGMENTATION = None


# 수동 fallback: SMPL-X 6890 vertex의 신체 부위별 인덱스 범위 (근사)
MANUAL_REGIONS = {
    # (start, end) — 근사값, 실제 segmentation 없을 때 사용
    "head":          (0,    410),
    "neck":          (410,  500),
    "left_arm":      (1350, 1800),
    "right_arm":     (4000, 4450),
    "left_forearm":  (1800, 2100),
    "right_forearm": (4450, 4750),
    "left_hand":     (2100, 2500),
    "right_hand":    (4750, 5150),
    "torso":         (500,  1350),
    "torso_back":    (3000, 4000),
    "left_thigh":    (1000, 1350),
    "right_thigh":   (3500, 3800),
    "left_leg":      (5150, 5750),
    "right_leg":     (5750, 6300),
    "left_foot":     (5750, 6000),
    "right_foot":    (6300, 6600),
}


CLOTH_PARTS = {
    "tshirt": ["torso", "torso_back", "left_arm", "right_arm"],
    "longsleeve": ["torso", "torso_back", "left_arm", "right_arm", "left_forearm", "right_forearm"],
    "hoodie":  ["torso", "torso_back", "left_arm", "right_arm", "left_forearm", "right_forearm"],
    "jacket":  ["torso", "torso_back", "left_arm", "right_arm", "left_forearm", "right_forearm"],
    "dress":   ["torso", "torso_back", "left_thigh", "right_thigh"],
    "pants":   ["left_thigh", "right_thigh", "left_leg", "right_leg"],
    "vest":    ["torso", "torso_back"],
    "coat":    ["torso", "torso_back", "left_arm", "right_arm", "left_forearm", "right_forearm",
                "left_thigh", "right_thigh"],
}


def _get_region_indices(region_name: str, num_verts: int) -> np.ndarray:
    """
    신체 부위 이름 → vertex index 배열.
    SMPL-X segmentation JSON이 있으면 그걸 사용, 없으면 manual range.
    """
    if SMPLX_SEGMENTATION and region_name in SMPLX_SEGMENTATION:
        return np.array(SMPLX_SEGMENTATION[region_name], dtype=np.int64)

    if region_name in MANUAL_REGIONS:
        s, e = MANUAL_REGIONS[region_name]
        return np.arange(min(s, num_verts), min(e, num_verts), dtype=np.int64)

    return np.array([], dtype=np.int64)


def hex_to_rgb01(hex_color: str) -> list:
    h = hex_color.lstrip("#")
    return [int(h[0:2],16)/255, int(h[2:4],16)/255, int(h[4:6],16)/255]


def drape_cloth(
    vertices:    np.ndarray,    # (V, 3)  SMPL-X 버텍스
    faces:       np.ndarray,    # (F, 3)
    cloth_style: str,           # "tshirt" | "hoodie" | ...
    cloth_color: str,           # "#rrggbb"
    skin_tone:   str = "medium",
    tightness:   float = 0.5,   # 0=loose 1=tight
    length_adj:  int   = 0,     # cm 보정
) -> dict:
    """
    SMPL-X vertices 위에 의상을 입혀 새 vertex colour + offset을 반환.

    Returns
    -------
    dict:
      vertex_colors : (V, 3) float32  0-1
      vertices      : (V, 3) float32  offset 적용된 위치
      cloth_mask    : (V,)   bool     의상이 입혀진 vertex
    """
    from smpl_body import SKIN_TONES

    V = len(vertices)
    skin_rgb = np.array(SKIN_TONES.get(skin_tone, SKIN_TONES["medium"]), dtype=np.float32)
    cloth_rgb = np.array(hex_to_rgb01(cloth_color), dtype=np.float32)

    # 기본: 모든 vertex 피부색
    vc = np.tile(skin_rgb, (V, 1)).astype(np.float32)

    # 의상 부위 목록
    parts = CLOTH_PARTS.get(cloth_style, CLOTH_PARTS["tshirt"])

    cloth_mask = np.zeros(V, dtype=bool)
    for part in parts:
        idx = _get_region_indices(part, V)
        if len(idx) == 0:
            continue
        cloth_mask[idx] = True
        vc[idx] = cloth_rgb

    # ── 의상 offset (바깥쪽으로 살짝 팽창) ─────────────────────
    import trimesh
    mesh_tm  = trimesh.Trimesh(vertices=vertices, faces=faces, process=False)
    normals  = mesh_tm.vertex_normals           # (V, 3)

    offset_amount = 0.007 * (1.0 + (1.0 - tightness) * 0.5)  # meters
    new_verts = vertices.copy()
    new_verts[cloth_mask] += normals[cloth_mask] * offset_amount

    # ── 주름 displacement ───────────────────────────────────────
    # 가슴/허리 경계에 미세 wave 적용
    if cloth_mask.any():
        y_coords = new_verts[cloth_mask, 1]
        y_min, y_max = y_coords.min(), y_coords.max()
        y_norm = (y_coords - y_min) / max(y_max - y_min, 1e-6)  # 0~1

        # 세로 주름 (sin wave on y)
        wrinkle_amp = 0.002
        wrinkle_freq = 12.0
        wrinkle = np.sin(y_norm * wrinkle_freq * np.pi) * wrinkle_amp

        idx_cloth = np.where(cloth_mask)[0]
        new_verts[idx_cloth, 2] += wrinkle  # Z축 미세 변위

        # 주름 색상 변조 (어두운 주름선)
        shadow = 1.0 - np.abs(np.sin(y_norm * wrinkle_freq * np.pi)) * 0.08
        vc[idx_cloth] *= shadow[:, np.newaxis]

    return {
        "vertex_colors": vc,
        "vertices":      new_verts.astype(np.float32),
        "cloth_mask":    cloth_mask,
    }


def apply_vertex_texture_to_export(
    vertices: np.ndarray,
    faces:    np.ndarray,
    vertex_colors: np.ndarray,
    out_path: str | Path,
) -> Path:
    """
    vertex colour가 적용된 메시를 .glb 로 내보냄.
    Three.js GLTFLoader 로 직접 로드 가능.
    """
    import trimesh
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    vc_255 = np.clip(vertex_colors * 255, 0, 255).astype(np.uint8)
    alpha  = np.full((len(vertices), 1), 255, dtype=np.uint8)
    vc_rgba = np.hstack([vc_255, alpha])

    mesh_tm = trimesh.Trimesh(vertices=vertices, faces=faces, process=False)
    mesh_tm.visual.vertex_colors = vc_rgba

    glb_path = out_path.with_suffix(".glb")
    mesh_tm.export(str(glb_path), file_type="glb")
    return glb_path
