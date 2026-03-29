"""
smpl_body.py  (Windows 호환 버전)
===================================
PyTorch3D 없이 동작하는 렌더러.
렌더링 백엔드 우선순위:
  1. pyrender  (가장 좋은 품질)
  2. trimesh scene (중간 품질)
  3. PIL 실루엣 (항상 동작하는 fallback)
"""

from __future__ import annotations

import math
import io
import os
import platform
from pathlib import Path
from typing import Optional

import numpy as np
import torch
import cv2
from PIL import Image, ImageDraw
import trimesh

# Windows headless 설정
if platform.system() == "Windows":
    os.environ.setdefault("PYOPENGL_PLATFORM", "")
else:
    os.environ.setdefault("PYOPENGL_PLATFORM", "osmesa")

try:
    import smplx
    HAS_SMPLX = True
except ImportError:
    HAS_SMPLX = False
    print("[WARN] smplx 없음: pip install smplx")

try:
    import pyrender
    HAS_PYRENDER = True
except Exception:
    HAS_PYRENDER = False
    print("[WARN] pyrender 없음 — trimesh fallback 사용")

HAS_P3D = False  # PyTorch3D Windows 미지원

DEVICE    = torch.device("cuda" if torch.cuda.is_available() else "cpu")
MODEL_DIR = Path(__file__).parent.parent / "models"

print(f"[smpl_body] device={DEVICE}  smplx={HAS_SMPLX}  pyrender={HAS_PYRENDER}")

SKIN_TONES = {
    "light":  [0.91, 0.75, 0.62],
    "medium": [0.78, 0.57, 0.43],
    "tan":    [0.66, 0.45, 0.32],
    "dark":   [0.42, 0.28, 0.19],
}

CLOTH_REGIONS = {
    "upper": (1500, 4500),
    "lower": (4500, 6500),
}


# ══════════════════════════════════════════════════════════════
#  SMPL-X BODY WRAPPER
# ══════════════════════════════════════════════════════════════
class SMPLXBody:
    def __init__(
        self,
        model_path: str | Path = None,
        gender: str = "neutral",
        num_betas: int = 10,
        device: torch.device = DEVICE,
    ):
        self.device     = device
        self.num_betas  = num_betas
        self.gender     = gender
        self.model_path = Path(model_path) if model_path else MODEL_DIR / "smplx"

        if not HAS_SMPLX:
            raise RuntimeError("smplx 패키지 필요: pip install smplx")

        candidates = [
            self.model_path / f"SMPLX_{gender.upper()}.npz",
            self.model_path / "SMPLX_NEUTRAL.npz",
        ]
        found = next((p for p in candidates if p.exists()), None)
        if found is None:
            raise FileNotFoundError(
                f"\n\n★ SMPL-X 모델 파일 없음 ★\n"
                f"  경로: {self.model_path}\n"
                f"  해결: https://smpl-x.is.tue.mpg.de 에서 무료 다운로드 후\n"
                f"        {self.model_path}\\SMPLX_NEUTRAL.npz 에 배치\n"
            )

        print(f"[SMPL-X] 로드: {found}")
        self.smplx_model = smplx.create(
            str(self.model_path),
            model_type="smplx",
            gender=gender,
            num_betas=num_betas,
            use_pca=False,
            flat_hand_mean=True,
        ).to(device)

        self.default_betas         = torch.zeros(1, num_betas, device=device)
        self.default_global_orient = torch.zeros(1, 3, device=device)
        self.default_body_pose     = torch.zeros(1, 63, device=device)

    @property
    def faces(self) -> np.ndarray:
        return self.smplx_model.faces.astype(np.int64)

    def forward(
        self,
        betas:         Optional[torch.Tensor] = None,
        body_pose:     Optional[torch.Tensor] = None,
        global_orient: Optional[torch.Tensor] = None,
        transl:        Optional[torch.Tensor] = None,
    ) -> dict:
        betas         = betas         if betas         is not None else self.default_betas
        body_pose     = body_pose     if body_pose     is not None else self.default_body_pose
        global_orient = global_orient if global_orient is not None else self.default_global_orient
        transl        = transl        if transl         is not None else torch.zeros(1, 3, device=self.device)

        with torch.no_grad():
            out = self.smplx_model(
                betas=betas,
                body_pose=body_pose,
                global_orient=global_orient,
                transl=transl,
                return_verts=True,
            )
        return {
            "vertices": out.vertices[0].cpu().numpy(),
            "joints":   out.joints[0].cpu().numpy(),
            "faces":    self.faces,
        }

    def shape_from_measurements(
        self,
        height_cm:  float = 170.0,
        chest_cm:   float = 90.0,
        waist_cm:   float = 76.0,
        hip_cm:     float = 95.0,
        gender:     str   = "neutral",
    ) -> torch.Tensor:
        betas = torch.zeros(1, self.num_betas, device=self.device)
        betas[0, 0] = (height_cm - 170.0) / 18.0
        avg_girth   = (chest_cm + waist_cm + hip_cm) / 3.0
        betas[0, 1] = (avg_girth - 87.0) / 14.0
        betas[0, 2] = (chest_cm - hip_cm) / 20.0
        betas[0, 3] = (chest_cm - waist_cm) / 22.0
        return torch.clamp(betas, -2.5, 2.5)


