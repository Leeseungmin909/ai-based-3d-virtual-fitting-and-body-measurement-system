"""
Blender 헤드리스 클로스 시뮬레이션 래퍼.
pipeline.py에서 호출: body GLB + cloth GLB -> Blender 시뮬 -> fitted GLB
"""
import os
import subprocess
import traceback
import tempfile

# Blender 실행 파일 탐색 경로 (Windows 버전별)
_BLENDER_PATHS = [
    r"C:\Program Files\Blender Foundation\Blender 5.1\blender.exe",
    r"C:\Program Files\Blender Foundation\Blender 5.0\blender.exe",
    r"C:\Program Files\Blender Foundation\Blender 4.4\blender.exe",
    r"C:\Program Files\Blender Foundation\Blender 4.3\blender.exe",
    r"C:\Program Files\Blender Foundation\Blender 4.2\blender.exe",
    r"C:\Program Files\Blender Foundation\Blender 4.1\blender.exe",
    r"C:\Program Files\Blender Foundation\Blender 4.0\blender.exe",
    r"C:\Program Files\Blender Foundation\Blender 3.6\blender.exe",
    r"C:\Program Files\Blender Foundation\Blender 3.5\blender.exe",
]


def _find_blender() -> str | None:
    for p in _BLENDER_PATHS:
        if os.path.exists(p):
            return p
    try:
        r = subprocess.run(["blender", "--version"],
                           capture_output=True, timeout=5)
        if r.returncode == 0:
            return "blender"
    except Exception:
        pass
    return None


_DECIMATE_TARGET = 15000  # 사전 데시메이션 최대 face 수 (하의용 — 셔츠는 Blender 내부 데시메이션)


def _predecimate_glb(cloth_glb_path: str) -> str:
    """
    pymeshlab로 고품질 데시메이션 후 임시 GLB 반환.
    _DECIMATE_TARGET 이하면 원본 경로 그대로 반환.
    """
    try:
        import pymeshlab
        import trimesh

        m_check = trimesh.load(cloth_glb_path, force='mesh')
        n = len(m_check.faces)
        del m_check
        if n <= _DECIMATE_TARGET:
            return cloth_glb_path

        print(f"[BlenderCloth] Pre-decimate: {n} -> {_DECIMATE_TARGET} faces (pymeshlab)")
        ms = pymeshlab.MeshSet()
        ms.load_new_mesh(cloth_glb_path)
        ms.apply_filter('meshing_merge_close_vertices',
                        threshold=pymeshlab.PercentageValue(0.0))
        ms.apply_filter('meshing_decimation_quadric_edge_collapse',
                        targetfacenum=_DECIMATE_TARGET,
                        qualitythr=0.3,
                        preserveboundary=True,
                        preservenormal=True)

        tmp_obj = tempfile.NamedTemporaryFile(suffix=".obj", delete=False)
        tmp_obj.close()
        ms.save_current_mesh(tmp_obj.name)

        tmp_glb = tempfile.NamedTemporaryFile(suffix=".glb", delete=False)
        tmp_glb.close()
        mesh = trimesh.load(tmp_obj.name, force='mesh')
        mesh.export(tmp_glb.name)
        for ext in ('.obj', '.mtl'):
            p = tmp_obj.name.replace('.obj', ext)
            if os.path.exists(p):
                os.unlink(p)

        kb = os.path.getsize(tmp_glb.name) // 1024
        print(f"[BlenderCloth] Pre-decimate done: {len(mesh.faces)} faces ({kb}KB)")
        return tmp_glb.name
    except Exception:
        print(f"[BlenderCloth] Pre-decimate failed, using original\n{traceback.format_exc()}")
        return cloth_glb_path


