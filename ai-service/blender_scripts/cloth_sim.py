"""
Blender 헤드리스 클로스 시뮬레이션 스크립트
사용법:
    blender --background --python cloth_sim.py -- body.glb cloth.glb output.glb [shirt|pants]

좌표계:
    GLTF Y-up → Blender Z-up 자동 변환
    Blender: X=폭, Y=앞뒤(−Y=앞), Z=높이
"""
import bpy
import sys
import os


def get_args():
    argv = sys.argv
    return argv[argv.index("--") + 1:] if "--" in argv else []


def clear_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=True)
    for coll in (bpy.data.meshes, bpy.data.materials, bpy.data.images):
        for item in list(coll):
            coll.remove(item)


def import_glb(filepath):
    """GLB 임포트 → 새 MESH 오브젝트 리스트"""
    before = set(bpy.data.objects.keys())
    bpy.ops.import_scene.gltf(filepath=os.path.abspath(filepath))
    after  = set(bpy.data.objects.keys())
    return [bpy.data.objects[k] for k in (after - before)
            if bpy.data.objects[k].type == 'MESH']


def join_meshes(obj_list):
    """메쉬 목록 → 하나로 합치기"""
    if not obj_list:
        return None
    if len(obj_list) == 1:
        return obj_list[0]
    bpy.ops.object.select_all(action='DESELECT')
    for o in obj_list:
        o.select_set(True)
    bpy.context.view_layer.objects.active = obj_list[0]
    bpy.ops.object.join()
    return bpy.context.active_object


def get_bbox(obj):
    """
    bound_box 8코너를 월드 변환 → (x0,x1, y0,y1, z0,z1)
    Blender Z-up: z = 높이
    """
    import mathutils
    corners = [obj.matrix_world @ mathutils.Vector(c) for c in obj.bound_box]
    xs = [c.x for c in corners]
    ys = [c.y for c in corners]
    zs = [c.z for c in corners]
    return min(xs), max(xs), min(ys), max(ys), min(zs), max(zs)


def set_active(obj):
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj


# ─────────────────────────────────────────────────────────────────────────────

