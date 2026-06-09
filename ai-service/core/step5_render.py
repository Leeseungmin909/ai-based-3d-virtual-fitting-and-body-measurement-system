import os
import numpy as np
from PIL import Image


def render_avatar_views(smplx_data: dict, texture_path: str, job_id: str) -> list:
    """pyrender 오프스크린으로 전/측면/후 3장 렌더링, 저장 경로 리스트 반환"""
    import pyrender, trimesh

    vertices = np.asarray(smplx_data["vertices"], dtype=np.float32)
    faces    = np.asarray(smplx_data["faces"],    dtype=np.int32)

    out_dir = f"outputs/renders/{job_id}"
    os.makedirs(out_dir, exist_ok=True)

    # trimesh 메쉬 구성
    mesh_tm = trimesh.Trimesh(vertices=vertices, faces=faces, process=False)

    # 텍스처 적용 시도, 실패 시 피부색
    if texture_path and os.path.exists(texture_path):
        try:
            tex_img = Image.open(texture_path).convert("RGBA")
            from core.uv_loader import load_smplx_uv
            uv = load_smplx_uv()
            uv_flip = uv.copy(); uv_flip[:, 1] = 1.0 - uv_flip[:, 1]
            mat = trimesh.visual.texture.TextureVisuals(
                uv=uv_flip,
                image=tex_img,
            )
            mesh_tm.visual = mat
        except Exception as e:
            print(f"[Step5] 텍스처 적용 실패 ({e}), 피부색 사용")
            mesh_tm.visual.vertex_colors = np.full((len(vertices), 4), [210, 180, 155, 255], dtype=np.uint8)
    else:
        mesh_tm.visual.vertex_colors = np.full((len(vertices), 4), [210, 180, 155, 255], dtype=np.uint8)

    py_mesh = pyrender.Mesh.from_trimesh(mesh_tm, smooth=True)

    # 카메라 거리 / 높이 기준
    body_height = float(vertices[:, 1].max())  # ~1.7
    cam_dist    = body_height * 1.5
    look_at_y   = body_height * 0.5            # 허리 높이

    W, H = 480, 720

    angles_deg = [0, 60, 180]   # 전면, 3/4, 후면
    labels     = ["front", "side", "back"]
    paths      = []

    for deg, label in zip(angles_deg, labels):
        rad = np.radians(deg)
        cam_x =  np.sin(rad) * cam_dist
        cam_z =  np.cos(rad) * cam_dist
        cam_pos = np.array([cam_x, look_at_y, cam_z])

        pose = _look_at_pose(cam_pos, np.array([0.0, look_at_y, 0.0]))

        scene = pyrender.Scene(bg_color=[0.08, 0.08, 0.12, 1.0],
                               ambient_light=[0.3, 0.3, 0.3])
        scene.add(py_mesh)

        camera = pyrender.PerspectiveCamera(yfov=np.radians(40),
                                            aspectRatio=W / H)
        scene.add(camera, pose=pose)

        # 키 라이트 (카메라 위-우측)
        kl_pose = _look_at_pose(cam_pos + np.array([cam_dist * 0.4, body_height * 0.5, 0]),
                                np.array([0.0, look_at_y, 0.0]))
        scene.add(pyrender.DirectionalLight(color=[1, 1, 1], intensity=4.0), pose=kl_pose)

        # 필 라이트 (반대편 약하게)
        fl_pose = _look_at_pose(-cam_pos + np.array([0, body_height * 0.3, 0]),
                                np.array([0.0, look_at_y, 0.0]))
        scene.add(pyrender.DirectionalLight(color=[0.8, 0.85, 1.0], intensity=1.5), pose=fl_pose)

        r = pyrender.OffscreenRenderer(W, H)
        color, _ = r.render(scene)
        r.delete()

        img_path = f"{out_dir}/{label}.png"
        Image.fromarray(color).save(img_path)
        paths.append(img_path)
        print(f"[Step5] {label} 렌더링 완료: {img_path}")

    return paths


def _look_at_pose(eye: np.ndarray, target: np.ndarray) -> np.ndarray:
    """eye 위치에서 target을 바라보는 4×4 카메라 pose 행렬"""
    up = np.array([0.0, 1.0, 0.0])
    z  = eye - target
    norm = np.linalg.norm(z)
    if norm < 1e-6:
        z = np.array([0.0, 0.0, 1.0])
    else:
        z /= norm
    x = np.cross(up, z)
    xn = np.linalg.norm(x)
    if xn < 1e-6:
        x = np.array([1.0, 0.0, 0.0])
    else:
        x /= xn
    y = np.cross(z, x)

    pose = np.eye(4)
    pose[:3, 0] = x
    pose[:3, 1] = y
    pose[:3, 2] = z
    pose[:3, 3] = eye
    return pose
