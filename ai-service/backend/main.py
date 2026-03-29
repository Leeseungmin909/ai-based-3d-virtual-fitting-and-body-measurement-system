"""
main.py  —  Avatar Try-On  FastAPI Server
==========================================

Endpoints
---------
POST /api/analyze       사진 → 배경제거 → 포즈 → 체형 측정
POST /api/build_avatar  체형 측정값 + 포즈 → SMPL-X 메시 → render PNG + export GLB
POST /api/tryon         GLB + 의상 선택 → 의상 드레이핑 → 새 GLB + render PNG
POST /api/gaussian      GLB → 3DGS 초기화 → .ply 내보내기
GET  /api/file/{name}   생성된 파일 다운로드 (GLB, PLY, PNG)
WS   /ws/progress       처리 진행상황 스트림
"""

from __future__ import annotations

import asyncio
import base64
import io
import json
import os
import sys
import time
import uuid
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
import torch
from fastapi import FastAPI, File, Form, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from PIL import Image, ImageOps
import uvicorn

# ── 로컬 모듈 ─────────────────────────────────────────────────
sys.path.insert(0, str(Path(__file__).parent))
from smpl_body   import SMPLXBody, HMR2Estimator, mediapipe_kpts_to_smplx_pose, render_smplx_mesh, export_obj
from cloth_drape import drape_cloth, apply_vertex_texture_to_export
from gaussian_avatar import mesh_to_gaussian_init, export_gaussian_ply

# ── Pose detection (MediaPipe) ────────────────────────────────
import mediapipe as mp
_mp_pose   = mp.solutions.pose
_mp_draw   = mp.solutions.drawing_utils
_pose_model = _mp_pose.Pose(
    static_image_mode=True, model_complexity=2,
    enable_segmentation=True, min_detection_confidence=0.45,
)
KPTS = [
    "nose","left_eye_inner","left_eye","left_eye_outer",
    "right_eye_inner","right_eye","right_eye_outer",
    "left_ear","right_ear","mouth_left","mouth_right",
    "left_shoulder","right_shoulder","left_elbow","right_elbow",
    "left_wrist","right_wrist","left_pinky","right_pinky",
    "left_index","right_index","left_thumb","right_thumb",
    "left_hip","right_hip","left_knee","right_knee",
    "left_ankle","right_ankle","left_heel","right_heel",
    "left_foot_index","right_foot_index",
]

# ── Background removal ────────────────────────────────────────
try:
    from rembg import remove as rembg_remove
    HAS_REMBG = True
except ImportError:
    HAS_REMBG = False

# ── GPU ───────────────────────────────────────────────────────
DEVICE   = torch.device("cuda" if torch.cuda.is_available() else "cpu")
MODEL_DIR = Path(__file__).parent.parent / "models"
OUTPUT_DIR = Path(__file__).parent.parent / "outputs"
OUTPUT_DIR.mkdir(exist_ok=True)

