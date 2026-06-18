"""여러 GLB를 glTF 레벨에서 하나로 병합한다.

앱의 model-viewer는 단일 GLB만 표시하므로, 몸 GLB와 피팅된 옷 GLB를
하나로 합쳐 "옷 입은 아바타"를 보여주기 위해 사용한다.
trimesh 재인코딩과 달리 원본 버퍼(COLOR_0 등)를 그대로 보존한다.
"""
import os
import copy
import pygltflib


def _pad4(b: bytes) -> bytes:
    return b + b"\x00" * ((4 - len(b) % 4) % 4)


def clip_top_under_bottom(top_path: str, bottom_path: str, overlap: float = 0.02) -> None:
    """하의 상단(허리) 높이를 경계로, 상의의 그 아래 부분을 잘라
    하의가 상의 밑단을 덮도록(상의를 하의에 넣은 듯) 한다.

    상의 밑단이 골반까지 길게 내려오는 것을 막고, 경계를 허리선으로 올린다.
    상·하의가 모두 있을 때만 병합 직전에 호출한다.
    """
    try:
        import trimesh
        import numpy as np
        top = trimesh.load(top_path, force="mesh")
        bottom = trimesh.load(bottom_path, force="mesh")
        by = np.asarray(bottom.vertices)[:, 1]
        # 하의 상단 밴드(상위 Y)에서 '가장 낮은' 지점 = 앞 중앙 dip.
        # 그 아래까지 상의를 남겨야 앞쪽에 틈이 안 생긴다(옆구리는 더 겹쳐 바지에 가려짐).
        band = by[by >= np.percentile(by, 85)]
        cut_y = float(band.min()) - overlap
        fy = np.asarray(top.vertices)[top.faces][:, :, 1]
        keep = (fy >= cut_y).all(axis=1)   # 세 정점 모두 컷 위인 face만 유지(상의 밑단 제거)
        removed = int((~keep).sum())
        if keep.sum() < 10 or removed == 0:
            return
        top.update_faces(keep)
        top.remove_unreferenced_vertices()
        top.export(top_path)
        print(f"[Merge] 상의 밑단 클립: y<{cut_y:.3f}m 제거 ({removed} faces)")
    except Exception as e:
        print(f"[Merge] 상의 클립 실패(무시): {e}")


def merge_glbs(out_path: str, paths: list) -> str:
    """paths[0](몸)에 나머지(옷)를 덧붙여 out_path로 저장하고 경로를 반환한다."""
    paths = [p for p in paths if p and os.path.exists(p)]
    if not paths:
        raise ValueError("병합할 GLB가 없습니다.")

    base = pygltflib.GLTF2().load(paths[0])
    blob = bytearray(base.binary_blob())

    for src_path in paths[1:]:
        g = pygltflib.GLTF2().load(src_path)
        blob = bytearray(_pad4(bytes(blob)))
        byte_shift = len(blob)
        blob += g.binary_blob()

        n_acc = len(base.accessors)
        n_bv = len(base.bufferViews)
        n_mat = len(base.materials)
        n_mesh = len(base.meshes)
        n_node = len(base.nodes)
        n_img = len(base.images)
        n_smp = len(base.samplers)
        n_tex = len(base.textures)

        for bv in g.bufferViews:
            bv = copy.deepcopy(bv)
            bv.buffer = 0
            bv.byteOffset = (bv.byteOffset or 0) + byte_shift
            base.bufferViews.append(bv)

        for ac in g.accessors:
            ac = copy.deepcopy(ac)
            if ac.bufferView is not None:
                ac.bufferView += n_bv
            base.accessors.append(ac)

        for im in g.images:
            base.images.append(copy.deepcopy(im))
        for sm in g.samplers:
            base.samplers.append(copy.deepcopy(sm))
        for tx in g.textures:
            tx = copy.deepcopy(tx)
            if tx.source is not None:
                tx.source += n_img
            if tx.sampler is not None:
                tx.sampler += n_smp
            base.textures.append(tx)

        for mt in g.materials:
            mt = copy.deepcopy(mt)
            pbr = mt.pbrMetallicRoughness
            if pbr and pbr.baseColorTexture and pbr.baseColorTexture.index is not None:
                pbr.baseColorTexture.index += n_tex
            base.materials.append(mt)

        for ms in g.meshes:
            ms = copy.deepcopy(ms)
            for pr in ms.primitives:
                a = pr.attributes
                for attr in ("POSITION", "NORMAL", "COLOR_0", "TEXCOORD_0", "TANGENT"):
                    v = getattr(a, attr, None)
                    if v is not None:
                        setattr(a, attr, v + n_acc)
                if pr.indices is not None:
                    pr.indices += n_acc
                if pr.material is not None:
                    pr.material += n_mat
            base.meshes.append(ms)

        for nd in g.nodes:
            nd = copy.deepcopy(nd)
            if nd.mesh is not None:
                nd.mesh += n_mesh
            if nd.children:
                nd.children = [c + n_node for c in nd.children]
            base.nodes.append(nd)

        roots = g.scenes[g.scene or 0].nodes if g.scenes else []
        base.scenes[base.scene or 0].nodes += [r + n_node for r in roots]

    base.buffers = [pygltflib.Buffer(byteLength=len(blob))]
    base.set_binary_blob(bytes(blob))
    base.save_binary(out_path)
    return out_path
