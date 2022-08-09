import bpy
import os
import subprocess
import textwrap

visibility_operators = {
    'ALL_COLLIDER': 'Colliders',
    'OBJECTS': "Non Colliders",
    'SIMPLE_COMPLEX': 'Simple and Complex',
    'SIMPLE': 'Simple',
    'COMPLEX': 'Complex',
}


def collider_presets_folder():
    # Make sure there is a directory for presets
    collider_presets = "collider_tools"
    collider_preset_directory = os.path.join(bpy.utils.user_resource('SCRIPTS'), "presets", collider_presets)
    collider_preset_paths = bpy.utils.preset_paths(collider_presets)

    if (collider_preset_directory not in collider_preset_paths):
        if (not os.path.exists(collider_preset_directory)):
            os.makedirs(collider_preset_directory)

    return collider_preset_directory


def label_multiline(context, text, parent):
    chars = int(context.region.width / 7)  # 7 pix on 1 character
    wrapper = textwrap.TextWrapper(width=chars)
    text_lines = wrapper.wrap(text=text)
    for text_line in text_lines:
        parent.label(text=text_line)


class EXPLORER_OT_open_folder(bpy.types.Operator):
    """Open render output directory in Explorer"""
    bl_idname = "explorer.open_in_explorer"
    bl_label = "Open Folder"
    bl_description = "Open folder in explorer"

    dirpath: bpy.props.StringProperty()

    def execute(self, context):

        if os.path.isdir(self.dirpath):
            subprocess.Popen(["explorer.exe", self.dirpath])
        else:
            self.report({'ERROR'}, 'Invalid Preset Path')
            return {'CANCELLED'}

        return {'FINISHED'}


class PREFERENCES_OT_open_addon(bpy.types.Operator):
    """Tooltip"""
    bl_idname = "preferences.addon_search"
    bl_label = "Open Addon preferences"

    addon_name: bpy.props.StringProperty()
    prefs_tabs: bpy.props.StringProperty()

    def execute(self, context):

        bpy.ops.screen.userpref_show()

        bpy.context.preferences.active_section = 'ADDONS'
        bpy.data.window_managers["WinMan"].addon_search = self.addon_name

        prefs = context.preferences.addons[__package__.split('.')[0]].preferences
        prefs.prefs_tabs = self.prefs_tabs


        import addon_utils
        mod = addon_utils.addons_fake_modules.get('collider_tools')

        #mod is None the first time the operation is called :/
        if mod:
            mod.bl_info['show_expanded'] = True

            # Find User Preferences area and redraw it
            for window in bpy.context.window_manager.windows:
                for area in window.screen.areas:
                    if area.type == 'USER_PREFERENCES':
                        area.tag_redraw()

        # bpy.ops.preferences.addon_expand(module=self.addon_name)
        return {'FINISHED'}


