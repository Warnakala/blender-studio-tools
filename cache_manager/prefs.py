import bpy

class CM_AddonPreferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    cachedir: bpy.props.StringProperty(  # type: ignore
        name="cache dir",
        default="//",
        options={"HIDDEN", "SKIP_SAVE"},
        subtype='DIR_PATH'
    )

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        box = layout.box()
        box.row().prop(self, "cachedir")

# ---------REGISTER ----------

classes = [CM_AddonPreferences]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
