import os
from typing import Optional
from pathlib import Path

import bpy

from blender_kitsu.rdpreset import opsdata


class RDPRESET_preferences(bpy.types.PropertyGroup):

    """
    Addon preferences for rdpreset.
    """

    def update_rd_preset_file_model(self, context: bpy.types.Context) -> None:
        opsdata.init_rd_preset_file_model(context)

    presets_dir: bpy.props.StringProperty(  # type: ignore
        name="Render Presets Directory",
        description="Directory path to folder in which render settings python files are stored.",
        default="",
        subtype="DIR_PATH",
        update=update_rd_preset_file_model,
    )

    @property
    def is_presets_dir_valid(self) -> bool:

        # check if file is saved
        if not self.presets_dir:
            return False

        if not bpy.data.filepath and self.presets_dir.startswith("//"):
            return False

        return True

    @property
    def presets_dir_path(self) -> Optional[Path]:
        if not self.presets_dir:
            return None
        return Path(os.path.abspath(bpy.path.abspath(self.presets_dir)))

    def draw(
        self,
        context: bpy.types.Context,
        layout: bpy.types.UILayout,
    ) -> None:

        # rd preset
        box = layout.box()
        box.label(text="General Tools", icon="PREFERENCES")
        box.row().prop(self, "presets_dir")


# ---------REGISTER ----------

classes = [RDPRESET_preferences]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():

    # unregister classes
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
