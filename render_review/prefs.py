import os
import bpy
from pathlib import Path
from typing import Optional, Dict, List, Set, Any

import bpy


def addon_prefs_get(context: bpy.types.Context) -> bpy.types.AddonPreferences:
    """
    shortcut to get addon preferences
    """
    return context.preferences.addons["render_review"].preferences


def is_blender_kitsu_enabled() -> bool:
    return "blender_kitsu" in bpy.context.preferences.addons


class RR_OT_enable_blender_kitsu(bpy.types.Operator):
    """"""

    bl_idname = "rr.enable_blender_kitsu"
    bl_label = "Enable Blender Kitsu"
    bl_description = ""
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context: bpy.types.Context) -> Set[str]:
        addon_prefs = addon_prefs_get(context)

        # enable_blender_kitsu checkbox is off -> user wants to enable it
        if not addon_prefs.enable_blender_kitsu:
            if not is_blender_kitsu_enabled():
                self.report({"ERROR"}, "blender_kitsu is not enabled or installed")
                return {"CANCELLED"}

            addon_prefs.enable_blender_kitsu = True
            return {"FINISHED"}

        # disable blender_kitsu, checkbox is on
        else:
            addon_prefs.enable_blender_kitsu = False
            return {"FINISHED"}


class RR_AddonPreferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    def _get_contachseet_dir(self: Any) -> str:
        # get it based on edit_storage_path
        # edit_storage_path: /home/guest/Blender Dropbox/render/sprites
        if not self.edit_storage_path:
            return ""
        return (
            self.edit_storage_path.parents[2]
            .joinpath("shared/sprites/contactsheets")
            .as_posix()
        )

    def _check_blender_kitsu_installed(self, value):
        if not is_blender_kitsu_enabled():
            raise RuntimeError("blender_kitsu addon ist not enabled")

    farm_output_dir: bpy.props.StringProperty(  # type: ignore
        name="Farm Output Directory",
        description="Should point to: /render/sprites/farm_output",
        default="/render/sprites/farm_output",
        subtype="DIR_PATH",
    )

    frame_storage_dir: bpy.props.StringProperty(  # type: ignore
        name="Frame Storage Directory",
        description="Should point to: /render/sprites/frame_storage",
        default="/render/sprites/frame_storage",
        subtype="DIR_PATH",
    )

    edit_storage_dir: bpy.props.StringProperty(  # type: ignore
        name="Edit Storage Directory",
        description="Should point to: /home/guest/Blender Dropbox/render/sprites",
        default="/home/guest/Blender Dropbox/render/sprites",
        subtype="DIR_PATH",
    )

    contactsheet_dir: bpy.props.StringProperty(  # type: ignore
        name="Contactsheet Directory",
        description="Should point to: /home/guest/Blender Dropbox/shared/sprites/contactsheet",
        subtype="DIR_PATH",
        get=_get_contachseet_dir,
    )
    enable_blender_kitsu: bpy.props.BoolProperty(
        name="Enable Blender Kitsu",
        description="This checkbox controls if render_review should try to use the blender_kitsu addon to extend its feature sets.",
        # set=_check_blender_kitsu_installed,
        default=False,
    )

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        box = layout.box()
        box.label(text="Filepaths", icon="FILEBROWSER")

        # farm outpur dir
        box.row().prop(self, "farm_output_dir")

        if not self.farm_output_dir:
            row = box.row()
            row.label(text="Please specify the Farm Output Directory", icon="ERROR")

        if not bpy.data.filepath and self.farm_output_dir.startswith("//"):
            row = box.row()
            row.label(
                text="In order to use a relative path the current file needs to be saved.",
                icon="ERROR",
            )

        # frame storage dir
        box.row().prop(self, "frame_storage_dir")

        if not self.frame_storage_dir:
            row = box.row()
            row.label(text="Please specify the Frame Storage Directory", icon="ERROR")

        if not bpy.data.filepath and self.frame_storage_dir.startswith("//"):
            row = box.row()
            row.label(
                text="In order to use a relative path the current file needs to be saved.",
                icon="ERROR",
            )

        # edit storage dir
        box.row().prop(self, "edit_storage_dir")

        if not self.edit_storage_dir:
            row = box.row()
            row.label(text="Please specify the Edit Storage Directory", icon="ERROR")

        if not bpy.data.filepath and self.edit_storage_dir.startswith("//"):
            row = box.row()
            row.label(
                text="In order to use a relative path the current file needs to be saved.",
                icon="ERROR",
            )
        # contactsheet dir
        box.row().prop(self, "contactsheet_dir")

        # enable blender kitsu
        icon = "CHECKBOX_DEHLT"
        label_text = "Enable Blender Kitsu"

        if self.enable_blender_kitsu:
            icon = "CHECKBOX_HLT"

        row = box.row(align=True)
        row.operator(
            RR_OT_enable_blender_kitsu.bl_idname, icon=icon, text="", emboss=False
        )
        row.label(text=label_text)

        # box.row().prop(self, "enable_blender_kitsu")

    @property
    def frame_storage_path(self) -> Optional[Path]:
        if not self.is_frame_storage_valid:
            return None
        return Path(os.path.abspath(bpy.path.abspath(self.frame_storage_dir)))

    @property
    def is_frame_storage_valid(self) -> bool:

        # check if file is saved
        if not self.frame_storage_dir:
            return False

        if not bpy.data.filepath and self.frame_storage_dir.startswith("//"):
            return False

        return True

    @property
    def farm_output_path(self) -> Optional[Path]:
        if not self.is_farm_output_valid:
            return None
        return Path(os.path.abspath(bpy.path.abspath(self.farm_output_dir)))

    @property
    def is_farm_output_valid(self) -> bool:

        # check if file is saved
        if not self.farm_output_dir:
            return False

        if not bpy.data.filepath and self.farm_output_dir.startswith("//"):
            return False

        return True

    @property
    def edit_storage_path(self) -> Optional[Path]:
        if not self.is_edit_storage_valid:
            return None
        return Path(os.path.abspath(bpy.path.abspath(self.edit_storage_dir)))

    @property
    def is_edit_storage_valid(self) -> bool:

        # check if file is saved
        if not self.edit_storage_dir:
            return False

        if not bpy.data.filepath and self.edit_storage_dir.startswith("//"):
            return False

        return True


# ---------REGISTER ----------

classes = [RR_OT_enable_blender_kitsu, RR_AddonPreferences]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