# ── App ───────────────────────────────────────────────────────
app = FastAPI(title="SMPL Avatar API", version="1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

FRONTEND = Path(__file__).parent.parent / "frontend"
if FRONTEND.exists():
    app.mount("/app", StaticFiles(directory=str(FRONTEND), html=True), name="static")

# ── WebSocket manager ─────────────────────────────────────────
class WSManager:
    def __init__(self):
        self._sockets: dict[str, WebSocket] = {}

    async def connect(self, sid: str, ws: WebSocket):
        await ws.accept()
        self._sockets[sid] = ws

    def disconnect(self, sid: str):
        self._sockets.pop(sid, None)

    async def send(self, sid: str, msg: dict):
        ws = self._sockets.get(sid)
        if ws:
            try:
                await ws.send_json(msg)
            except Exception:
                self.disconnect(sid)

ws_manager = WSManager()

# ── Lazy-loaded models ────────────────────────────────────────
_smplx_body: Optional[SMPLXBody] = None
_hmr2_est:   Optional[HMR2Estimator] = None

def get_smplx() -> SMPLXBody:
    global _smplx_body
    if _smplx_body is None:
        _smplx_body = SMPLXBody(model_path=MODEL_DIR / "smplx", device=DEVICE)
    return _smplx_body

def get_hmr2() -> HMR2Estimator:
    global _hmr2_est
    if _hmr2_est is None:
        _hmr2_est = HMR2Estimator(ckpt_path=MODEL_DIR / "hmr2" / "hmr2_checkpoint.ckpt")
    return _hmr2_est


# ══════════════════════════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════════════════════════

def _pil_to_b64(img: Image.Image, fmt="PNG") -> str:
    buf = io.BytesIO()
    img.save(buf, format=fmt)
    return base64.b64encode(buf.getvalue()).decode()

def _b64_to_pil(data: str) -> Image.Image:
    raw = base64.b64decode(data.split(",")[-1])
    return Image.open(io.BytesIO(raw))

def _save_output(name: str, data: bytes) -> Path:
    p = OUTPUT_DIR / name
    p.write_bytes(data)
    return p

def _remove_bg(pil: Image.Image) -> Image.Image:
    if HAS_REMBG:
        buf = io.BytesIO()
        pil.save(buf, "PNG")
        return Image.open(io.BytesIO(rembg_remove(buf.getvalue()))).convert("RGBA")
    # GrabCut fallback
    bgr  = cv2.cvtColor(np.array(pil.convert("RGB")), cv2.COLOR_RGB2BGR)
    h, w = bgr.shape[:2]
    mask = np.zeros((h, w), np.uint8)
    bgd  = np.zeros((1, 65), np.float64)
    fgd  = np.zeros((1, 65), np.float64)
    m    = max(10, int(min(h, w) * 0.04))
    cv2.grabCut(bgr, mask, (m, m, w-2*m, h-2*m), bgd, fgd, 10, cv2.GC_INIT_WITH_RECT)
    m2   = np.where((mask==2)|(mask==0), 0, 255).astype(np.uint8)
    k    = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9,9))
    m2   = cv2.morphologyEx(m2, cv2.MORPH_CLOSE, k, iterations=3)
    m2   = cv2.GaussianBlur(m2, (7,7), 0)
    rgba = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGBA)
    rgba[:,:,3] = m2
    return Image.fromarray(rgba, "RGBA")

def _estimate_pose(rgba: Image.Image):
    rgb     = np.array(rgba.convert("RGB"))
    results = _pose_model.process(rgb)
    if not results.pose_landmarks:
        return None, None
    h, w = rgb.shape[:2]
    lm   = results.pose_landmarks.landmark
    kpts = {name: {"x": lm[i].x*w, "y": lm[i].y*h, "z": lm[i].z, "vis": lm[i].visibility}
            for i, name in enumerate(KPTS)}
    seg = None
    if results.segmentation_mask is not None:
        seg = (results.segmentation_mask > 0.5).astype(np.uint8) * 255
    return kpts, seg

def _measure_body(kpts: dict, H: int, W: int) -> dict:
    import math
    def d(a, b): return math.hypot(kpts[a]["x"]-kpts[b]["x"], kpts[a]["y"]-kpts[b]["y"])
    foot_y = max(kpts["left_ankle"]["y"], kpts["right_ankle"]["y"])
    px_h   = max(foot_y - kpts["nose"]["y"], H*0.5)
    scale  = 170.0 / px_h
    sh_px  = d("left_shoulder", "right_shoulder")
    hip_px = d("left_hip",      "right_hip")
    return {
        "height_cm":   round(px_h  * scale),
        "shoulder_cm": round(sh_px * scale * 2.6),
        "chest_cm":    round(sh_px * scale * 2.9),
        "waist_cm":    round(hip_px* scale * 2.3),
        "hip_cm":      round(hip_px* scale * 2.9),
    }

def _np_img_to_b64(arr: np.ndarray, fmt="PNG") -> str:
    img = Image.fromarray(arr)
    return _pil_to_b64(img, fmt)


# ══════════════════════════════════════════════════════════════
#  ROUTES
# ══════════════════════════════════════════════════════════════

@app.get("/")
def root():
    return {"status": "ok", "device": str(DEVICE),
            "smplx_ready": (MODEL_DIR/"smplx"/"SMPLX_NEUTRAL.npz").exists(),
            "hmr2_ready":  (MODEL_DIR/"hmr2"/"hmr2_checkpoint.ckpt").exists()}

