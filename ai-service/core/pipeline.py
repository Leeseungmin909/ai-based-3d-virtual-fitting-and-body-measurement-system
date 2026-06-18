import asyncio, traceback, os, json
from core.job_store import JobStore
from core.step1_analyze import analyze_photo
from core.step2_smplx import fit_smplx
from core.step3_texture import extract_vertex_colors, extract_clothing_color, compute_body_measurements
from core.step4_export import export_glb
from core.step5_render import render_avatar_views
from core.step_blender_cloth import fit_cloth_blender
from core.measure_body import measure_body_cm
from core.merge_glb import merge_glbs, clip_top_under_bottom

async def run_pipeline(job_id: str, job_store: JobStore):
    loop = asyncio.get_event_loop()
    try:
        job = job_store.get(job_id)
        photo_path      = job["photo_path"]
        face_photo_path = job.get("face_photo_path")
        gender          = job.get("gender", "neutral")

        # GLB 의상 여부와 관계없이 상하의 모두 피부색 유지
        shirt_color = None
        pants_color = None

        # STEP 1: 사진 분석 (MediaPipe Body + FaceMesh)
        job_store.update(job_id, status="running", step="사진 분석 중...", progress=15)
        analysis = await loop.run_in_executor(None, analyze_photo, photo_path, job_id, face_photo_path)

        # STEP 2: SMPL-X 피팅 (사진 + 키·체중으로 체형 betas 결정)
        job_store.update(job_id, step="3D 체형 생성 중...", progress=40)
        smplx_data = await loop.run_in_executor(
            None, fit_smplx, analysis, gender, job_id,
            job.get("height_cm"), job.get("weight_kg"))

        # STEP 2.5: 신체 치수 계산 → 뷰어 클라이언트 피팅에 사용
        measurements = compute_body_measurements(smplx_data)
        job_store.update(job_id, measurements=measurements)
        # (서버 측 GLB 수정 없음: 원본 GLB를 그대로 서빙, 피팅은 Three.js에서 수행)

        # STEP 2.6: 실측 cm 신체 치수 (Java ERD user_measurements 스키마)
        measurements_cm = measure_body_cm(smplx_data, job.get("height_cm"))
        job_store.update(job_id, measurements_cm=measurements_cm)
        print(f"[Pipeline] 실측 cm 치수: {measurements_cm}")

        # STEP 3: 버텍스 컬러 생성 (의상 색 + 얼굴 사진 투영)
        job_store.update(job_id, step="의상 및 얼굴 색상 적용 중...", progress=60)
        vertex_colors = await loop.run_in_executor(
            None, extract_vertex_colors,
            photo_path, analysis, smplx_data, shirt_color, pants_color)

        # STEP 4: GLB 생성 (버텍스 컬러 머티리얼)
        job_store.update(job_id, step="GLB 생성 중...", progress=70)
        glb_path = await loop.run_in_executor(None, export_glb, smplx_data, vertex_colors, job_id)

        # STEP 4.5: Blender 클로스 시뮬레이션 (GLB 의상만 처리, 이미지는 뷰어에서 처리)
        _IMG_EXT = (".jpg", ".jpeg", ".png", ".webp")
        _DEFAULT_SHIRT = "clothes/top/top_002/model.glb"        # 남성 반팔 폴로
        _DEFAULT_PANTS = "clothes/bottom/bottom_002/model.glb"  # 데님 반바지
        shirt_raw = (job.get("shirt_glb_url") or "").lstrip("/")
        pants_raw = (job.get("pants_glb_url") or "").lstrip("/")

        # 의상 미선택 시 기본 반팔·반바지로 대체 (맨몸/노출 방지)
        if not shirt_raw and os.path.exists(_DEFAULT_SHIRT):
            shirt_raw = _DEFAULT_SHIRT
        if not pants_raw and os.path.exists(_DEFAULT_PANTS):
            pants_raw = _DEFAULT_PANTS

        if shirt_raw and os.path.exists(shirt_raw) and not shirt_raw.lower().endswith(_IMG_EXT):
            job_store.update(job_id, step="상의 Blender 피팅 중...", progress=78)
            fitted_shirt = await loop.run_in_executor(
                None, fit_cloth_blender, shirt_raw, glb_path, 'shirt', job_id, measurements)
            job_store.update(job_id, shirt_glb_url=f"/{fitted_shirt}")

        if pants_raw and os.path.exists(pants_raw) and not pants_raw.lower().endswith(_IMG_EXT):
            job_store.update(job_id, step="하의 Blender 피팅 중...", progress=84)
            fitted_pants = await loop.run_in_executor(
                None, fit_cloth_blender, pants_raw, glb_path, 'pants', job_id, measurements)
            job_store.update(job_id, pants_glb_url=f"/{fitted_pants}")

        # STEP 4.6: 몸 + 피팅된 옷을 하나의 GLB로 병합 (앱 뷰어는 단일 GLB만 표시)
        job_mid = job_store.get(job_id) or {}
        shirt_p = (job_mid.get("shirt_glb_url") or "").lstrip("/")
        pants_p = (job_mid.get("pants_glb_url") or "").lstrip("/")

        def _valid_cloth(p):
            return p and os.path.exists(p) and not p.lower().endswith(_IMG_EXT)

        # 상·하의가 모두 있으면 허리 충돌 방지: 상의 밑단을 허리선에서 잘라 하의가 덮게 함
        if _valid_cloth(shirt_p) and _valid_cloth(pants_p):
            clip_top_under_bottom(shirt_p, pants_p)

        cloth_paths = [p for p in (shirt_p, pants_p) if _valid_cloth(p)]

        display_glb = glb_path
        if cloth_paths:
            try:
                job_store.update(job_id, step="아바타에 옷 입히는 중...", progress=88)
                dressed_path = f"outputs/avatars/{job_id}_dressed.glb"
                await loop.run_in_executor(
                    None, merge_glbs, dressed_path, [glb_path, *cloth_paths])
                display_glb = dressed_path
                print(f"[Pipeline] 옷 입은 아바타 병합 완료: {dressed_path}")
            except Exception as merge_err:
                print(f"[Pipeline] GLB 병합 실패, 맨몸 GLB 사용: {merge_err}")

        # STEP 5: 미리보기 렌더링 (선택 — 실패해도 피팅은 완료. 앱은 PNG가 아닌 GLB 뷰어 사용)
        job_store.update(job_id, step="렌더링 중...", progress=90)
        try:
            render_paths = await loop.run_in_executor(
                None, render_avatar_views, smplx_data, None, job_id)
        except Exception as render_err:
            print(f"[Pipeline] 렌더링 실패(무시), 미리보기 없이 진행: {render_err}")
            render_paths = []

        # STEP 6: 결과 매니페스트 JSON (Java 서버가 가져가 DB에 저장 → result_json_url)
        job_after = job_store.get(job_id) or {}
        result_path = f"outputs/{job_id}_result.json"
        result = {
            "job_id":           job_id,
            "status":           "done",
            "measurements_cm":  measurements_cm,             # user_measurements 스키마
            "smpl_mesh_url":    f"/outputs/debug/{job_id}/smplx.ply",
            "avatar_glb_url":   f"/{display_glb}",
            "shirt_glb_url":    job_after.get("shirt_glb_url"),
            "pants_glb_url":    job_after.get("pants_glb_url"),
            "render_urls":      [f"/{p}" for p in render_paths],
            "result_json_url":  f"/{result_path}",
        }
        with open(result_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        job_store.update(job_id, status="done", step="완료!", progress=100,
                         avatar_glb=f"/{display_glb}",
                         render_paths=[f"/{p}" for p in render_paths],
                         result_json_url=f"/{result_path}")

    except Exception as e:
        job_store.update(job_id, status="error", step=f"오류: {str(e)}", error=traceback.format_exc(), progress=0)
        print(traceback.format_exc())
