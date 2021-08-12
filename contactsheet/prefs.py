import os
import bpy
from pathlib import Path
from typing import Optional, Dict, List, Set, Any

import bpy


def addon_prefs_get(context: bpy.types.Context) -> bpy.types.AddonPreferences:
    """
    shortcut to get addon preferences
    """
    return context.preferences.addons["contactsheet"].preferences


class RR_AddonPreferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    contactsheet_dir: bpy.props.StringProperty(  # type: ignore
        name="Contactsheet Directory",
        description="Should point to: /shared/sprites/contactsheet",
        default="",
        subtype="DIR_PATH",
    )

    contactsheet_scale_factor: bpy.props.FloatProperty(
        name="Contactsheet Scale Factor",
        description="This value controls how much space there is between the individual cells of the contactsheet",
        min=0.1,
        max=1.0,
        step=5,
        default=0.9,
    )

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        box = layout.box()
        box.label(text="Filepaths", icon="FILEBROWSER")

        # contactsheet settings
        box.row().prop(self, "contactsheet_dir")
        box.row().prop(self, "contactsheet_scale_factor")

    @property
    def contactsheet_dir_path(self) -> Optional[Path]:
        if not self.is_contactsheet_dir_valid:
            return None
        return Path(os.path.abspath(bpy.path.abspath(self.contactsheet_dir)))

    @property
    def is_contactsheet_dir_valid(self) -> bool:

        # check if file is saved
        if not self.contactsheet_dir:
            return False

        if not bpy.data.filepath and self.contactsheet_dir.startswith("//"):
            return False

        return True


# ---------REGISTER ----------

classes = [RR_AddonPreferences]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
