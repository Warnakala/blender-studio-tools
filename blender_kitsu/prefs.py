import hashlib
import sys
from pathlib import Path

import bpy
from bpy import context

from .auth import ZSession
from .logger import ZLoggerFactory
from .ops import (
    KITSU_OT_productions_load,
    KITSU_OT_session_end,
    KITSU_OT_session_start,
)
from . import cache

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

    def get_playblast_dir(self) -> str:
        seq = cache.sequence_active_get()
        shot = cache.shot_active_get()

        if not seq or not shot:
            return ""

        storage_dir = (
            self.get_datadir()
            / "blender_kitsu"
            / "playblasts"
            / seq.name
            / shot.name
            / context.scene.kitsu.playblast_version
        )
        return storage_dir.as_posix()

    def get_playblast_version_dir(self) -> str:
        seq = cache.sequence_active_get()
        shot = cache.shot_active_get()

        if not seq or not shot:
            return ""

        storage_dir = (
            self.get_datadir() / "blender_kitsu" / "playblasts" / seq.name / shot.name
        )
        return storage_dir.as_posix()

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
    category: bpy.props.EnumProperty(  # type: ignore
        items=(
            ("ASSETS", "Assets", "Asset related tasks", "FILE_3D", 0),
            ("SHOTS", "Shots", "Shot related tasks", "FILE_MOVIE", 1),
        ),
        default="SHOTS",
    )
    thumbnail_dir: bpy.props.StringProperty(  # type: ignore
        name="Thumbnail Folder",
        description="Folder in which thumbnails will be saved",
        default="",
        subtype="DIR_PATH",
        get=get_thumbnails_dir,
    )

    playblast_dir: bpy.props.StringProperty(  # type: ignore
        name="Playblasts Folder",
        description="Folder in which playblasts will be saved",
        default="",
        subtype="DIR_PATH",
        get=get_playblast_dir,
    )

    playblast_version_dir: bpy.props.StringProperty(  # type: ignore
        name="Playblasts Version Folder",
        description="Folder in which all playblasts version dirs are found",
        default="",
        subtype="DIR_PATH",
        get=get_playblast_version_dir,
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

    session: ZSession = ZSession()

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
            KITSU_OT_productions_load.bl_idname,
            text=prod_load_text,
            icon="DOWNARROW_HLT",
        )
        # misc settings
        box = layout.box()
        box.label(text="Misc", icon="MODIFIER")
        box.row().prop(self, "thumbnail_dir")
        box.row().prop(self, "playblast_dir")
        box.row().prop(self, "enable_debug")
        box.row().prop(self, "show_advanced")

        if self.show_advanced:
            box.row().prop(self, "shot_pattern")
            box.row().prop(self, "shot_counter_digits")
            box.row().prop(self, "shot_counter_increment")


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
