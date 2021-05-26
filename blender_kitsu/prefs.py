import hashlib
import sys
import os

from typing import Optional
from pathlib import Path

import bpy

from .auth import ZSession
from .logger import ZLoggerFactory

from .ops_auth import (
    KITSU_OT_session_end,
    KITSU_OT_session_start,
)
from .ops_context import KITSU_OT_con_productions_load

from . import cache, ops_anim_data

logger = ZLoggerFactory.getLogger(name=__name__)


class KITSU_addon_preferences(bpy.types.AddonPreferences):
    """
    Addon preferences to kitsu. Holds variables that are important for authentification.
    During runtime new attributes are created that get initialized in: bz_prefs_init_properties()
    """

    def get_datadir(self) -> Path:
        """Returns a Path where persistent application data can be stored.

        # linux: ~/.local/share
        # macOS: ~/Library/Application Support
        # windows: C:/Users/<USER>/AppData/Roaming
        """

        home = Path.home()

        if sys.platform == "win32":
            return home / "AppData/Roaming"
        elif sys.platform == "linux":
            return home / ".local/share"
        elif sys.platform == "darwin":
            return home / "Library/Application Support"

    def get_thumbnails_dir(self) -> str:
        """Generate a path based on get_datadir and the current file name.

        The path is constructed by combining the OS application data dir,
        "blender_kitsu" and a hashed version of the filepath.
        """
        hashed_filepath = hashlib.md5(bpy.data.filepath.encode()).hexdigest()
        storage_dir = self.get_datadir() / "blender_kitsu" / hashed_filepath
        return storage_dir.as_posix()

    def init_playblast_file_model(self, context: bpy.types.Context) -> None:
        ops_anim_data.init_playblast_file_model(context)

    bl_idname = __package__

    host: bpy.props.StringProperty(  # type: ignore
        name="Host", default="", options={"HIDDEN", "SKIP_SAVE"}
    )

    email: bpy.props.StringProperty(  # type: ignore
        name="Email", default="", options={"HIDDEN", "SKIP_SAVE"}
    )

    passwd: bpy.props.StringProperty(  # type: ignore
        name="Password", default="", options={"HIDDEN", "SKIP_SAVE"}, subtype="PASSWORD"
    )

    thumbnail_dir: bpy.props.StringProperty(  # type: ignore
        name="Thumbnail Folder",
        description="Folder in which thumbnails will be saved",
        default="",
        subtype="DIR_PATH",
        get=get_thumbnails_dir,
    )

    playblast_root_dir: bpy.props.StringProperty(  # type: ignore
        name="Playblasts Root Directory",
        description="Directory path to playblast root folder.",
        default="",
        subtype="DIR_PATH",
        update=init_playblast_file_model,
    )

    rd_settings_dir: bpy.props.StringProperty(  # type: ignore
        name="Render Settings Directory",
        description="Directory path to folder in which render settings python files are stored.",
        default="",
        subtype="DIR_PATH",
        # update=init_playblast_file_model,
    )

    project_active_id: bpy.props.StringProperty(  # type: ignore
        name="Project Active ID",
        description="Server Id that refers to the last active project",
        default="",
        options={"HIDDEN", "SKIP_SAVE"},
    )

    enable_debug: bpy.props.BoolProperty(  # type: ignore
        name="Enable Debug Operators",
        description="Enables Operatots that provide debug functionality.",
    )
    show_advanced: bpy.props.BoolProperty(  # type: ignore
        name="Show Advanced Settings",
        description="Show advanced settings that should already have good defaults.",
    )

    shot_pattern: bpy.props.StringProperty(  # type: ignore
        name="Shot Pattern",
        description="Pattern to define how Bulk Init will name the shots. Supported wildcards: <Project>, <Sequence>, <Counter>",
        default="<Sequence>_<Counter>_A",
    )

    shot_counter_digits: bpy.props.IntProperty(  # type: ignore
        name="Shot Counter Digits",
        description="How many digits the counter should contain.",
        default=4,
        min=0,
    )
    shot_counter_increment: bpy.props.IntProperty(  # type: ignore
        name="Shot Counter Increment",
        description="By which Increment counter should be increased.",
        default=10,
        step=5,
        min=0,
    )
    pb_open_webbrowser: bpy.props.BoolProperty(  # type: ignore
        name="Open Webbrowser after Playblast",
        description="Controls if the default webbrowser should be opened to kitsu after playblast creation.",
        default=True,
    )

    session: ZSession = ZSession()

    @property
    def is_rd_settings_dir_valid(self) -> bool:

        # check if file is saved
        if not self.rd_settings_dir:
            return False

        if not bpy.data.filepath and self.rd_settings_dir.startswith("//"):
            return False

        return True

    @property
    def rd_settings_dir_path(self) -> Optional[Path]:
        if not self.rd_settings_dir:
            return None
        return Path(os.path.abspath(bpy.path.abspath(self.rd_settings_dir)))

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        project_active = cache.project_active_get()

        # login
        box = layout.box()
        box.label(text="Login and Host Settings", icon="URL")
        if not self.session.is_auth():
            box.row().prop(self, "host")
            box.row().prop(self, "email")
            box.row().prop(self, "passwd")
            box.row().operator(
                KITSU_OT_session_start.bl_idname, text="Login", icon="PLAY"
            )
        else:
            row = box.row()
            row.prop(self, "host")
            row.enabled = False
            box.row().label(text=f"Logged in: {self.session.email}")
            box.row().operator(
                KITSU_OT_session_end.bl_idname, text="Logout", icon="PANEL_CLOSE"
            )

        # Production
        box = layout.box()
        box.label(text="Project settings", icon="FILEBROWSER")
        row = box.row(align=True)

        if not project_active:
            prod_load_text = "Select Production"
        else:
            prod_load_text = project_active.name

        row.operator(
            KITSU_OT_con_productions_load.bl_idname,
            text=prod_load_text,
            icon="DOWNARROW_HLT",
        )
        # anim tools settings
        box = layout.box()
        box.label(text="Anim Tools", icon="RENDER_ANIMATION")
        box.row().prop(self, "playblast_root_dir")
        box.row().prop(self, "pb_open_webbrowser")

        # general tools settings
        box = layout.box()
        box.label(text="General Tools", icon="PREFERENCES")
        box.row().prop(self, "rd_settings_dir")

        # misc settings
        box = layout.box()
        box.label(text="Misc", icon="MODIFIER")
        box.row().prop(self, "thumbnail_dir")
        box.row().prop(self, "enable_debug")
        box.row().prop(self, "show_advanced")

        if self.show_advanced:
            box.row().prop(self, "shot_pattern")
            box.row().prop(self, "shot_counter_digits")
            box.row().prop(self, "shot_counter_increment")

    @property
    def playblast_root_path(self) -> Optional[Path]:
        if not self.is_playblast_root_valid:
            return None
        return Path(os.path.abspath(bpy.path.abspath(self.playblast_root_dir)))

    @property
    def is_playblast_root_valid(self) -> bool:

        # check if file is saved
        if not self.playblast_root_dir:
            return False

        if not bpy.data.filepath and self.playblast_root_dir.startswith("//"):
            return False

        return True


def zsession_get(context: bpy.types.Context) -> ZSession:
    """
    shortcut to get zsession from blender_kitsu addon preferences
    """
    prefs = context.preferences.addons["blender_kitsu"].preferences
    return prefs.session  # type: ignore


def addon_prefs_get(context: bpy.types.Context) -> bpy.types.AddonPreferences:
    """
    shortcut to get blender_kitsu addon preferences
    """
    return context.preferences.addons["blender_kitsu"].preferences


def zsession_auth(context: bpy.types.Context) -> bool:
    """
    shortcut to check if zession is authorized
    """
    return zsession_get(context).is_auth()


# ---------REGISTER ----------

classes = [KITSU_addon_preferences]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():

    # log user out
    addon_prefs = bpy.context.preferences.addons["blender_kitsu"].preferences
    if addon_prefs.session.is_auth():
        addon_prefs.session.end()

    # unregister classes
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
