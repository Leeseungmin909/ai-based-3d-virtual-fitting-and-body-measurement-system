import os
import numpy as np
import pygltflib


def export_glb(smplx_data: dict, vertex_colors: np.ndarray, job_id: str) -> str:
    """버텍스 컬러(얼굴 투영 포함) + 법선 벡터 GLB 생성"""
    vertices = smplx_data["vertices"]
    faces    = smplx_data["faces"]

    out_dir  = "outputs/avatars"
    os.makedirs(out_dir, exist_ok=True)
    glb_path = f"{out_dir}/{job_id}_avatar.glb"

    _write_glb(vertices, faces, vertex_colors, glb_path)
    print(f"[Step4] GLB 저장 완료: {glb_path}")
    return glb_path


def _write_glb(vertices, faces, vertex_colors, glb_path):
    verts = np.asarray(vertices,     dtype=np.float32)
    tris  = np.asarray(faces,        dtype=np.uint32)
    # COLOR_0: uint8 RGB → float32 [0,1]
    vc    = np.asarray(vertex_colors, dtype=np.float32) / 255.0

    import trimesh
    normals = trimesh.Trimesh(vertices=verts, faces=tris, process=False) \
                     .vertex_normals.astype(np.float32)

    def _align4(b: bytes) -> bytes:
        r = len(b) % 4
        return b + b"\x00" * ((4 - r) % 4)

    vert_b  = _align4(verts.tobytes())
    norm_b  = _align4(normals.tobytes())
    color_b = _align4(vc.tobytes())
    idx_b   = _align4(tris.tobytes())

    off_v = 0
    off_n = len(vert_b)
    off_c = off_n + len(norm_b)
    off_i = off_c + len(color_b)
    blob  = vert_b + norm_b + color_b + idx_b

    n_v  = len(verts)
    n_i  = len(tris) * 3
    bmin = verts.min(axis=0).tolist()
    bmax = verts.max(axis=0).tolist()

    gltf = pygltflib.GLTF2(
        asset=pygltflib.Asset(version="2.0", generator="AVATARFIT"),
        scene=0,
        scenes=[pygltflib.Scene(nodes=[0])],
        nodes=[pygltflib.Node(mesh=0)],
        meshes=[pygltflib.Mesh(primitives=[pygltflib.Primitive(
            attributes=pygltflib.Attributes(POSITION=0, NORMAL=1, COLOR_0=2),
            indices=3,
            material=0,
            mode=pygltflib.TRIANGLES,
        )])],
        accessors=[
            pygltflib.Accessor(                                          # 0: position
                bufferView=0, byteOffset=0,
                componentType=pygltflib.FLOAT, count=n_v, type=pygltflib.VEC3,
                min=bmin, max=bmax,
            ),
            pygltflib.Accessor(                                          # 1: normal
                bufferView=1, byteOffset=0,
                componentType=pygltflib.FLOAT, count=n_v, type=pygltflib.VEC3,
            ),
            pygltflib.Accessor(                                          # 2: color
                bufferView=2, byteOffset=0,
                componentType=pygltflib.FLOAT, count=n_v, type=pygltflib.VEC3,
            ),
            pygltflib.Accessor(                                          # 3: indices
                bufferView=3, byteOffset=0,
                componentType=pygltflib.UNSIGNED_INT, count=n_i, type=pygltflib.SCALAR,
            ),
        ],
        bufferViews=[
            pygltflib.BufferView(buffer=0, byteOffset=off_v,
                                 byteLength=len(verts.tobytes()),
                                 target=pygltflib.ARRAY_BUFFER),
            pygltflib.BufferView(buffer=0, byteOffset=off_n,
                                 byteLength=len(normals.tobytes()),
                                 target=pygltflib.ARRAY_BUFFER),
            pygltflib.BufferView(buffer=0, byteOffset=off_c,
                                 byteLength=len(vc.tobytes()),
                                 target=pygltflib.ARRAY_BUFFER),
            pygltflib.BufferView(buffer=0, byteOffset=off_i,
                                 byteLength=len(tris.tobytes()),
                                 target=pygltflib.ELEMENT_ARRAY_BUFFER),
        ],
        materials=[pygltflib.Material(
            name="avatar",
            pbrMetallicRoughness=pygltflib.PbrMetallicRoughness(
                baseColorFactor=[1.0, 1.0, 1.0, 1.0],   # 버텍스 컬러를 그대로 표시
                metallicFactor=0.0,
                roughnessFactor=0.85,
            ),
            doubleSided=True,
        )],
        buffers=[pygltflib.Buffer(byteLength=len(blob))],
    )

    gltf.set_binary_blob(blob)
    gltf.save_binary(glb_path)
    print(f"[Step4] GLB {os.path.getsize(glb_path)/1024:.1f} KB (버텍스 컬러 {n_v}개)")
