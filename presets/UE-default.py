import bpy

prefs = bpy.context.preferences.addons['collider_tools'].preferences

prefs.naming_position = 'PREFIX'
prefs.replace_name = False
prefs.obj_basename = 'geo'
prefs.separator = '_'
prefs.collision_string_prefix = ''
prefs.collision_string_suffix = ''
prefs.box_shape = 'UBX'
prefs.sphere_shape = 'USP'
prefs.convex_shape = 'UCX'
prefs.mesh_shape = ''
prefs.collider_groups_enabled = True
prefs.user_group_01 = ''
prefs.user_group_02 = ''
prefs.user_group_03 = 'Complex'
prefs.user_group_01_name = 'Simple'
prefs.user_group_02_name = 'Simple 2'
prefs.user_group_03_name = 'Complex'
prefs.physics_material_name = 'MI_COL'
prefs.physics_material_filter = 'COL'