def _transfer_deformation(proxy_orig_path: str, proxy_def_path: str,
                           shirt_orig_path: str, out_path: str,
                           max_residual: float = 0.25) -> None:
    """
    pygltflib로 GLB 바이너리를 직접 패치: POSITION만 수정, NORMAL은 원본 유지.

    변위 전달 방식: 앞/뒤 분리 IDW (Side-aware Inverse Distance Weighting)
    """
    import numpy as np
    import pygltflib, struct
    from scipy.spatial import KDTree

    pre_npy  = proxy_def_path.replace('.glb', '_pre.npy')
    disp_npy = proxy_def_path.replace('.glb', '_disp.npy')

    if not (os.path.exists(pre_npy) and os.path.exists(disp_npy)):
        raise FileNotFoundError(f"_pre.npy / _disp.npy 없음: {pre_npy}")

    pre_verts = np.load(pre_npy).astype(np.float64)   # (N_proxy, 3) GLTF Y-up
    disp      = np.load(disp_npy).astype(np.float64)  # (N_proxy, 3)

    # 전체 평균 변위 (translation 성분) — residual 클램프 기준
    mean_disp = disp.mean(axis=0)                      # (3,)
    MAX_RESIDUAL = max_residual                        # 이 이상 local 변형은 클램프 (셔츠는 소매 드레이프 때문에 크게)

    # ── 프록시를 앞면(Z≥0) / 뒷면(Z<0) 으로 분리 ─────────────────────────
    fm = pre_verts[:, 2] >= 0
    bm = ~fm
    tree_f = KDTree(pre_verts[fm])
    tree_b = KDTree(pre_verts[bm])
    disp_f = disp[fm]
    disp_b = disp[bm]
    mean_y = float(disp[:, 1].mean())
    print(f"[BlenderCloth] side-IDW: front={fm.sum()} back={bm.sum()} verts  "
          f"Y+{mean_y:.4f}m  max_res_clamp={MAX_RESIDUAL}m")

    _K = 8

    def _idw(tree: KDTree, disp_side: np.ndarray,
             pts: np.ndarray) -> np.ndarray:
        """IDW 변위 계산 + residual 클램프 (폭발 버텍스로 인한 찢김 방지)"""
        if len(pts) == 0:
            return np.zeros((0, 3), dtype=np.float64)
        dists, idx = tree.query(pts, k=min(_K, len(disp_side)))
        dists = np.maximum(dists, 1e-6)
        w = 1.0 / (dists ** 2)
        w /= w.sum(axis=1, keepdims=True)
        result = (w[:, :, None] * disp_side[idx]).sum(axis=1)  # (N, 3)

        # residual = IDW결과 - translation 성분
        residual = result - mean_disp                           # (N, 3)
        res_mag  = np.linalg.norm(residual, axis=1)            # (N,)
        oversized = res_mag > MAX_RESIDUAL
        if oversized.any():
            scale = MAX_RESIDUAL / res_mag[oversized]
            residual[oversized] *= scale[:, None]
        return mean_disp + residual

    gltf = pygltflib.GLTF2().load(shirt_orig_path)
    blob = bytearray(gltf.binary_blob())
    total_verts = 0

    # ── 원본 GLB 단위 감지 ────────────────────────────────────────────────
    # pre_verts/disp는 Blender에서 항상 미터 단위로 저장됨.
    # 원본 GLB가 cm(max accessor coord > 3.0)이면 미터로 변환 후 IDW,
    # 출력도 미터로 저장 (뷰어의 body GLB와 단위 통일).
    _to_m = 1.0
    for _mg in gltf.meshes:
        for _pg in _mg.primitives:
            if _pg.attributes.POSITION is None: continue
            _ac = gltf.accessors[_pg.attributes.POSITION]
            _mx = max(abs(v) for v in (_ac.max or [])) if _ac.max else 0
            if _mx > 3.0:
                _to_m = 0.01
                print(f"[BlenderCloth] 원본 GLB cm 단위 감지(max={_mx:.1f}) → 미터 변환 후 IDW")
            break
        break

    for mesh in gltf.meshes:
        for prim in mesh.primitives:
            pos_idx = prim.attributes.POSITION
            if pos_idx is None:
                continue

            pa   = gltf.accessors[pos_idx]
            pbv  = gltf.bufferViews[pa.bufferView]
            poff = (pbv.byteOffset or 0) + (pa.byteOffset or 0)
            ps   = pbv.byteStride if pbv.byteStride else 12
            n    = pa.count

            if ps == 12:
                verts = np.frombuffer(blob[poff:poff + n*12],
                                      dtype=np.float32).reshape(n, 3).copy()
            else:
                verts = np.array([struct.unpack_from('3f', blob, poff + i*ps)
                                  for i in range(n)], dtype=np.float32)

            # ── 단위 정규화 + 앞/뒤 분리 IDW + Z≈0 소프트 블렌딩 ───────────
            # v64를 미터 단위로 변환 → proxy(미터)와 좌표계 일치 → KDTree 올바름
            v64 = verts.astype(np.float64) * _to_m   # cm이면 0.01, 미터면 1.0
            z   = v64[:, 2]
            BLEND = 0.015

            fi   = np.where(z >= BLEND)[0]
            bi   = np.where(z <= -BLEND)[0]
            mi   = np.where((z > -BLEND) & (z < BLEND))[0]

            new_verts = v64.copy()
            if len(fi): new_verts[fi] += _idw(tree_f, disp_f, v64[fi])
            if len(bi): new_verts[bi] += _idw(tree_b, disp_b, v64[bi])
            if len(mi):
                t = (z[mi] / BLEND + 1.0) * 0.5
                d_f = _idw(tree_f, disp_f, v64[mi])
                d_b = _idw(tree_b, disp_b, v64[mi])
                new_verts[mi] += (1 - t)[:, None] * d_b + t[:, None] * d_f
            # new_verts는 미터 단위로 출력 (body GLB와 단위 통일)
            new_verts = new_verts.astype(np.float32)

            if ps == 12:
                blob[poff:poff + n*12] = new_verts.tobytes()
            else:
                for i in range(n):
                    struct.pack_into('3f', blob, poff + i*ps, *new_verts[i])

            pa.min = new_verts.min(axis=0).tolist()
            pa.max = new_verts.max(axis=0).tolist()
            total_verts += n

    gltf.set_binary_blob(bytes(blob))
    gltf.save(out_path)
    kb = os.path.getsize(out_path) // 1024
    print(f"[BlenderCloth] IDW transfer: {total_verts} verts → {out_path} ({kb}KB)")


