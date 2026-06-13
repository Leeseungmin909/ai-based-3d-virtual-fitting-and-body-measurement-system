import os
import uvicorn
from typing import Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import FileResponse
import shutil, uuid, asyncio
from core.job_store import JobStore
from core.pipeline import run_pipeline

app = FastAPI(title="Avatar Photo System")

# 모바일 앱(model-viewer WebView 등)이 GLB/이미지를 교차 출처로 가져올 수 있도록 허용
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static",  StaticFiles(directory="static"),  name="static")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
app.mount("/outputs", StaticFiles(directory="outputs"), name="outputs")
app.mount("/clothes", StaticFiles(directory="clothes"), name="clothes")

templates = Jinja2Templates(directory="templates")
job_store = JobStore()

@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse(request, "index.html")

@app.get("/viewer/{job_id}")
async def viewer(request: Request, job_id: str):
    job = job_store.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Not found")
    return templates.TemplateResponse(request, "viewer.html", {"job_id": job_id})

@app.post("/api/upload-photo")
async def upload_photo(
    file:        UploadFile = File(...),
    gender:      str        = Form("neutral"),
    height_cm:   Optional[float] = Form(None),        # 사용자 실제 키 → 실측 cm 환산
    weight_kg:   Optional[float] = Form(None),        # 사용자 체중 → 체형(betas) 반영
    face_photo:  Optional[UploadFile] = File(None),
    shirt_glb:   Optional[UploadFile] = File(None),   # 상의 GLB 파일
    pants_glb:   Optional[UploadFile] = File(None),   # 하의 GLB 파일
):
    if not file.filename.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
        raise HTTPException(status_code=400, detail="JPG, PNG, WEBP만 지원합니다")

    job_id     = str(uuid.uuid4())[:8]
    photo_path = f"uploads/{job_id}_{file.filename}"
    with open(photo_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    def _save_opt(upload, tag):
        if upload and upload.filename:
            path = f"uploads/{job_id}_{tag}_{upload.filename}"
            with open(path, "wb") as f:
                shutil.copyfileobj(upload.file, f)
            return path
        return None

    face_photo_path = _save_opt(face_photo, "face")
    shirt_glb_path  = _save_opt(shirt_glb,  "shirt")
    pants_glb_path  = _save_opt(pants_glb,  "pants_glb")

    shirt_glb_url = f"/{shirt_glb_path}" if shirt_glb_path else None
    pants_glb_url = f"/{pants_glb_path}" if pants_glb_path else None

    job_store.set(job_id, {
        "status":          "uploaded",
        "progress":        0,
        "step":            "사진 업로드 완료",
        "photo_path":      photo_path,
        "face_photo_path": face_photo_path,
        "shirt_glb_url":   shirt_glb_url,
        "pants_glb_url":   pants_glb_url,
        "gender":          gender,
        "height_cm":       height_cm,
        "weight_kg":       weight_kg,
        "avatar_glb":      None,
        "cloth_url":       None,
        "error":           None,
    })

    asyncio.create_task(run_pipeline(job_id, job_store))
    return {"job_id": job_id}

@app.get("/api/measurements/{job_id}")
async def get_measurements(job_id: str):
    """Java 서버 연동용: user_measurements 스키마(cm) + 결과 아티팩트 URL 반환."""
    job = job_store.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Not found")
    return {
        "job_id":           job_id,
        "status":           job.get("status"),
        "measurements_cm":  job.get("measurements_cm"),   # user_measurements 매핑
        "smpl_mesh_url":    f"/outputs/debug/{job_id}/smplx.ply",
        "avatar_glb_url":   job.get("avatar_glb"),
        "shirt_glb_url":    job.get("shirt_glb_url"),
        "pants_glb_url":    job.get("pants_glb_url"),
        "result_json_url":  job.get("result_json_url"),
        "result_splat_url": job.get("result_splat_url"),
    }

@app.get("/api/job/{job_id}")
async def get_job(job_id: str):
    job = job_store.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Not found")
    return job

@app.post("/api/upload-cloth/{job_id}")
async def upload_cloth(job_id: str, file: UploadFile = File(...)):
    job = job_store.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Not found")
    if not file.filename.lower().endswith((".glb", ".gltf")):
        raise HTTPException(status_code=400, detail="GLB, GLTF만 지원합니다")

    path = f"uploads/{job_id}_cloth_{file.filename}"
    with open(path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    job["cloth_url"]      = f"/{path}"
    job["cloth_filename"] = file.filename
    job_store.set(job_id, job)
    return {"cloth_url": f"/{path}"}

@app.get("/api/renders/{job_id}")
async def get_renders(job_id: str):
    job = job_store.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Not found")
    return {"renders": job.get("render_paths", []), "avatar_glb": job.get("avatar_glb")}

@app.get("/api/avatar-glb/{job_id}")
async def get_avatar_glb(job_id: str):
    job = job_store.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Not found")
    glb_path = (job.get("avatar_glb") or "").lstrip("/")
    if not glb_path or not os.path.exists(glb_path):
        raise HTTPException(status_code=404, detail="GLB not ready")
    return FileResponse(glb_path, media_type="model/gltf-binary",
                        filename=f"{job_id}_avatar.glb")

@app.get("/api/clothes")
async def list_clothes():
    """clothes/ 디렉토리에 있는 GLB 파일 목록 반환"""
    tops    = sorted(f for f in os.listdir("clothes/상의") if f.lower().endswith('.glb'))
    bottoms = sorted(f for f in os.listdir("clothes/하의") if f.lower().endswith('.glb'))
    return {"tops": tops, "bottoms": bottoms}


@app.post("/api/fit")
async def fit_from_library(
    file:   UploadFile      = File(...),
    gender: str             = Form("neutral"),
    shirt:  Optional[str]   = Form(None),   # clothes/상의/ 파일명
    pants:  Optional[str]   = Form(None),   # clothes/하의/ 파일명
):
    """clothes 라이브러리 파일 + 사진으로 피팅 잡 생성"""
    if not file.filename.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
        raise HTTPException(status_code=400, detail="이미지 파일만 지원합니다")

    job_id     = str(uuid.uuid4())[:8]
    photo_path = f"uploads/{job_id}_{file.filename}"
    with open(photo_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    def _lib(folder, name):
        if not name:
            return None
        p = f"clothes/{folder}/{name}"
        return p if os.path.exists(p) else None

    shirt_path = _lib("상의", shirt)
    pants_path = _lib("하의", pants)

    job_store.set(job_id, {
        "status":          "uploaded",
        "progress":        0,
        "step":            "사진 업로드 완료",
        "photo_path":      photo_path,
        "face_photo_path": None,
        "shirt_glb_url":   f"/{shirt_path}" if shirt_path else None,
        "pants_glb_url":   f"/{pants_path}" if pants_path else None,
        "gender":          gender,
        "avatar_glb":      None,
        "cloth_url":       None,
        "error":           None,
    })

    asyncio.create_task(run_pipeline(job_id, job_store))
    return {"job_id": job_id}


if __name__ == "__main__":
    # reload=True는 리로더+서버 2중 프로세스를 만들어 재시작 시 좀비가 남음 → 비활성
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
