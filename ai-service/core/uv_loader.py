import numpy as np
import os
from core.config import SMPLX_UV_OBJ, SMPLX_UV_PNG

_cache = {}

def load_smplx_uv(obj_path: str | os.PathLike = SMPLX_UV_OBJ):
    """공식 SMPL-X UV2021 OBJ에서 UV 좌표 로드"""
    obj_path = os.fspath(obj_path)
    if obj_path in _cache:
        return _cache[obj_path]

    print(f"[UV] 공식 UV맵 로딩: {obj_path}")

    vt_list  = []  # UV 좌표 (텍스처 버텍스)
    f_list   = []  # face: (v_idx, vt_idx) 쌍
    ft_list  = []  # face의 UV 인덱스

    with open(obj_path, "r") as f:
        for line in f:
            line = line.strip()
            if line.startswith("vt "):
                parts = line.split()
                vt_list.append([float(parts[1]), float(parts[2])])
            elif line.startswith("f "):
                parts = line.split()[1:]
                v_ids, vt_ids = [], []
                for p in parts:
                    tokens = p.split("/")
                    v_ids.append(int(tokens[0]) - 1)   # 1-indexed → 0-indexed
                    if len(tokens) > 1 and tokens[1]:
                        vt_ids.append(int(tokens[1]) - 1)
                f_list.append(v_ids)
                ft_list.append(vt_ids)

    vt = np.array(vt_list, dtype=np.float32)  # (N_vt, 2)

    # SMPL-X 버텍스(10475개)별 UV 좌표 매핑
    # OBJ face에서 vertex → UV 매핑 추출
    n_verts = 10475
    uv_per_vert = np.zeros((n_verts, 2), dtype=np.float32)
    count       = np.zeros(n_verts, dtype=np.int32)

    for face_v, face_vt in zip(f_list, ft_list):
        if len(face_v) != len(face_vt):
            continue
        for v_idx, vt_idx in zip(face_v, face_vt):
            if 0 <= v_idx < n_verts and 0 <= vt_idx < len(vt):
                uv_per_vert[v_idx] += vt[vt_idx]
                count[v_idx] += 1

    # 평균 (여러 face에서 공유되는 버텍스)
    mask = count > 0
    uv_per_vert[mask] /= count[mask, np.newaxis]

    # V 좌표 뒤집기 (OpenGL 컨벤션)
    uv_per_vert[:, 1] = 1.0 - uv_per_vert[:, 1]

    print(f"[UV] 로딩 완료: {len(vt)}개 UV좌표, {len(f_list)}개 face")
    _cache[obj_path] = uv_per_vert
    return uv_per_vert


def get_uv_texture_path() -> str:
    return os.fspath(SMPLX_UV_PNG)
