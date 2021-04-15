from pathlib import Path

import bpy


class CM_AddonPreferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    cachedir: bpy.props.StringProperty(  # type: ignore
        name="cache dir",
        default="//cache",
        options={"HIDDEN", "SKIP_SAVE"},
        subtype="DIR_PATH",
    )

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        box = layout.box()
        box.row().prop(self, "cachedir")

    @property
    def cachedir_path(self) -> Path:
        return Path(bpy.path.abspath(self.cachedir)).absolute()

    @property
    def is_cachedir_valid(self) -> bool:

        # check if file is saved
        if not self.cachedir:
            return False

        if not bpy.data.filepath and self.cachedir.startswith("//"):
            return False

        return True


def addon_prefs_get(context: bpy.types.Context) -> bpy.types.AddonPreferences:
    """
    shortcut to get cache_manager addon preferences
    """
    return context.preferences.addons["cache_manager"].preferences


# ---------REGISTER ----------

classes = [CM_AddonPreferences]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
