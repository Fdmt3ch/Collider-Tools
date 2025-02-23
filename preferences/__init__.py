import bpy

from . import naming_preset
from . import preferences
from . import properties
from . import keymap
from .properties import ColliderTools_Properties
from .preferences import update_panel_category


classes = (
    properties.ColliderTools_Properties,
    naming_preset.COLLISION_preset,
    preferences.BUTTON_OT_change_key,
    preferences.CollisionAddonPrefs,
    keymap.REMOVE_OT_hotkey,
)


def register():
    from bpy.utils import register_class

    for cls in classes:
        register_class(cls)

    update_panel_category(None, bpy.context)

    # Pointer Properties have to be initialized after classes
    scene = bpy.types.Scene
    scene.collider_tools = bpy.props.PointerProperty(
        type=ColliderTools_Properties)

    keymap.add_keymap()


def unregister():
    from bpy.utils import unregister_class

    for cls in reversed(classes):
        unregister_class(cls)

    scene = bpy.types.Scene
    del scene.collider_tools

    keymap.remove_keymap()
