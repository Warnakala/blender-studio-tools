from typing import List, Any, Generator, Optional

import bpy


class CM_property_group_scene(bpy.types.PropertyGroup):

    layout_cut_in: bpy.props.IntProperty(
        name="Layout Cut In",
        description="Frame where the camera marker is set for the shot, in the layout file",
        default=0,
        step=1,
    )


# ---------REGISTER ----------.

classes: List[Any] = [
    CM_property_group_scene,
]


def register():

    for cls in classes:
        bpy.utils.register_class(cls)

    # Scene Properties.
    bpy.types.Scene.anim_setup = bpy.props.PointerProperty(type=CM_property_group_scene)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