def draw_visibility_selection_menu(layout):
    split_left = layout.split(factor=0.35)
    col_01 = split_left.column(align=True)
    col_02 = split_left.column(align=True)

    show_icon = 'HIDE_OFF'
    hide_icon = 'HIDE_ON'
    show_text = ''
    hide_text = ''

    select_icon = 'NONE'
    deselect_icon = 'NONE'
    select_text = 'Select'
    deselect_text = 'Deselect'

    delete_icon = 'TRASH'
    delete_text = ''

    row = col_01.row(align=True)
    row.label(text=visibility_operators['ALL_COLLIDER'])

    row = col_02.row(align=True)
    op = row.operator("object.all_show_collisions", icon=show_icon, text=show_text)
    op.hide = False
    op.mode = 'ALL_COLLIDER'
    op = row.operator("object.all_hide_collisions", icon=hide_icon, text=hide_text)
    op.hide = True
    op.mode = 'ALL_COLLIDER'
    op = row.operator("object.all_select_collisions", icon=select_icon, text=select_text)
    op.select = True
    op.mode = 'ALL_COLLIDER'
    op = row.operator("object.all_deselect_collisions", icon=deselect_icon, text=deselect_text)
    op.select = False
    op.mode = 'ALL_COLLIDER'
    op = row.operator("object.all_delete_collisions", icon=delete_icon, text=delete_text)
    op.mode = 'ALL_COLLIDER'

    row = col_01.row(align=True)
    row.label(text=visibility_operators['OBJECTS'])
    row = col_02.row(align=True)
    op = row.operator("object.non_collider_show_collisions", icon=show_icon, text=show_text)
    op.hide = False
    op.mode = 'OBJECTS'
    op = row.operator("object.non_collider_hide_collisions", icon=hide_icon, text=hide_text)
    op.hide = True
    op.mode = 'OBJECTS'
    op = row.operator("object.non_collider_select_collisions", icon=select_icon, text=select_text)
    op.select = True
    op.mode = 'OBJECTS'
    op = row.operator("object.non_collider_deselect_collisions", icon=deselect_icon, text=deselect_text)
    op.select = False
    op.mode = 'OBJECTS'
    op = row.operator("object.non_collider_delete_collisions", icon=delete_icon, text=delete_text)
    op.mode = 'OBJECTS'

    prefs = bpy.context.preferences.addons[__package__.split('.')[0]].preferences
    # row = layout.row(align=True)
    # row.prop(prefs, 'useCustomColGroups')

    if prefs.useCustomColGroups:
        box = layout.box()

        split_left = box.split(factor=0.35)
        col_01 = split_left.column(align=True)
        col_02 = split_left.column(align=True)

        row = col_01.row(align=True)
        row.label(text=visibility_operators['SIMPLE_COMPLEX'])
        row = col_02.row(align=True)
        op = row.operator("object.simple_complex_show_collisions", icon=show_icon, text=show_text)
        op.hide = False
        op.mode = 'SIMPLE_COMPLEX'
        op = row.operator("object.simple_complex_hide_collisions", icon=hide_icon, text=hide_text)
        op.hide = True
        op.mode = 'SIMPLE_COMPLEX'
        op = row.operator("object.simple_complex_select_collisions", icon=select_icon, text=select_text)
        op.select = True
        op.mode = 'SIMPLE_COMPLEX'
        op = row.operator("object.simple_complex_deselect_collisions", icon=deselect_icon, text=deselect_text)
        op.select = False
        op.mode = 'SIMPLE_COMPLEX'
        op = row.operator("object.simple_complex_delete_collisions", icon=delete_icon, text=delete_text)
        op.mode = 'SIMPLE_COMPLEX'

        row = col_01.row(align=True)
        row.label(text=visibility_operators['SIMPLE'])

        row = col_02.row(align=True)
        op = row.operator("object.simple_show_collisions", icon=show_icon, text=show_text)
        op.hide = False
        op.mode = 'SIMPLE'
        op = row.operator("object.simple_hide_collisions", icon=hide_icon, text=hide_text)
        op.hide = True
        op.mode = 'SIMPLE'
        op = row.operator("object.simple_select_collisions", icon=select_icon, text=select_text)
        op.select = True
        op.mode = 'SIMPLE'
        op = row.operator("object.simple_deselect_collisions", icon=deselect_icon, text=deselect_text)
        op.select = False
        op.mode = 'SIMPLE'
        op = row.operator("object.simple_delete_collisions", icon=delete_icon, text=delete_text)
        op.mode = 'SIMPLE'

        row = col_01.row(align=True)
        row.label(text=visibility_operators['COMPLEX'])
        row = col_02.row(align=True)
        op = row.operator("object.complex_show_collisions", icon=show_icon, text=show_text)
        op.hide = False
        op.mode = 'COMPLEX'
        op = row.operator("object.complex_hide_collisions", icon=hide_icon, text=hide_text)
        op.hide = True
        op.mode = 'COMPLEX'
        op = row.operator("object.complex_select_collisions", icon=select_icon, text=select_text)
        op.select = True
        op.mode = 'COMPLEX'
        op = row.operator("object.complex_deselect_collisions", icon=deselect_icon, text=deselect_text)
        op.select = False
        op.mode = 'COMPLEX'
        op = row.operator("object.simple_delete_collisions", icon=delete_icon, text=delete_text)
        op.mode = 'COMPLEX'


class VIEW3D_PT_collission(bpy.types.Panel):
    """Creates a Panel in the Object properties window"""

    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Collider Tools"