@app.get("/health")
def health():
    return {
        "rembg":    HAS_REMBG,
        "cuda":     torch.cuda.is_available(),
        "device":   str(DEVICE),
        "smplx":    (MODEL_DIR/"smplx"/"SMPLX_NEUTRAL.npz").exists(),
        "hmr2":     (MODEL_DIR/"hmr2"/"hmr2_checkpoint.ckpt").exists(),
    }


# ── STEP 1 : ANALYZE ──────────────────────────────────────────
@app.post("/api/analyze")
async def analyze(file: UploadFile = File(...)):
    """사진 → 배경 제거 → 포즈 감지 → 체형 측정."""
    t0  = time.time()
    raw = await file.read()
    pil = ImageOps.exif_transpose(Image.open(io.BytesIO(raw)))
    MAX_H = 1024
    if pil.height > MAX_H:
        pil = pil.resize((int(pil.width * MAX_H / pil.height), MAX_H), Image.LANCZOS)

    # 1. 배경 제거
    bg = _remove_bg(pil.convert("RGBA"))

    # 2. 포즈
    kpts, seg = _estimate_pose(bg)
    if kpts is None:
        return JSONResponse({"ok": False, "error": "포즈 감지 실패. 전신이 나오는 사진을 사용해주세요."}, 422)

    # 3. 체형 측정
    meas = _measure_body(kpts, bg.height, bg.width)

    # 4. 포즈 디버그 이미지
    debug_rgb = np.array(bg.convert("RGB"))
    _mp_draw.draw_landmarks(
        debug_rgb, _est_pose_raw(bg),
        _mp_pose.POSE_CONNECTIONS,
        _mp_draw.DrawingSpec(color=(124,111,255), thickness=2, circle_radius=5),
        _mp_draw.DrawingSpec(color=(56,189,248),  thickness=2),
    )

    return JSONResponse({
        "ok":          True,
        "bg_b64":      _pil_to_b64(bg),
        "debug_b64":   _np_img_to_b64(debug_rgb),
        "keypoints":   kpts,
        "measurements": meas,
        "img_w": bg.width, "img_h": bg.height,
        "elapsed_s": round(time.time()-t0, 2),
    })

def _est_pose_raw(img):
    """pose_landmarks only (for draw_landmarks)."""
    rgb = np.array(img.convert("RGB"))
    r   = _pose_model.process(rgb)
    return r.pose_landmarks


