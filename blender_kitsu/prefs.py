import hashlib
import sys
import os

from typing import Optional
from pathlib import Path

import bpy

from blender_kitsu import cache

# TODO: restructure this to not acess ops_anim_data
from blender_kitsu.anim import opsdata as ops_anim_data
from blender_kitsu.types import Session
from blender_kitsu.logger import LoggerFactory
from blender_kitsu.auth.ops import (
    KITSU_OT_session_end,
    KITSU_OT_session_start,
)
from blender_kitsu.context.ops import KITSU_OT_con_productions_load
from blender_kitsu.rdpreset.prefs import RDPRESET_preferences


logger = LoggerFactory.getLogger(name=__name__)


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

    def get_sqe_render_dir(self) -> str:
        hashed_filepath = hashlib.md5(bpy.data.filepath.encode()).hexdigest()
        storage_dir = (
            self.get_datadir() / "blender_kitsu" / "sqe_render" / hashed_filepath
        )
        return storage_dir.absolute().as_posix()

    def get_config_dir(self) -> str:
        if not self.is_project_root_valid:
            return ""
        return self.project_root_path.joinpath("pipeline/blender_kitsu").as_posix()

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
        name="Thumbnail Directory",
        description="Directory in which thumbnails will be saved",
        default="",
        subtype="DIR_PATH",
        get=get_thumbnails_dir,
    )

    sqe_render_dir: bpy.props.StringProperty(  # type: ignore
        name="Sequence Editor Render Directory",
        description="Directory in which thumbnails will be saved",
        default="",
        subtype="DIR_PATH",
        get=get_sqe_render_dir,
    )

    rdpreset: bpy.props.PointerProperty(  # type: ignore
        name="Render Preset",
        type=RDPRESET_preferences,
        description="Metadata that is required for rdpreset",
    )

    playblast_root_dir: bpy.props.StringProperty(  # type: ignore
        name="Playblasts Root Directory",
        description="Directory path to playblast root folder.",
        default="",
        subtype="DIR_PATH",
        update=init_playblast_file_model,
    )

    project_root_dir: bpy.props.StringProperty(  # type: ignore
        name="Project Root Directory",
        description=(
            "Directory path to the root of the project."
            "In this directory blender kitsu searches for ./pipeline/blender_kitsu"
            "folder to configure the addon per project"
        ),
        default="",
        subtype="DIR_PATH",
        # update=,
    )
    config_dir: bpy.props.StringProperty(  # type: ignore
        name="Config Directory",
        description=(
            "Configuration directory of blender_kitsu."
            "See readme.md how you can configurate the addon on a per project basis"
        ),
        default="",
        subtype="DIR_PATH",
        get=get_config_dir,
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

    session: Session = Session()

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
        box.row().prop(self, "project_root_dir")
        box.row().prop(self, "config_dir")

        # anim tools settings
        box = layout.box()
        box.label(text="Anim Tools", icon="RENDER_ANIMATION")
        box.row().prop(self, "playblast_root_dir")
        box.row().prop(self, "pb_open_webbrowser")

        # rd preset tools settings
        self.rdpreset.draw(context, layout)

        # misc settings
        box = layout.box()
        box.label(text="Misc", icon="MODIFIER")
        box.row().prop(self, "thumbnail_dir")
        box.row().prop(self, "sqe_render_dir")
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

    @property
    def project_root_path(self) -> Optional[Path]:
        if not self.project_root_dir:
            return None
        return Path(os.path.abspath(bpy.path.abspath(self.project_root_dir)))

    @property
    def is_project_root_valid(self) -> bool:

        # check if file is saved
        if not self.project_root_dir:
            return False

        if not bpy.data.filepath and self.project_root_dir.startswith("//"):
            return False

        return True

    @property
    def is_config_dir_valid(self) -> bool:

        # check if file is saved
        if not self.config_dir:
            return False

        if not bpy.data.filepath and self.config_dir.startswith("//"):
            return False

        return True


def session_get(context: bpy.types.Context) -> Session:
    """
    shortcut to get session from blender_kitsu addon preferences
    """
    prefs = context.preferences.addons["blender_kitsu"].preferences
    return prefs.session  # type: ignore


def addon_prefs_get(context: bpy.types.Context) -> bpy.types.AddonPreferences:
    """
    shortcut to get blender_kitsu addon preferences
    """
    return context.preferences.addons["blender_kitsu"].preferences


def session_auth(context: bpy.types.Context) -> bool:
    """
    shortcut to check if zession is authorized
    """
    return session_get(context).is_auth()


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
