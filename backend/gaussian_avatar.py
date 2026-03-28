"""
gaussian_avatar.py
==================
SMPL-X 메시에서 3D Gaussian Splatting 초기화 포인트 클라우드를 생성하고
PLY 파일로 내보냅니다.

실제 3DGS 학습(gaussian-splatting 원본)과 연동하거나
GaussianAvatar / HumanGaussian 파이프라인과 연결 가능합니다.
"""

from __future__ import annotations

import math
import struct
from pathlib import Path

import numpy as np
from plyfile import PlyData, PlyElement


def _rotation_matrix_to_quaternion(R: np.ndarray) -> np.ndarray:
    """3×3 회전 행렬 → 쿼터니언 (w, x, y, z)."""
    trace = R[0,0] + R[1,1] + R[2,2]
    if trace > 0:
        s = 0.5 / math.sqrt(trace + 1.0)
        w = 0.25 / s
        x = (R[2,1] - R[1,2]) * s
        y = (R[0,2] - R[2,0]) * s
        z = (R[1,0] - R[0,1]) * s
    elif R[0,0] > R[1,1] and R[0,0] > R[2,2]:
        s = 2.0 * math.sqrt(1.0 + R[0,0] - R[1,1] - R[2,2])
        w = (R[2,1] - R[1,2]) / s
        x = 0.25 * s
        y = (R[0,1] + R[1,0]) / s
        z = (R[0,2] + R[2,0]) / s
    elif R[1,1] > R[2,2]:
        s = 2.0 * math.sqrt(1.0 + R[1,1] - R[0,0] - R[2,2])
        w = (R[0,2] - R[2,0]) / s
        x = (R[0,1] + R[1,0]) / s
        y = 0.25 * s
        z = (R[1,2] + R[2,1]) / s
    else:
        s = 2.0 * math.sqrt(1.0 + R[2,2] - R[0,0] - R[1,1])
        w = (R[1,0] - R[0,1]) / s
        x = (R[0,2] + R[2,0]) / s
        y = (R[1,2] + R[2,1]) / s
        z = 0.25 * s
    return np.array([w, x, y, z], dtype=np.float32)


def mesh_to_gaussian_init(
    vertices:      np.ndarray,   # (V, 3)
    faces:         np.ndarray,   # (F, 3)
    vertex_colors: np.ndarray,   # (V, 3) float 0-1
    n_gaussians:   int = 50_000,
    scale_factor:  float = 0.004,
) -> dict:
    """
    SMPL-X 메시 표면에서 n_gaussians 개의 Gaussian을 초기화합니다.

    각 Gaussian:
      - 위치(xyz):  메시 면 위의 무작위 샘플
      - 회전(rot):  면 법선 기반 쿼터니언
      - 스케일(scale): 면 크기에 비례
      - 불투명도(opacity): sigmoid 공간
      - SH 계수(sh_dc): 기본 색상

    Returns
    -------
    dict with keys: xyz, rot, scale, opacity, sh_dc
    """
    rng = np.random.default_rng(42)

    # ── 면 면적 기반 중요도 샘플링 ─────────────────────────────
    v0 = vertices[faces[:, 0]]
    v1 = vertices[faces[:, 1]]
    v2 = vertices[faces[:, 2]]

    edge1 = v1 - v0
    edge2 = v2 - v0
    cross = np.cross(edge1, edge2)
    areas = np.linalg.norm(cross, axis=1) * 0.5   # (F,)
    probs = areas / areas.sum()

    face_idx = rng.choice(len(faces), size=n_gaussians, p=probs)

    # ── 무작위 중심 좌표 (삼각형 내부 샘플링) ──────────────────
    r1 = rng.random(n_gaussians)
    r2 = rng.random(n_gaussians)
    # Barycentric 좌표
    u = 1.0 - np.sqrt(r1)
    v = np.sqrt(r1) * (1.0 - r2)
    w = np.sqrt(r1) * r2

    xyz = (u[:, None] * vertices[faces[face_idx, 0]] +
           v[:, None] * vertices[faces[face_idx, 1]] +
           w[:, None] * vertices[faces[face_idx, 2]]).astype(np.float32)

    # ── 법선 기반 쿼터니언 ────────────────────────────────────
    norms = cross[face_idx]
    norms_len = np.linalg.norm(norms, axis=1, keepdims=True) + 1e-8
    norms = norms / norms_len                             # (N, 3) 단위 법선

    # up = (0,0,1) 기준으로 회전 행렬 구성
    up = np.array([0., 0., 1.], dtype=np.float32)
    rotations = []
    for n in norms:
        n = n.astype(np.float64)
        axis = np.cross(up, n)
        axis_len = np.linalg.norm(axis)
        if axis_len < 1e-6:
            rotations.append(np.array([1., 0., 0., 0.], dtype=np.float32))
            continue
        axis /= axis_len
        angle = math.acos(np.clip(np.dot(up, n), -1, 1))
        c, s = math.cos(angle/2), math.sin(angle/2)
        rotations.append(np.array([c, axis[0]*s, axis[1]*s, axis[2]*s], dtype=np.float32))
    rot = np.array(rotations, dtype=np.float32)           # (N, 4) wxyz

    # ── 스케일 ────────────────────────────────────────────────
    face_scales = (areas[face_idx] ** 0.5) * scale_factor
    scale = np.log(face_scales[:, None].repeat(3, axis=1) + 1e-8).astype(np.float32)

    # ── Opacity (logit space) ─────────────────────────────────
    opacity_raw = np.full(n_gaussians, 0.9, dtype=np.float32)
    opacity = np.log(opacity_raw / (1 - opacity_raw))   # inverse sigmoid

    # ── SH 0차 계수 (기본 colour) ─────────────────────────────
    # Vertex colour 를 중간점 색으로 보간
    col = (u[:, None] * vertex_colors[faces[face_idx, 0]] +
           v[:, None] * vertex_colors[faces[face_idx, 1]] +
           w[:, None] * vertex_colors[faces[face_idx, 2]]).astype(np.float32)
    # SH 0th order = colour / (2 * sqrt(pi)) — 3DGS 공식
    C0 = 0.28209479177387814
    sh_dc = (col - 0.5) / C0                            # (N, 3)

    return {
        "xyz":     xyz,
        "rot":     rot,
        "scale":   scale,
        "opacity": opacity[:, None],
        "sh_dc":   sh_dc,
    }