# ── STEP 2 : BUILD AVATAR ─────────────────────────────────────
@app.post("/api/build_avatar")
async def build_avatar(
    measurements_json: str = Form(...),
    kpts_json:         str = Form(...),
    img_w:             int = Form(512),
    img_h:             int = Form(512),
    gender:            str = Form("neutral"),
    skin_tone:         str = Form("medium"),
    session_id:        str = Form(""),
    use_hmr2:          bool = Form(False),
    bg_b64:            str = Form(""),
):
    """
    체형 측정값 + 포즈 keypoints → SMPL-X 메시 생성 → GLB + 4-view PNG.
    """
    t0   = time.time()
    meas = json.loads(measurements_json)
    kpts = json.loads(kpts_json)
    sid  = session_id or str(uuid.uuid4())[:8]

    async def progress(step: str, pct: int):
        await ws_manager.send(sid, {"step": step, "pct": pct})

    await progress("SMPL-X 모델 로드 중...", 5)

    # ── SMPL-X 로드 ──────────────────────────────────────────
    try:
        body = get_smplx()
    except FileNotFoundError as e:
        return JSONResponse({"ok": False, "error": str(e)}, 422)

    await progress("체형 파라미터 계산 중...", 15)

    # ── Shape parameters from measurements ───────────────────
    betas = body.shape_from_measurements(
        height_cm = meas.get("height_cm",  170),
        chest_cm  = meas.get("chest_cm",    90),
        waist_cm  = meas.get("waist_cm",    76),
        hip_cm    = meas.get("hip_cm",      95),
        gender    = gender,
    )

    await progress("포즈 파라미터 추정 중...", 30)

    # ── Pose parameters ───────────────────────────────────────
    if use_hmr2 and bg_b64:
        try:
            estimator = get_hmr2()
            pil_img   = _b64_to_pil(bg_b64)
            img_rgb   = np.array(pil_img.convert("RGB"))
            pose_params = estimator.estimate(img_rgb)
        except Exception as e:
            print(f"[WARN] HMR2 실패 ({e}), MediaPipe fallback 사용")
            pose_params = mediapipe_kpts_to_smplx_pose(kpts, img_w, img_h)
    else:
        pose_params = mediapipe_kpts_to_smplx_pose(kpts, img_w, img_h)

    pose_params = {k: v.to(DEVICE) for k, v in pose_params.items()}

    await progress("SMPL-X 메시 생성 중...", 45)

    # ── Generate mesh ─────────────────────────────────────────
    result = body.forward(
        betas         = betas,
        body_pose     = pose_params["body_pose"],
        global_orient = pose_params["global_orient"],
    )
    verts = result["vertices"]
    faces = result["faces"]

    await progress("메시 렌더링 중 (4-view)...", 60)

    # ── Export GLB ────────────────────────────────────────────
    from cloth_drape import drape_cloth, apply_vertex_texture_to_export, hex_to_rgb01
    skin_colors = {
        "light":  [0.91,0.75,0.62], "medium": [0.78,0.57,0.43],
        "tan":    [0.66,0.45,0.32], "dark":   [0.42,0.28,0.19],
    }
    skin_rgb = np.array(skin_colors.get(skin_tone, skin_colors["medium"]), dtype=np.float32)
    vc       = np.tile(skin_rgb, (len(verts), 1)).astype(np.float32)
    glb_path = apply_vertex_texture_to_export(verts, faces, vc, OUTPUT_DIR / f"{sid}_avatar.glb")

    await progress("멀티뷰 렌더링 중...", 72)

    # ── Multi-view renders ────────────────────────────────────
    views = {}
    view_configs = [
        ("front",  0,  0),
        ("side",   0, 90),
        ("back",   0, 180),
        ("three_quarter", 10, 45),
    ]
    for name, elev, azim in view_configs:
        try:
            img_np = render_smplx_mesh(
                verts, faces,
                skin_tone   = skin_tone,
                img_size    = 512,
                elevation   = elev,
                azimuth     = azim,
                dist        = 2.8,
                bg_color    = [18, 18, 30],
            )
            views[name] = _np_img_to_b64(img_np)
        except Exception as e:
            print(f"[WARN] render {name} 실패: {e}")

    await progress("완료", 100)

    return JSONResponse({
        "ok":          True,
        "session_id":  sid,
        "glb_url":     f"/api/file/{sid}_avatar.glb",
        "views":       views,
        "measurements": meas,
        "elapsed_s":   round(time.time()-t0, 2),
    })


# ── STEP 3 : TRY-ON ───────────────────────────────────────────
@app.post("/api/tryon")
async def tryon(
    session_id:  str   = Form(...),
    cloth_style: str   = Form("tshirt"),
    cloth_color: str   = Form("#6c63ff"),
    skin_tone:   str   = Form("medium"),
    tightness:   float = Form(0.5),
    length_adj:  int   = Form(0),
    measurements_json: str = Form("{}"),
    kpts_json:         str = Form("{}"),
):
    """의상 드레이핑 → 새 GLB + 4-view PNG."""
    t0   = time.time()
    sid  = session_id
    meas = json.loads(measurements_json)
    kpts = json.loads(kpts_json)

    # ── Re-generate body mesh (캐싱 생략) ────────────────────
    try:
        body  = get_smplx()
    except FileNotFoundError as e:
        return JSONResponse({"ok": False, "error": str(e)}, 422)

    betas = body.shape_from_measurements(
        height_cm = meas.get("height_cm", 170),
        chest_cm  = meas.get("chest_cm",   90),
        waist_cm  = meas.get("waist_cm",   76),
        hip_cm    = meas.get("hip_cm",     95),
    )

    img_w = meas.get("img_w", 512)
    img_h = meas.get("img_h", 512)
    pose_params = mediapipe_kpts_to_smplx_pose(kpts, img_w, img_h)
    pose_params = {k: v.to(DEVICE) for k, v in pose_params.items()}

    result = body.forward(betas=betas, body_pose=pose_params["body_pose"],
                           global_orient=pose_params["global_orient"])
    verts  = result["vertices"]
    faces  = result["faces"]

    # ── Cloth draping ─────────────────────────────────────────
    draped    = drape_cloth(verts, faces, cloth_style, cloth_color, skin_tone, tightness, length_adj)
    new_verts = draped["vertices"]
    vc        = draped["vertex_colors"]

    glb_path  = apply_vertex_texture_to_export(new_verts, faces, vc, OUTPUT_DIR / f"{sid}_tryon.glb")

    # ── Multi-view renders with cloth colours ─────────────────
    from cloth_drape import hex_to_rgb01
    cloth_rgb = hex_to_rgb01(cloth_color)
    views     = {}
    view_configs = [("front",0,0), ("side",0,90), ("back",0,180), ("three_quarter",10,45)]
    for name, elev, azim in view_configs:
        try:
            img_np = render_smplx_mesh(
                new_verts, faces,
                skin_tone          = skin_tone,
                cloth_color_upper  = cloth_rgb,
                cloth_color_lower  = cloth_rgb if cloth_style in ("dress","coat","pants") else None,
                img_size           = 512,
                elevation          = elev,
                azimuth            = azim,
                dist               = 2.8,
                bg_color           = [18, 18, 30],
            )
            views[name] = _np_img_to_b64(img_np)
        except Exception as e:
            print(f"[WARN] render {name}: {e}")

    return JSONResponse({
        "ok":       True,
        "glb_url":  f"/api/file/{sid}_tryon.glb",
        "views":    views,
        "elapsed_s":round(time.time()-t0, 2),
    })