def main():
    args = get_args()
    if len(args) < 4:
        print("[ERROR] 인수 부족: body.glb cloth.glb output.glb [shirt|pants]")
        sys.exit(1)

    body_path   = args[0]
    cloth_path  = args[1]
    output_path = args[2]
    cloth_type  = args[3]

    # args[4] (선택): SMPL-X 신체 치수 JSON 파일 경로
    import json as _json
    smplx_meas = None
    if len(args) > 4 and os.path.exists(args[4]):
        try:
            with open(args[4], encoding='utf-8') as _f:
                smplx_meas = _json.load(_f)
            _sm = smplx_meas.get(cloth_type, smplx_meas.get('shirt' if cloth_type == 'shirt' else 'pants', {}))
            print(f"[Cloth] SMPL-X 측정값: w={_sm.get('width')}  d={_sm.get('depth')}  "
                  f"y_max={_sm.get('y_max')}")
        except Exception as _e:
            print(f"[Cloth] 측정값 로드 실패: {_e}")

    print(f"[Cloth] type={cloth_type}  cloth={os.path.basename(cloth_path)}")

    # ① 씬 초기화
    clear_scene()
    # 셔츠/하의 모두 정상 중력 → 여분 천이 belly에 자연 드레이프.
    # 셔츠 칼라는 어깨 요크 핀(강도↑)으로 목에 유지.
    bpy.context.scene.gravity[2] = -9.81

    # ② Body 임포트 → 충돌체 설정
    body_list = import_glb(body_path)
    if not body_list:
        print("[ERROR] body mesh 없음"); sys.exit(1)
    body_obj = join_meshes(body_list)
    body_obj.name = "Body"

    set_active(body_obj)
    bpy.ops.object.modifier_add(type='COLLISION')
    body_obj.collision.thickness_outer = 0.005
    body_obj.collision.friction_factor  = 5.0

    bx0, bx1, by0, by1, bz0, bz1 = get_bbox(body_obj)
    body_h     = bz1 - bz0
    body_depth = by1 - by0
    print(f"[Cloth] Body: h={body_h:.3f}m  depth={body_depth:.3f}m  faces={len(body_obj.data.polygons)}")

    # 바닥 충돌 평면
    bpy.ops.mesh.primitive_plane_add(size=6.0, location=(0, 0, bz0 - 0.01))
    floor_obj = bpy.context.active_object
    floor_obj.name = "Floor_Collision"
    bpy.ops.object.modifier_add(type='COLLISION')
    floor_obj.collision.thickness_outer = 0.002
    floor_obj.collision.friction_factor  = 2.0

    # ③ Cloth 임포트
    cloth_list = import_glb(cloth_path)
    if not cloth_list:
        print("[ERROR] cloth mesh 없음"); sys.exit(1)
    cloth_obj = join_meshes(cloth_list)
    cloth_obj.name = "Cloth"
    set_active(cloth_obj)

    # ④ 단위 감지 (cm → m)
    cx0, cx1, cy0, cy1, cz0, cz1 = get_bbox(cloth_obj)
    max_dim = max(cx1-cx0, cy1-cy0, cz1-cz0)
    if max_dim > 3.0:
        cloth_obj.scale = (0.01, 0.01, 0.01)
        bpy.ops.object.transform_apply(scale=True)
        cx0, cx1, cy0, cy1, cz0, cz1 = get_bbox(cloth_obj)
        print(f"[Cloth] cm→m 변환 완료")

    cloth_depth = cy1 - cy0
    cz_ctr = (cz0 + cz1) / 2
    cx_ctr = (cx0 + cx1) / 2
    cy_ctr = (cy0 + cy1) / 2
    print(f"[Cloth] Cloth: h={cz1-cz0:.3f}m  depth={cloth_depth:.3f}m  faces={len(cloth_obj.data.polygons)}")

    # ④.5  원본 프록시 버텍스 월드 좌표 저장 (변형 전달용)
    import numpy as np
    def _save_verts_gltf(obj, path):
        """Blender 월드 좌표(Z-up) → GLTF(Y-up): (X,Y,Z)_B → (X,Z,-Y)_G"""
        import mathutils
        vs = [obj.matrix_world @ v.co for v in obj.data.vertices]
        arr = np.array([[v.x, v.z, -v.y] for v in vs], dtype=np.float32)
        np.save(path, arr)
        return arr
    pre_npy  = output_path.replace('.glb', '_pre.npy')
    pre_verts_g = _save_verts_gltf(cloth_obj, pre_npy)

    # ⑤ Y축 스케일 (front-back depth)
    # 핵심: 셔츠 깊이 < 바디 깊이이면 바디가 셔츠를 뚫어 시뮬 즉시 폭발
    # → 셔츠 깊이가 반드시 바디 깊이 × 1.1 이상이 되도록 스케일 (캡 없음)
    _sm = (smplx_meas or {}).get(cloth_type, {})
    if cloth_type == 'shirt':
        # 깊이는 바디 + 소폭 여유만(부풀림 최소) → 중력이 앞면을 belly에 드레이프.
        # 깊이 축소는 소매 길이(X축)에 영향 없음.
        target_d = max(_sm.get('depth', body_depth), body_depth) * 1.05
        scale_y = target_d / max(cloth_depth, 0.05)
        print(f"[Cloth] shirt depth: cloth={cloth_depth:.3f}m body={body_depth:.3f}m target={target_d:.3f}m scale={scale_y:.3f}")
    else:
        target_d = _sm.get('depth', body_depth) + 0.08
        scale_y = min(target_d / max(cloth_depth, 0.05), 1.4)
    if scale_y > 1.01:
        cloth_obj.scale.y = scale_y
        bpy.ops.object.transform_apply(scale=True)
        cx0, cx1, cy0, cy1, cz0, cz1 = get_bbox(cloth_obj)
        cy_ctr = (cy0 + cy1) / 2
        print(f"[Cloth] Y-scale: {scale_y:.3f}")

    # ⑤.5 X축 스케일 (left-right width)
    # 셔츠: SMPL-X 토르소 너비(팔 제외) + 10% 여유 — 캡 없음
    # 하의: 기존 캡 유지
    cloth_w = cx1 - cx0
    if cloth_type == 'shirt':
        target_w = max(_sm.get('width', bx1-bx0), 0.1) * 1.1 + 0.05
        scale_x = target_w / max(cloth_w, 0.05)
        print(f"[Cloth] shirt width: cloth={cloth_w:.3f}m target={target_w:.3f}m scale={scale_x:.3f}")
    else:
        target_w = _sm.get('width', bx1-bx0) + 0.06
        scale_x = min(target_w / max(cloth_w, 0.05), 1.4)
    if scale_x > 1.01:
        cloth_obj.scale.x = scale_x
        bpy.ops.object.transform_apply(scale=True)
        cx0, cx1, cy0, cy1, cz0, cz1 = get_bbox(cloth_obj)
        cx_ctr = (cx0 + cx1) / 2
        print(f"[Cloth] X-scale: {scale_x:.3f}")

    # ⑥ 초기 위치 정렬 (상단 기준: collar → 어깨, waistband → 허리)
    if cloth_type == 'shirt':
        # 카라가 목 밑단~어깨를 덮도록 배치. neck_y(목 조인트) + lift.
        # 0.12 = 어깨 맨살 틈 방지(실제 neck_y 기준).
        COLLAR_LIFT = 0.12
        neck_y = (smplx_meas or {}).get('neck_y')
        if neck_y:
            collar_z = bz0 + neck_y + COLLAR_LIFT
            print(f"[Cloth] collar_z from neck_y({neck_y:.3f})+lift: {collar_z:.4f}m")
        elif _sm.get('y_max'):
            collar_z = bz0 + _sm['y_max'] + COLLAR_LIFT
            print(f"[Cloth] collar_z from y_max+lift: {collar_z:.4f}m")
        else:
            collar_z = bz0 + body_h * 0.86
        cloth_obj.location.x = -cx_ctr
        cloth_obj.location.y = -cy_ctr
        cloth_obj.location.z = collar_z - cz1
    else:
        # 하의 상단(waistband): SMPL-X y_max 사용, 없으면 58% fallback
        if _sm.get('y_max'):
            waist_z = bz0 + _sm['y_max']
        else:
            waist_z = bz0 + body_h * 0.58
        cloth_obj.location.x = -cx_ctr
        cloth_obj.location.y = -cy_ctr
        cloth_obj.location.z = waist_z - cz1

    bpy.ops.object.transform_apply(location=True)
    print(f"[Cloth] 위치 정렬 완료")

    # ⑦ 핀 그룹: 상단 고정
    verts  = cloth_obj.data.vertices
    z_vals = [v.co.z for v in verts]
    z_max, z_min = max(z_vals), min(z_vals)
    pg = cloth_obj.vertex_groups.new(name="Pin")
    if cloth_type == 'shirt':
        # 어깨 요크만 핀, 칼라 구멍(목 둘레)은 핀 제외 → 목 충돌이 천을 밀어내
        # 관통 방지. (중심축 neck_r 이내 상단 정점은 자유)
        pin_z = z_max - (z_max - z_min) * 0.18
        x_vals = [v.co.x for v in verts]
        y_vals = [v.co.y for v in verts]
        cx = (max(x_vals) + min(x_vals)) / 2
        cy = (max(y_vals) + min(y_vals)) / 2
        neck_r = 0.12   # 목 둘레 반경 + 여유
        pin_ids = [v.index for v in verts
                   if v.co.z >= pin_z
                   and ((v.co.x - cx) ** 2 + (v.co.y - cy) ** 2) > neck_r ** 2]
    else:
        pin_z = z_max - (z_max - z_min) * 0.12
        pin_ids = [v.index for v in verts if v.co.z >= pin_z]
    pg.add(pin_ids, 1.0, 'REPLACE')
    print(f"[Cloth] pin group: {len(pin_ids)} verts")

    # ⑧ 클로스 모디파이어
    set_active(cloth_obj)
    bpy.ops.object.modifier_add(type='CLOTH')
    cm = cloth_obj.modifiers["Cloth"]
    cm.settings.quality               = 15
    cm.settings.mass                  = 0.3
    cm.settings.tension_stiffness     = 25.0
    cm.settings.compression_stiffness = 25.0
    cm.settings.shear_stiffness       = 10.0
    cm.settings.bending_stiffness     = 1.5
    cm.settings.air_damping           = 10.0   # 공기 저항 증가: 진동→폭발 방지
    cm.settings.vertex_group_mass     = "Pin"   # Blender 5.x API
    cm.settings.pin_stiffness         = 1.0
    if cloth_type == 'shirt':
        # 어깨 요크 핀 강도↑ → 칼라 목에 고정.
        # 굽힘 강성↓ → 앞면이 belly 윤곽에 부드럽게 컨폼(뻣뻣한 풍선 방지).
        cm.settings.pin_stiffness     = 5.0
        cm.settings.bending_stiffness = 0.3
        cm.settings.tension_stiffness = 15.0
    cm.collision_settings.use_collision      = True
    # 목/몸통이 천을 뚫지 않도록 충돌 거리·품질 강화
    cm.collision_settings.distance_min       = 0.015
    cm.collision_settings.collision_quality  = 4
    cm.collision_settings.use_self_collision = False   # self-collision 비활성 (안정성)

    # ⑨ 프레임별 시뮬레이션
    N = 35
    bpy.context.scene.frame_start = 1
    bpy.context.scene.frame_end   = N
    print(f"[Cloth] 시뮬 {N} frames 시작...")

    for f in range(1, N + 1):
        bpy.context.scene.frame_set(f)
        bpy.context.view_layer.update()
        if f % 10 == 0:
            print(f"[Cloth]   frame {f}/{N}")

    # ⑩ 시뮬 결과를 베이스 메쉬로 교체
    dg = bpy.context.evaluated_depsgraph_get()
    dg.update()
    evaled   = cloth_obj.evaluated_get(dg)
    new_mesh = bpy.data.meshes.new_from_object(evaled)
    old_mesh = cloth_obj.data
    cloth_obj.data = new_mesh
    cloth_obj.modifiers.remove(cloth_obj.modifiers["Cloth"])
    bpy.data.meshes.remove(old_mesh)
    print("[Cloth] 시뮬 적용 완료")

    # ⑩.5  시뮬 후 버텍스 좌표 저장 → displacement 계산
    post_npy = output_path.replace('.glb', '_post.npy')
    post_verts_g = _save_verts_gltf(cloth_obj, post_npy)
    disp_npy = output_path.replace('.glb', '_disp.npy')
    disp = post_verts_g - pre_verts_g
    max_disp = float(abs(disp).max())
    print(f"[Cloth] max displacement: {max_disp:.4f}m")

    # 폭발 감지: 최대 변위가 1.5m 초과 → 시뮬 실패로 간주
    _EXPLODE_THRESH = 1.5
    if max_disp > _EXPLODE_THRESH:
        print(f"[Cloth] ⚠ EXPLOSION: {max_disp:.3f}m > {_EXPLODE_THRESH}m → exit(2)")
        sys.exit(2)

    np.save(disp_npy, disp)
    print(f"[Cloth] vertex data saved: {len(pre_verts_g)} verts")

    # ⑩.6 표면 스무딩(셔츠): 충돌로 생긴 거친 주름 노이즈 완화 → 자연스러운 천 질감
    if cloth_type == 'shirt':
        set_active(cloth_obj)
        sm = cloth_obj.modifiers.new(name="Smooth", type='SMOOTH')
        sm.factor = 0.6
        sm.iterations = 10
        bpy.ops.object.modifier_apply(modifier=sm.name)
        print("[Cloth] 표면 스무딩 적용")

    # ⑩.7 스무스 쉐이딩: 법선 부드럽게 → 천 질감 스무스
    set_active(cloth_obj)
    bpy.ops.object.shade_smooth()

    # ⑪ 의상만 선택 → GLB 내보내기
    bpy.ops.object.select_all(action='DESELECT')
    cloth_obj.select_set(True)
    bpy.context.view_layer.objects.active = cloth_obj

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    bpy.ops.export_scene.gltf(
        filepath=output_path,
        use_selection=True,
        export_format='GLB',
        export_apply=True,
    )
    sz = os.path.getsize(output_path) // 1024
    print(f"[Cloth] ✓ 저장: {output_path} ({sz}KB)")


main()