def export_gaussian_ply(
    gaussians: dict,
    out_path:  str | Path,
) -> Path:
    """
    3DGS 공식 형식의 .ply 파일로 내보냅니다.
    gaussian-splatting 원본 뷰어 / Supersplat / Three.js splat viewer 에서 로드 가능.
    """
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    xyz     = gaussians["xyz"]
    rot     = gaussians["rot"]
    scale   = gaussians["scale"]
    opacity = gaussians["opacity"]
    sh_dc   = gaussians["sh_dc"]
    N       = len(xyz)

    # SH 고차 계수 (0으로 초기화 — 학습 전)
    SH_EXTRA = 45   # degree 3: (4²-1)*3 = 45
    sh_rest   = np.zeros((N, SH_EXTRA), dtype=np.float32)

    # plyfile dtype 정의
    dtype = [
        ("x", "f4"), ("y", "f4"), ("z", "f4"),
        ("nx", "f4"), ("ny", "f4"), ("nz", "f4"),
        ("f_dc_0", "f4"), ("f_dc_1", "f4"), ("f_dc_2", "f4"),
    ]
    for i in range(SH_EXTRA):
        dtype.append((f"f_rest_{i}", "f4"))
    dtype += [
        ("opacity", "f4"),
        ("scale_0", "f4"), ("scale_1", "f4"), ("scale_2", "f4"),
        ("rot_0", "f4"), ("rot_1", "f4"), ("rot_2", "f4"), ("rot_3", "f4"),
    ]

    arr = np.zeros(N, dtype=dtype)
    arr["x"],  arr["y"],  arr["z"]  = xyz[:,0], xyz[:,1], xyz[:,2]
    arr["nx"], arr["ny"], arr["nz"] = 0., 0., 0.
    arr["f_dc_0"] = sh_dc[:, 0]
    arr["f_dc_1"] = sh_dc[:, 1]
    arr["f_dc_2"] = sh_dc[:, 2]
    for i in range(SH_EXTRA):
        arr[f"f_rest_{i}"] = sh_rest[:, i]
    arr["opacity"] = opacity[:, 0]
    arr["scale_0"] = scale[:, 0]
    arr["scale_1"] = scale[:, 1]
    arr["scale_2"] = scale[:, 2]
    arr["rot_0"]   = rot[:, 0]
    arr["rot_1"]   = rot[:, 1]
    arr["rot_2"]   = rot[:, 2]
    arr["rot_3"]   = rot[:, 3]

    el  = PlyElement.describe(arr, "vertex")
    ply = PlyData([el], text=False)
    ply.write(str(out_path))

    print(f"[GS] 저장됨: {out_path}  ({N:,} Gaussians)")
    return out_path