# ══════════════════════════════════════════════════════════════
#  POSE FITTING
# ══════════════════════════════════════════════════════════════
def mediapipe_kpts_to_smplx_pose(kpts: dict, img_w: int, img_h: int) -> dict:
    def kp(name):
        k = kpts.get(name)
        if k is None:
            return None
        return np.array([
            (k["x"] / img_w) * 2 - 1,
            -((k["y"] / img_h) * 2 - 1),
            k.get("z", 0.0),
        ], dtype=np.float32)

    body_pose = np.zeros(63, dtype=np.float32)

    lsh  = kp("left_shoulder");  rsh  = kp("right_shoulder")
    lel  = kp("left_elbow");     rel  = kp("right_elbow")
    lhip = kp("left_hip");       rhip = kp("right_hip")
    lkn  = kp("left_knee");      rkn  = kp("right_knee")
    lank = kp("left_ankle");     rank = kp("right_ankle")

    if lsh is not None and lel is not None:
        d  = lel - lsh
        az = math.atan2(d[0], -d[1])
        body_pose[16*3:16*3+3] = [0, 0, az - math.pi/2]

    if rsh is not None and rel is not None:
        d  = rel - rsh
        az = math.atan2(d[0], -d[1])
        body_pose[17*3:17*3+3] = [0, 0, az + math.pi/2]

    if lsh is not None and lel is not None and kp("left_wrist") is not None:
        lwr = kp("left_wrist")
        d_u = lel - lsh; d_l = lwr - lel
        dot = np.dot(d_u[:2], d_l[:2]) / (np.linalg.norm(d_u[:2]) * np.linalg.norm(d_l[:2]) + 1e-6)
        body_pose[18*3:18*3+3] = [0, math.acos(np.clip(dot,-1,1)) * 0.6, 0]

    if rsh is not None and rel is not None and kp("right_wrist") is not None:
        rwr = kp("right_wrist")
        d_u = rel - rsh; d_l = rwr - rel
        dot = np.dot(d_u[:2], d_l[:2]) / (np.linalg.norm(d_u[:2]) * np.linalg.norm(d_l[:2]) + 1e-6)
        body_pose[19*3:19*3+3] = [0, -math.acos(np.clip(dot,-1,1)) * 0.6, 0]

    if lhip is not None and lkn is not None:
        d = lkn - lhip
        body_pose[1*3:1*3+3] = [math.atan2(-d[1], math.hypot(d[0],d[2])) * 0.5, 0, 0]

    if rhip is not None and rkn is not None:
        d = rkn - rhip
        body_pose[2*3:2*3+3] = [math.atan2(-d[1], math.hypot(d[0],d[2])) * 0.5, 0, 0]

    if lhip is not None and lkn is not None and lank is not None:
        d_u = lkn - lhip; d_l = lank - lkn
        dot = np.dot(d_u[:2], d_l[:2]) / (np.linalg.norm(d_u[:2]) * np.linalg.norm(d_l[:2]) + 1e-6)
        body_pose[4*3:4*3+3] = [-math.acos(np.clip(dot,-1,1)) * 0.5, 0, 0]

    if rhip is not None and rkn is not None and rank is not None:
        d_u = rkn - rhip; d_l = rank - rkn
        dot = np.dot(d_u[:2], d_l[:2]) / (np.linalg.norm(d_u[:2]) * np.linalg.norm(d_l[:2]) + 1e-6)
        body_pose[5*3:5*3+3] = [-math.acos(np.clip(dot,-1,1)) * 0.5, 0, 0]

    body_pose[3*3:3*3+3] = [0.04, 0, 0]
    body_pose[6*3:6*3+3] = [0.04, 0, 0]

    return {
        "body_pose":     torch.tensor(body_pose[np.newaxis], dtype=torch.float32),
        "global_orient": torch.zeros(1, 3, dtype=torch.float32),
    }