# ── STEP 4 : GAUSSIAN ─────────────────────────────────────────
@app.post("/api/gaussian")
async def gaussian(
    session_id:  str = Form(...),
    n_gaussians: int = Form(50000),
    measurements_json: str = Form("{}"),
    kpts_json:         str = Form("{}"),
    cloth_style: str = Form("tshirt"),
    cloth_color: str = Form("#6c63ff"),
    skin_tone:   str = Form("medium"),
):
    """SMPL-X 메시 → 3DGS 초기화 .ply."""
    t0   = time.time()
    sid  = session_id
    meas = json.loads(measurements_json)
    kpts = json.loads(kpts_json)

    body  = get_smplx()
    betas = body.shape_from_measurements(
        height_cm = meas.get("height_cm", 170),
        chest_cm  = meas.get("chest_cm",   90),
        waist_cm  = meas.get("waist_cm",   76),
        hip_cm    = meas.get("hip_cm",     95),
    )
    pose_params = mediapipe_kpts_to_smplx_pose(kpts, meas.get("img_w",512), meas.get("img_h",512))
    pose_params = {k: v.to(DEVICE) for k, v in pose_params.items()}
    result = body.forward(betas=betas, body_pose=pose_params["body_pose"],
                           global_orient=pose_params["global_orient"])

    from cloth_drape import drape_cloth
    draped = drape_cloth(result["vertices"], result["faces"], cloth_style, cloth_color, skin_tone)

    gaussians = mesh_to_gaussian_init(
        draped["vertices"], result["faces"], draped["vertex_colors"],
        n_gaussians=n_gaussians,
    )
    ply_path = export_gaussian_ply(gaussians, OUTPUT_DIR / f"{sid}_avatar.ply")

    return JSONResponse({
        "ok":         True,
        "ply_url":    f"/api/file/{sid}_avatar.ply",
        "n_gaussians": n_gaussians,
        "elapsed_s":  round(time.time()-t0, 2),
    })


# ── FILE DOWNLOAD ─────────────────────────────────────────────
@app.get("/api/file/{filename}")
def get_file(filename: str):
    path = OUTPUT_DIR / filename
    if not path.exists():
        return JSONResponse({"error": "파일 없음"}, 404)
    media = {
        ".glb": "model/gltf-binary",
        ".ply": "application/octet-stream",
        ".png": "image/png",
        ".obj": "text/plain",
    }.get(path.suffix, "application/octet-stream")
    return FileResponse(str(path), media_type=media, filename=filename)


# ── WEBSOCKET ─────────────────────────────────────────────────
@app.websocket("/ws/{session_id}")
async def websocket_endpoint(ws: WebSocket, session_id: str):
    await ws_manager.connect(session_id, ws)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(session_id)


# ── RUN ───────────────────────────────────────────────────────
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False, log_level="info")
