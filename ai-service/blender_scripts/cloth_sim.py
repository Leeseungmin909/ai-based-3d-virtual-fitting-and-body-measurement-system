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


def apply_transform(objs, **kw):
    """여러 오브젝트에 동일한 transform_apply 적용"""
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.transform_apply(**kw)


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
    # 원본 GLB의 노드 변환(회전·스케일)을 메쉬에 베이크 → 로컬=월드 좌표 보장
    # (핀 그룹 z 선택이 로컬 좌표 기준이므로 필수)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

    # ③.4 정점 용접 (Merge by Distance): GLB는 UV 경계마다 정점이 분리돼 있어
    # 메쉬가 조각나 있음 → 천 시뮬 시 조각이 따로 날아가 폭발.
    # UV는 루프에 저장되므로 용접해도 보존됨. (구 pymeshlab 경로의 merge_close_vertices 대응)
    n_before = len(cloth_obj.data.vertices)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.remove_doubles(threshold=0.0001)
    bpy.ops.object.mode_set(mode='OBJECT')
    print(f"[Cloth] 정점 용접: {n_before} -> {len(cloth_obj.data.vertices)} verts")

    # ③.5 Blender 내부 데시메이션 → 시뮬 프록시.
    # 원본(hi-res, 지오메트리 조각 질감)은 ClothHi로 보존, Surface Deform으로 프록시를 따라감.
    _SIM_FACES = 50000
    n_faces = len(cloth_obj.data.polygons)
    hi_obj = None
    if n_faces > _SIM_FACES:
        set_active(cloth_obj)
        bpy.ops.object.duplicate()
        hi_obj = bpy.context.active_object
        hi_obj.name = "ClothHi"
        set_active(cloth_obj)
        dec = cloth_obj.modifiers.new(name="Decimate", type='DECIMATE')
        dec.ratio = _SIM_FACES / n_faces
        bpy.ops.object.modifier_apply(modifier=dec.name)
        print(f"[Cloth] Blender decimate: {n_faces} -> {len(cloth_obj.data.polygons)} faces (프록시, hi-res 보존)")

    # 프록시 + hi-res 동시 변환 대상 (스케일·위치가 둘 다 같아야 Surface Deform 정확)
    _both = [cloth_obj] + ([hi_obj] if hi_obj else [])

    # ④ 단위 감지 (cm → m)
    cx0, cx1, cy0, cy1, cz0, cz1 = get_bbox(cloth_obj)
    max_dim = max(cx1-cx0, cy1-cy0, cz1-cz0)
    if max_dim > 3.0:
        for _o in _both:
            _o.scale = (0.01, 0.01, 0.01)
        apply_transform(_both, scale=True)
        cx0, cx1, cy0, cy1, cz0, cz1 = get_bbox(cloth_obj)
        print("[Cloth] cm→m 변환 완료")

    cloth_depth = cy1 - cy0
    cx_ctr = (cx0 + cx1) / 2
    cy_ctr = (cy0 + cy1) / 2
    print(f"[Cloth] Cloth: h={cz1-cz0:.3f}m  depth={cloth_depth:.3f}m  faces={len(cloth_obj.data.polygons)}")

    # ④.5  원본 프록시 버텍스 월드 좌표 저장 (변형 전달용)
    import numpy as np
    def _save_verts_gltf(obj, path):
        """Blender 월드 좌표(Z-up) → GLTF(Y-up): (X,Y,Z)_B → (X,Z,-Y)_G"""
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
        for _o in _both:
            _o.scale.y = scale_y
        apply_transform(_both, scale=True)
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
        for _o in _both:
            _o.scale.x = scale_x
        apply_transform(_both, scale=True)
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
        _loc = (-cx_ctr, -cy_ctr, collar_z - cz1)
    else:
        # 하의 상단(waistband): SMPL-X y_max 사용, 없으면 58% fallback
        if _sm.get('y_max'):
            waist_z = bz0 + _sm['y_max']
        else:
            waist_z = bz0 + body_h * 0.58
        _loc = (-cx_ctr, -cy_ctr, waist_z - cz1)

    for _o in _both:
        _o.location = _loc
    apply_transform(_both, location=True)
    print("[Cloth] 위치 정렬 완료")

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

    # ⑦.5 hi-res 추종 준비: 시뮬 전 프록시(rest 상태) 메쉬를 복사해 둠.
    # 시뮬 후 barycentric 전달로 hi-res가 프록시 변형을 따라감.
    # (Surface Deform은 비매니폴드 메쉬에서 바인딩 거부 → BVH 방식은 무관)
    pre_mesh_copy = None
    if hi_obj:
        pre_mesh_copy = cloth_obj.data.copy()
        print(f"[Cloth] hi-res 추종 준비: 프록시 rest 메쉬 복사 ({len(pre_mesh_copy.vertices)} verts)")

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

    # ⑩.55 hi-res barycentric 전달 (폭발 검사 통과 후):
    # 각 hi-res 정점 → rest 프록시의 최근접 삼각형 → 시뮬 후 같은 삼각형 위치로 변환.
    # 시뮬은 토폴로지를 바꾸지 않으므로 정점 순서로 pre/post 삼각형이 1:1 대응.
    if hi_obj and pre_mesh_copy:
        from mathutils.bvhtree import BVHTree
        from mathutils.geometry import barycentric_transform
        pre_mesh_copy.calc_loop_triangles()
        tri_table = [lt.vertices[:] for lt in pre_mesh_copy.loop_triangles]
        verts_pre = [v.co.copy() for v in pre_mesh_copy.vertices]
        bvh = BVHTree.FromPolygons([tuple(v) for v in verts_pre], tri_table)
        verts_post = cloth_obj.data.vertices
        # 원본 정점 위치·법선 스냅샷 (이동 중 법선 재계산 오염 방지)
        hi_verts = hi_obj.data.vertices
        hi_cos = [v.co.copy() for v in hi_verts]
        hi_nos = [v.normal.copy() for v in hi_verts]
        _R = 0.015   # 후보 탐색 반경: 안/겉감 간격보다 크고 소매-몸통 간격보다 작게
        n_fail = 0
        for i, v in enumerate(hi_verts):
            co, vn = hi_cos[i], hi_nos[i]
            # 법선이 같은 방향인 삼각형만 후보 (안감/겉감·접힌 맞은편 혼입 방지 → 소매 슬릿 제거)
            fidx = None
            for rad in (_R, _R * 3):   # 실패 시 반경 확장 재시도 (무조건 최근접 폴백은 혼선 재유입)
                best_d = None
                for (_loc, fno, fi, dist) in bvh.find_nearest_range(co, rad):
                    if fno.dot(vn) < 0.3:   # 비스듬한 혼선(접힌 면 맞은편)까지 차단
                        continue
                    if best_d is None or dist < best_d:
                        fidx, best_d = fi, dist
                if fidx is not None:
                    break
            if fidx is None:
                _loc, _n, fidx, _d = bvh.find_nearest(co)
                if fidx is None:
                    n_fail += 1
                    continue
            ia, ib, ic = tri_table[fidx]
            v.co = barycentric_transform(
                co,
                verts_pre[ia], verts_pre[ib], verts_pre[ic],
                verts_post[ia].co, verts_post[ib].co, verts_post[ic].co)
        bpy.data.meshes.remove(pre_mesh_copy)
        print(f"[Cloth] hi-res barycentric 전달(법선 매칭): {len(hi_verts)} verts (실패 {n_fail})")

        # 변위 스무딩: 인접 정점이 서로 다른 삼각형에 매핑되며 생기는 불연속(소매 슬릿) 제거.
        # 조각 질감은 원본 좌표에 있으므로 변위만 스무딩하면 디테일은 유지됨.
        n_hi = len(hi_verts)
        orig = np.array([(c.x, c.y, c.z) for c in hi_cos], dtype=np.float32)
        moved = np.empty(n_hi * 3, dtype=np.float32)
        hi_obj.data.vertices.foreach_get("co", moved)
        disp_hi = moved.reshape(n_hi, 3) - orig
        edges = np.empty(len(hi_obj.data.edges) * 2, dtype=np.int32)
        hi_obj.data.edges.foreach_get("vertices", edges)
        e0, e1 = edges.reshape(-1, 2)[:, 0], edges.reshape(-1, 2)[:, 1]
        deg = np.zeros(n_hi, dtype=np.float32)
        np.add.at(deg, e0, 1.0)
        np.add.at(deg, e1, 1.0)
        deg[deg == 0] = 1.0
        _SMOOTH_ITERS = 30
        for _ in range(_SMOOTH_ITERS):
            acc = np.zeros_like(disp_hi)
            np.add.at(acc, e0, disp_hi[e1])
            np.add.at(acc, e1, disp_hi[e0])
            disp_hi = 0.5 * disp_hi + 0.5 * (acc / deg[:, None])
        hi_obj.data.vertices.foreach_set("co", (orig + disp_hi).ravel())
        hi_obj.data.update()
        print(f"[Cloth] hi-res 변위 스무딩 완료 ({_SMOOTH_ITERS}회)")

    # ⑩.6 표면 스무딩(셔츠 프록시 전용): hi-res는 조각 질감 보존을 위해 스무딩 생략
    if cloth_type == 'shirt' and not hi_obj:
        set_active(cloth_obj)
        sm = cloth_obj.modifiers.new(name="Smooth", type='SMOOTH')
        sm.factor = 0.6
        sm.iterations = 10
        bpy.ops.object.modifier_apply(modifier=sm.name)
        print("[Cloth] 표면 스무딩 적용")

    # 최종 출력 오브젝트: hi-res가 있으면 hi-res, 없으면 프록시
    export_obj = hi_obj if hi_obj else cloth_obj

    # ⑩.7 스무스 쉐이딩: 법선 부드럽게 → 천 질감 스무스
    set_active(export_obj)
    bpy.ops.object.shade_smooth()

    # ⑪ 의상만 선택 → GLB 내보내기
    bpy.ops.object.select_all(action='DESELECT')
    export_obj.select_set(True)
    bpy.context.view_layer.objects.active = export_obj

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