# ══════════════════════════════════════════════════════════════
#  RENDERER
# ══════════════════════════════════════════════════════════════
def _build_vertex_colors(vertices, skin_tone, cloth_color_upper=None, cloth_color_lower=None):
    V  = len(vertices)
    vc = np.tile(SKIN_TONES.get(skin_tone, SKIN_TONES["medium"]), (V, 1)).astype(np.float32)
    if cloth_color_upper is not None:
        s, e = CLOTH_REGIONS["upper"]
        vc[max(0,s):min(V,e)] = cloth_color_upper
    if cloth_color_lower is not None:
        s, e = CLOTH_REGIONS["lower"]
        vc[max(0,s):min(V,e)] = cloth_color_lower
    return vc


def _look_at(eye, target, up=np.array([0.,1.,0.])):
    z = eye - target
    z = z / (np.linalg.norm(z) + 1e-8)
    x = np.cross(up, z)
    x = x / (np.linalg.norm(x) + 1e-8)
    y = np.cross(z, x)
    m = np.eye(4)
    m[:3,0]=x; m[:3,1]=y; m[:3,2]=z; m[:3,3]=eye
    return m


def _cam_pos(azimuth, elevation, dist):
    az = math.radians(azimuth)
    el = math.radians(elevation)
    cx = dist * math.cos(el) * math.sin(az)
    cy = dist * math.sin(el) + 0.9
    cz = dist * math.cos(el) * math.cos(az)
    return np.array([cx, cy, cz])


def _render_pyrender(vertices, faces, vc, img_size, elevation, azimuth, dist, bg_color):
    tm = trimesh.Trimesh(
        vertices=vertices, faces=faces,
        vertex_colors=(vc * 255).astype(np.uint8),
        process=False,
    )
    mesh  = pyrender.Mesh.from_trimesh(tm, smooth=True)
    scene = pyrender.Scene(
        bg_color=[c/255.0 for c in bg_color[:3]] + [1.0],
        ambient_light=[0.45, 0.45, 0.45],
    )
    scene.add(mesh)

    eye      = _cam_pos(azimuth, elevation, dist)
    cam_pose = _look_at(eye, np.array([0.0, 0.9, 0.0]))
    camera   = pyrender.PerspectiveCamera(yfov=math.radians(40), aspectRatio=1.0)
    scene.add(camera, pose=cam_pose)

    for pos, color, intensity in [
        ([2,4,3],   [1.0,0.97,0.90], 3.5),
        ([-3,2,-2], [0.8,0.85,1.0],  1.5),
        ([0,-2,-4], [1.0,1.0,1.0],   1.0),
    ]:
        light = pyrender.DirectionalLight(color=color, intensity=intensity)
        scene.add(light, pose=_look_at(np.array(pos, dtype=float), np.zeros(3)))

    r = pyrender.OffscreenRenderer(img_size, img_size)
    try:
        color, _ = r.render(scene)
    finally:
        r.delete()
    return color