class VIEW3D_PT_collission_panel(VIEW3D_PT_collission):
    """Creates a Panel in the Object properties window"""

    bl_label = "Collider Tools"

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        # Naming presets
        from ..preferences.naming_preset import OBJECT_MT_collision_presets
        row = layout.row(align=True)
        row.menu(OBJECT_MT_collision_presets.__name__, text=OBJECT_MT_collision_presets.bl_label)

        # Edit Naming
        from .. import bl_info
        addon_name = bl_info["name"]

        op = row.operator("preferences.addon_search", text="", icon='SETTINGS')
        op.addon_name = addon_name
        op.prefs_tabs = 'NAMING'

        op = row.operator("explorer.open_in_explorer", text="", icon='FILE_FOLDER')
        op.dirpath = collider_presets_folder()

        # Create Collider
        row = layout.row(align=True)
        row.label(text='Add Collider Shape')

        col = self.layout.column(align=True)
        row = col.row(align=True)
        row.operator("mesh.add_bounding_box", icon='MESH_CUBE')
        row = col.row(align=True)
        row.operator("mesh.add_bounding_cylinder", icon='MESH_CYLINDER')
        row = col.row(align=True)
        row.operator("mesh.add_bounding_convex_hull", icon='MESH_ICOSPHERE')
        row = col.row(align=True)
        row.operator("mesh.add_bounding_sphere", icon='MESH_UVSPHERE')
        row = col.row(align=True)
        row.operator("mesh.add_mesh_collision", icon='MESH_MONKEY')

        layout.separator()
        row = layout.row(align=True)
        row.operator("mesh.add_minimum_bounding_box", icon='MESH_CUBE')

        # special Collider Creation
        # layout.separator()
        row = layout.row(align=True)
        row.label(text='Add Complex Collider')

        # Auto Convex
        box = layout.box()
        col = box.column(align=True)
        row = col.row(align=True)
        row.prop(scene, 'convex_decomp_depth')
        row.prop(scene, 'maxNumVerticesPerCH')

        prefs = context.preferences.addons[__package__.split('.')[0]].preferences
        row = col.row(align=True)

        if prefs.executable_path:
            row.operator("collision.vhacd", text="Auto Convex", icon='MESH_ICOSPHERE')
        else:
            from .. import bl_info
            op = row.operator("preferences.addon_search", text="Install V-HACD", icon='ERROR')
            op.addon_name = bl_info["name"]
            op.prefs_tabs = 'VHACD'

        # Conversion
        # layout.separator()
        row = layout.row(align=True)
        row.label(text='Convert')

        col = layout.column(align=True)
        row = col.row(align=True)
        row.operator('object.convert_to_collider', icon='PHYSICS')
        row = col.row(align=True)
        row.operator('object.convert_to_mesh', icon='MESH_MONKEY')


class VIEW3D_PT_collission_visibility_panel(VIEW3D_PT_collission):
    """Creates a Panel in the Object properties window"""

    bl_label = "Visibility, Selection, Deletion"

    def draw(self, context):
        layout = self.layout
        draw_visibility_selection_menu(layout)


class VIEW3D_PT_collission_material_panel(VIEW3D_PT_collission):
    """Creates a Panel in the Object properties window"""

    bl_label = "Physics Materials"

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        row = layout.row()
        row.operator('material.create_physics_material', icon='PLUS', text="Add Physics Material")

        col = layout.column(align=True)
        row = col.row()
        row.template_list("MATERIAL_UL_physics_materials", "", bpy.data, "materials", scene, "asset_list_index")




class VIEW3D_PT_collission_settings_panel(VIEW3D_PT_collission):
    """Creates a Panel in the Object properties window"""

    bl_label = "Collider Settings"

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        # Choose Naming Preset
        row = layout.row(align=True)
        row.label(text='Naming')

        row = layout.row(align=True)
        row.label(text='Creation Settings')
        row = layout.row(align=True)
        row.prop(scene, "my_hide")

        col = layout.column(align=True)
        row = col.row(align=True)
        row.prop(scene, "my_collision_shading_view")
        row = col.row(align=True)
        row.prop(scene, "my_space")
        row = col.row(align=True)
        row.prop(scene, "wireframe_mode")
        row = col.row(align=True)
        row.prop(scene, "creation_mode")
