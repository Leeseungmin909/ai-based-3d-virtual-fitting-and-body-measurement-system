"""Blender 5.x cloth modifier API 확인용 스크립트"""
import bpy

bpy.ops.mesh.primitive_plane_add()
obj = bpy.context.active_object
bpy.ops.object.modifier_add(type='CLOTH')
cm = bpy.context.active_object.modifiers["Cloth"]

print("=== ClothSettings attrs ===")
for attr in sorted(dir(cm.settings)):
    if not attr.startswith('_'):
        print(f"  cm.settings.{attr}")

print("=== ClothCollisionSettings attrs ===")
for attr in sorted(dir(cm.collision_settings)):
    if not attr.startswith('_'):
        print(f"  cm.collision_settings.{attr}")