def _dominant_color(thumb_path: str):
    """상품 썸네일 중앙 영역에서 배경(흰색)을 제외한 대표 색(RGB)을 추출한다."""
    import numpy as np
    from PIL import Image
    im = Image.open(thumb_path).convert("RGB")
    a = np.asarray(im)
    h, w, _ = a.shape
    c = a[int(h * 0.3):int(h * 0.7), int(w * 0.3):int(w * 0.7)].reshape(-1, 3)
    bright = c.mean(1)
    sat = c.max(1).astype(int) - c.min(1).astype(int)
    mask = ~((bright > 225) & (sat < 18))   # 밝고 무채색(흰 배경) 제거
    g = c[mask] if mask.sum() > 50 else c
    return tuple(int(x) for x in np.median(g, 0))


def _apply_thumbnail_color(glb_path: str, source_cloth_path: str) -> None:
    """옷 썸네일(상품 사진)의 대표 색을 피팅된 옷 메시에 균일하게 입힌다.

    옷 3D 모델에 색·텍스처·UV가 없어 흰색으로 렌더되는 문제를 보정한다.
    질감(프린트)은 UV가 없어 적용 불가하므로 단색만 입힌다.
    """
    try:
        import os
        import numpy as np
        import trimesh
        thumb = os.path.join(os.path.dirname(source_cloth_path), "thumbnail.jpg")
        if not os.path.exists(thumb):
            return
        r, g, b = _dominant_color(thumb)
        m = trimesh.load(glb_path, force="mesh")
        vc = np.tile(np.array([r, g, b, 255], np.uint8), (len(m.vertices), 1))
        m.visual = trimesh.visual.ColorVisuals(m, vertex_colors=vc)
        m.export(glb_path)
        print(f"[BlenderCloth] 옷 색 적용: #{r:02X}{g:02X}{b:02X} ({os.path.basename(os.path.dirname(source_cloth_path))})")
    except Exception as e:
        print(f"[BlenderCloth] 옷 색 적용 실패(무시): {e}")


