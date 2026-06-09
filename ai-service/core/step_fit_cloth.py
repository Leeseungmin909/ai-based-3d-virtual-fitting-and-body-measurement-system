"""
Cloth-to-body fitting — 단순 위치 정렬 방식.

PBD/물리 시뮬레이션은 Meshy AI GLB의 임의 토폴로지에서 불안정하므로 사용하지 않음.
대신:
  1. 단위 감지 (cm → m)
  2. Y축 스케일: 상의는 body 상체 높이에 맞춤, 하의는 body 하체 높이에 맞춤
  3. X/Z: 원본 크기 유지 (소매/다리 폭은 Meshy AI 디자인 그대로)
  4. 위치 정렬: 상의는 어깨-골반 중간, 하의는 발바닥 기준
  5. 약간 앞으로 오프셋 (Z+0.01m) — 아바타와 겹침 방지
"""
import os
import traceback
import numpy as np


def fit_cloth_glb(cloth_glb_path: str, smplx_data: dict,
                  cloth_type: str, job_id: str) -> str:
    """
    의상 GLB를 SMPL-X 체형에 맞게 위치/스케일 정렬 후 저장.
    cloth_type: 'shirt' | 'pants'
    실패 시 원본 경로 반환.
    """
    try:
        import trimesh
    except ImportError:
        print("[FitCloth] trimesh 미설치")
        return cloth_glb_path

    try:
        # ── 신체 치수 계산 ─────────────────────────────────────────────
        from core.step3_texture import compute_body_measurements
        meas_all = compute_body_measurements(smplx_data)
        meas_key = "shirt" if cloth_type == "shirt" else "pants"
        meas     = meas_all.get(meas_key)

        # fallback: body vertices 에서 직접 계산
        if meas is None:
            bv = np.asarray(smplx_data["vertices"])
            bj = np.asarray(smplx_data.get("joints", np.zeros((55, 3))))
            pelvis_y = float(bj[0, 1]) if len(bj) > 0 else 0.88
            shoulder_y = float((bj[16, 1] + bj[17, 1]) / 2) if len(bj) > 17 else 1.38
            if cloth_type == "shirt":
                y_min, y_max = pelvis_y * 0.95, shoulder_y * 1.02
            else:
                y_min, y_max = 0.0, pelvis_y * 1.02
            meas = {"y_min": y_min, "y_max": y_max, "y_mid": (y_min + y_max) / 2}

        # ── 의상 로드 ─────────────────────────────────────────────────
        loaded = trimesh.load(cloth_glb_path, force="scene", process=False)
        if isinstance(loaded, trimesh.Scene):
            geoms = loaded.geometry
        else:
            geoms = {"_mesh": loaded}

        if not geoms:
            return cloth_glb_path

        # ── 단위 자동 감지 ────────────────────────────────────────────
        all_v   = np.vstack([m.vertices for m in geoms.values()])
        max_dim = float((all_v.max(axis=0) - all_v.min(axis=0)).max())
        to_m    = 0.01 if max_dim > 3.0 else 1.0
        print(f"[FitCloth] {cloth_type}  max_dim={max_dim:.3f}  to_m={to_m}")

        # ── 각 서브메쉬 변환 ─────────────────────────────────────────
        for mesh in geoms.values():
            v = mesh.vertices.astype(np.float64) * to_m

            vlo, vhi = v.min(axis=0), v.max(axis=0)
            csz = vhi - vlo
            if csz.min() < 1e-6:
                continue

            # ── Y 스케일: body 영역 높이에 맞춤 ─────────────────────
            body_h  = meas["y_max"] - meas["y_min"]
            y_ease  = 0.02  # 2cm 여유
            sy      = (body_h + y_ease) / csz[1] if csz[1] > 0.01 else 1.0
            # X/Z: 원본 유지 (소매폭/두께 변형 금지)
            sx, sz  = 1.0, 1.0

            v = v.copy()
            v[:, 1] *= sy   # Y만 스케일

            # ── 위치 정렬 ─────────────────────────────────────────────
            vlo2, vhi2 = v.min(axis=0), v.max(axis=0)
            ctr = (vlo2 + vhi2) / 2

            if cloth_type == "shirt":
                # 상의: 중심을 body 상체 Y 중앙에, Z는 약간 앞으로
                target_y = meas["y_mid"]
                v[:, 0] -= ctr[0]               # X 중앙 정렬
                v[:, 1] += target_y - ctr[1]    # Y 정렬
                v[:, 2] -= ctr[2] - 0.01        # Z: 약간 앞으로
            else:
                # 하의: 하단을 발바닥(y=0)에 맞춤
                v[:, 1] -= vlo2[1]
                v[:, 0] -= ctr[0]
                v[:, 2] -= ctr[2] - 0.01

            mesh.vertices = v

            vlo3, vhi3 = v.min(axis=0), v.max(axis=0)
            print(f"[FitCloth] {cloth_type}  sy={sy:.3f}"
                  f"  Y=[{vlo3[1]:.2f},{vhi3[1]:.2f}]"
                  f"  Z=[{vlo3[2]:.2f},{vhi3[2]:.2f}]")

        # ── 저장 ──────────────────────────────────────────────────────
        os.makedirs("outputs", exist_ok=True)
        out = f"outputs/{job_id}_fitted_{cloth_type}.glb"
        if isinstance(loaded, trimesh.Scene):
            loaded.export(out, file_type="glb")
        else:
            list(geoms.values())[0].export(out, file_type="glb")

        print(f"[FitCloth] 저장: {out}")
        return out

    except Exception:
        print(f"[FitCloth] 오류 → 원본 반환\n{traceback.format_exc()}")
        return cloth_glb_path