def _render_trimesh_pil(vertices, faces, vc, img_size, azimuth, elevation, dist, bg_color):
    tm = trimesh.Trimesh(
        vertices=vertices.copy(), faces=faces,
        vertex_colors=(vc * 255).astype(np.uint8),
        process=False,
    )
    # 회전 적용
    R_az = trimesh.transformations.rotation_matrix(math.radians(azimuth),  [0,1,0])
    R_el = trimesh.transformations.rotation_matrix(math.radians(elevation), [1,0,0])
    tm.apply_transform(R_az)
    tm.apply_transform(R_el)

    scene = tm.scene()
    scene.camera.fov = [40, 40]
    try:
        png = scene.save_image(resolution=[img_size, img_size], visible=False)
        img = Image.open(io.BytesIO(png)).convert("RGB")
        return np.array(img)
    except Exception as e:
        print(f"[WARN] trimesh scene render 실패 ({e}), PIL fallback")
        return _render_silhouette(vertices, faces, vc, img_size, azimuth, bg_color)


def _render_silhouette(vertices, faces, vc, img_size, azimuth, bg_color):
    """항상 동작하는 최후 fallback."""
    img  = Image.new("RGB", (img_size, img_size), tuple(int(c) for c in bg_color[:3]))
    draw = ImageDraw.Draw(img)

    az      = math.radians(azimuth)
    cos_az  = math.cos(az)
    sin_az  = math.sin(az)
    x_r     =  vertices[:,0] * cos_az + vertices[:,2] * sin_az
    y_r     =  vertices[:,1]

    x_min, x_max = x_r.min(), x_r.max()
    y_min, y_max = y_r.min(), y_r.max()
    rng  = max(x_max-x_min, y_max-y_min, 1e-6)
    pad  = img_size * 0.1
    scale = (img_size - 2*pad) / rng

    def proj(xi, yi):
        return (int((xi-x_min)*scale+pad), int((y_max-yi)*scale+pad))

    mean_col = tuple((vc.mean(axis=0)*255).astype(int))
    for face in faces[::6]:
        pts = [proj(x_r[i], y_r[i]) for i in face]
        draw.polygon(pts, fill=mean_col)
    return np.array(img)


def render_smplx_mesh(
    vertices:          np.ndarray,
    faces:             np.ndarray,
    skin_tone:         str   = "medium",
    cloth_color_upper: list  = None,
    cloth_color_lower: list  = None,
    img_size:          int   = 512,
    elevation:         float = 0.0,
    azimuth:           float = 0.0,
    dist:              float = 2.8,
    bg_color:          list  = None,
) -> np.ndarray:
    bg = bg_color if bg_color is not None else [18, 18, 30]
    vc = _build_vertex_colors(vertices, skin_tone, cloth_color_upper, cloth_color_lower)

    if HAS_PYRENDER:
        try:
            return _render_pyrender(vertices, faces, vc, img_size, elevation, azimuth, dist, bg)
        except Exception as e:
            print(f"[WARN] pyrender 실패 ({e}), trimesh fallback")

    return _render_trimesh_pil(vertices, faces, vc, img_size, azimuth, elevation, dist, bg)


# ══════════════════════════════════════════════════════════════
#  GLB EXPORT
# ══════════════════════════════════════════════════════════════
def export_obj(
    vertices:          np.ndarray,
    faces:             np.ndarray,
    out_path:          str | Path,
    skin_tone:         str  = "medium",
    cloth_color_upper: list = None,
    cloth_color_lower: list = None,
) -> Path:
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    vc      = _build_vertex_colors(vertices, skin_tone, cloth_color_upper, cloth_color_lower)
    vc_255  = np.clip(vc * 255, 0, 255).astype(np.uint8)
    vc_rgba = np.hstack([vc_255, np.full((len(vertices),1), 255, dtype=np.uint8)])

    tm = trimesh.Trimesh(vertices=vertices, faces=faces, process=False)
    tm.visual = trimesh.visual.ColorVisuals(vertex_colors=vc_rgba)

    glb_path = out_path.with_suffix(".glb")
    tm.export(str(glb_path), file_type="glb")
    print(f"[export] GLB: {glb_path}  ({len(vertices):,} verts, {len(faces):,} faces)")
    return glb_path
