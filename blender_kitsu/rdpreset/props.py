import bpy


class RDPRESET_property_group_scene(bpy.types.PropertyGroup):
    """"""

    # render settings
    preset_file: bpy.props.StringProperty(  # type: ignore
        name="Render Settings File",
        description="Path to file that is the active render settings preset",
        default="",
        subtype="FILE_PATH",
    )


# ----------------REGISTER--------------

classes = [
    RDPRESET_property_group_scene,
]


def register():

    for cls in classes:
        bpy.utils.register_class(cls)

    # Scene Properties
    bpy.types.Scene.rdpreset = bpy.props.PointerProperty(
        name="Render Preset",
        type=RDPRESET_property_group_scene,
        description="Metadata that is required for rdpreset",
    )


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