def fit_cloth_blender(cloth_glb_path: str, body_glb_path: str,
                      cloth_type: str, job_id: str,
                      measurements: dict | None = None) -> str:
    """
    Blender 클로스 시뮬로 의상 피팅.
    measurements: SMPL-X 신체 치수 (shirt/pants 너비·깊이·높이) — 정밀 스케일링에 사용.
    성공 시 fitted GLB 경로 반환, 실패 시 원본 cloth_glb_path 반환.
    """
    import json as _json
    blender = _find_blender()
    if not blender:
        print("[BlenderCloth] Blender 미설치 -> 원본 반환")
        return cloth_glb_path

    script = os.path.abspath("blender_scripts/cloth_sim.py")
    if not os.path.exists(script):
        print(f"[BlenderCloth] 스크립트 없음: {script}")
        return cloth_glb_path

    # 셔츠: pymeshlab(OBJ 경유)은 UV·텍스처를 잃음 → 원본 그대로 Blender에 넘기고
    #       Blender 내부 Decimate(UV 보존)로 줄임. 하의는 기존 경로 유지(IDW용 프록시).
    if cloth_type == 'shirt':
        decimated_path = os.path.abspath(cloth_glb_path)
    else:
        decimated_path = _predecimate_glb(os.path.abspath(cloth_glb_path))
    tmp_created = decimated_path != os.path.abspath(cloth_glb_path)

    # SMPL-X 측정값 → 임시 JSON 파일 (Blender 스크립트에 전달)
    meas_path = None
    if measurements:
        mf = tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode='w',
                                         encoding='utf-8')
        _json.dump(measurements, mf)
        mf.close()
        meas_path = mf.name

    os.makedirs("outputs", exist_ok=True)
    output_rel  = f"outputs/{job_id}_blender_{cloth_type}.glb"
    output_path = os.path.abspath(output_rel)

    cmd = [
        blender,
        "--background",
        "--python", script,
        "--",
        os.path.abspath(body_glb_path),
        decimated_path,
        output_path,
        cloth_type,
    ]
    if meas_path:
        cmd.append(meas_path)

    log_path = os.path.abspath(f"outputs/{job_id}_blender_{cloth_type}.log")
    print(f"[BlenderCloth] {cloth_type} 시뮬 시작... (log: {log_path})")
    try:
        with open(log_path, 'w', encoding='utf-8', errors='replace') as _log_f:
            result = subprocess.run(
                cmd,
                stdout=_log_f,
                stderr=subprocess.STDOUT,
                timeout=900,   # Surface Deform 바인딩(hi-res) 시간 여유
                cwd=os.path.abspath("."),
            )

        if result.returncode == 2:
            # 폭발 감지 (cloth_sim.py sys.exit(2))
            print(f"[BlenderCloth] ⚠ explosion rc=2 → {cloth_type} 원본 반환")
            return cloth_glb_path

        if os.path.exists(output_path) and result.returncode == 0:
            # 셔츠: Blender가 Surface Deform으로 hi-res를 직접 출력 → IDW 불필요.
            # 하의: 원본 고품질 메쉬에 변형 전달(IDW).
            if tmp_created and cloth_type != 'shirt':
                _transfer_deformation(
                    proxy_orig_path=decimated_path,
                    proxy_def_path=output_path,
                    shirt_orig_path=os.path.abspath(cloth_glb_path),
                    out_path=output_path,
                )
            # 임시 파일 정리
            for _suf in ('_pre.npy', '_post.npy', '_disp.npy', '_faces.npy'):
                _p = output_path.replace('.glb', _suf)
                if os.path.exists(_p):
                    os.unlink(_p)
            # 옷 썸네일 대표 색을 입힘 (모델에 색이 없어 흰색으로 나오는 문제 보정)
            _apply_thumbnail_color(output_path, cloth_glb_path)
            kb = os.path.getsize(output_path) // 1024
            print(f"[BlenderCloth] OK {cloth_type} -> {output_rel} ({kb}KB)")
            return output_rel
        else:
            # 로그 끝 500자 출력
            try:
                with open(log_path, encoding='utf-8', errors='replace') as _lf:
                    _tail = _lf.read()[-500:]
            except Exception:
                _tail = ""
            print(f"[BlenderCloth] failed rc={result.returncode}\n{_tail}")
            return cloth_glb_path

    except subprocess.TimeoutExpired:
        print("[BlenderCloth] timeout -> fallback")
        return cloth_glb_path
    except Exception:
        print(f"[BlenderCloth] error: {traceback.format_exc()}")
        return cloth_glb_path
    finally:
        if tmp_created and os.path.exists(decimated_path):
            os.unlink(decimated_path)
        if meas_path and os.path.exists(meas_path):
            os.unlink(meas_path)
