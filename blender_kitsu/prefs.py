# ***** BEGIN GPL LICENSE BLOCK *****
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
# ***** END GPL LICENCE BLOCK *****
#
# (c) 2021, Blender Foundation - Paul Golter

import hashlib
import sys
import os
import re

from typing import Optional, Any, Set, Tuple, List
from pathlib import Path

import bpy

from blender_kitsu import cache, bkglobals

# TODO: restructure this to not access ops_playblast_data.
from blender_kitsu.playblast import opsdata as ops_playblast_data
from blender_kitsu.types import Session
from blender_kitsu.logger import LoggerFactory
from blender_kitsu.auth.ops import (
    KITSU_OT_session_end,
    KITSU_OT_session_start,
)
from blender_kitsu.context.ops import KITSU_OT_con_productions_load
from blender_kitsu.lookdev.prefs import LOOKDEV_preferences
from blender_kitsu.shot_builder.editorial.core import editorial_export_check_latest


logger = LoggerFactory.getLogger()


class KITSU_task(bpy.types.PropertyGroup):
    # name: StringProperty() -> Instantiated by default
    id: bpy.props.StringProperty(name="Task ID", default="")
    entity_id: bpy.props.StringProperty(name="Entity ID", default="")
    entity_name: bpy.props.StringProperty(name="Entity Name", default="")
    task_type_id: bpy.props.StringProperty(name="Task Type ID", default="")
    task_type_name: bpy.props.StringProperty(name="Task Type Name", default="")


class KITSU_media_update_search_paths(bpy.types.PropertyGroup):
    # name: StringProperty() -> Instantiated by default
    filepath: bpy.props.StringProperty(
        name="Media Update Search Path",
        default="",
        subtype="DIR_PATH",
        description="Top level directory path in which to search for media updates",
    )


class KITSU_OT_prefs_media_search_path_add(bpy.types.Operator):
    """"""

    bl_idname = "kitsu.prefs_media_search_path_add"
    bl_label = "Add Path"
    bl_description = "Adds new entry to media update search paths list"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context: bpy.types.Context) -> Set[str]:
        addon_prefs = addon_prefs_get(context)
        media_update_search_paths = addon_prefs.media_update_search_paths

        item = media_update_search_paths.add()

        return {"FINISHED"}


class KITSU_OT_prefs_media_search_path_remove(bpy.types.Operator):
    """"""

    bl_idname = "kitsu.prefs_media_search_path_remove"
    bl_label = "Removes Path"
    bl_description = "Removes Path from media udpate search paths list"
    bl_options = {"REGISTER", "UNDO"}

    index: bpy.props.IntProperty(
        name="Index",
        description="Refers to index that will be removed from collection property",
    )

    def execute(self, context: bpy.types.Context) -> Set[str]:
        addon_prefs = addon_prefs_get(context)
        media_update_search_paths = addon_prefs.media_update_search_paths

        media_update_search_paths.remove(self.index)

        return {"FINISHED"}


class KITSU_addon_preferences(bpy.types.AddonPreferences):
    """
    Addon preferences to kitsu. Holds variables that are important for authentication and configuring
    how some of the operators work.
    """

    def get_datadir(self) -> Path:
        """Returns a Path where persistent application data can be stored.

        # linux: ~/.local/share
        # macOS: ~/Library/Application Support
        # windows: C:/Users/<USER>/AppData/Roaming
        """
        # This function is copied from the edit_breakdown addon by Inês Almeida and Francesco Siddi.

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
        # This function is copied and modified from the edit_breakdown addon by Inês Almeida and Francesco Siddi.

        hashed_filepath = hashlib.md5(bpy.data.filepath.encode()).hexdigest()
        storage_dir = (
            self.get_datadir() / "blender_kitsu" / "thumbnails" / hashed_filepath
        )
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

    def get_metastrip_file(self) -> str:
        res_dir = bkglobals.RES_DIR_PATH
        return res_dir.joinpath("metastrip.mp4").as_posix()

    def init_playblast_file_model(self, context: bpy.types.Context) -> None:
        ops_playblast_data.init_playblast_file_model(context)

    bl_idname = __package__

    host: bpy.props.StringProperty(  # type: ignore
        name="Host",
        default="",
    )

    email: bpy.props.StringProperty(  # type: ignore
        name="Email",
        default="",
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
        description="Directory in which sequence renders will be saved",
        default="",
        subtype="DIR_PATH",
        get=get_sqe_render_dir,
    )

    lookdev: bpy.props.PointerProperty(  # type: ignore
        name="Lookdev Preferences",
        type=LOOKDEV_preferences,
        description="Metadata that is required for lookdev",
    )

    playblast_root_dir: bpy.props.StringProperty(  # type: ignore
        name="Playblasts Root Directory",
        description="Directory path to playblast root folder. Should point to: ./Blender Dropbox/render/sprites/shots/",
        default="",
        subtype="DIR_PATH",
        update=init_playblast_file_model,
    )

    project_root_dir: bpy.props.StringProperty(  # type: ignore
        name="Project Root Directory",
        description=(
            "Directory path to the root of the project"
            "In this directory blender kitsu searches for ./pipeline/blender_kitsu"
            "folder to configure the addon per project"
        ),
        default="",
        subtype="DIR_PATH",
    )
    config_dir: bpy.props.StringProperty(  # type: ignore
        name="Config Directory",
        description=(
            "Configuration directory of blender_kitsu"
            "See readme.md how you can configurate the addon on a per project basis"
        ),
        default="",
        subtype="DIR_PATH",
        get=get_config_dir,
    )

    metastrip_file: bpy.props.StringProperty(  # type: ignore
        name="Meta Strip File",
        description=(
            "Filepath to black .mp4 file that will be used as metastrip for shots in the sequence editor"
        ),
        default="",
        subtype="FILE_PATH",
        get=get_metastrip_file,
    )

    project_active_id: bpy.props.StringProperty(  # type: ignore
        name="Project Active ID",
        description="Server Id that refers to the last active project",
        default="",
    )

    enable_debug: bpy.props.BoolProperty(  # type: ignore
        name="Enable Debug Operators",
        description="Enables Operatots that provide debug functionality",
    )
    show_advanced: bpy.props.BoolProperty(  # type: ignore
        name="Show Advanced Settings",
        description="Show advanced settings that should already have good defaults",
    )
    shot_builder_show_advanced : bpy.props.BoolProperty(  # type: ignore
        name="Show Advanced Settings",
        description="Show advanced settings that should already have good defaults",
    )

    shot_pattern: bpy.props.StringProperty(  # type: ignore
        name="Shot Pattern",
        description="Pattern to define how Bulk Init will name the shots. Supported wildcards: <Project>, <Sequence>, <Counter>",
        default="<Sequence>_<Counter>_A",
    )

    shot_counter_digits: bpy.props.IntProperty(  # type: ignore
        name="Shot Counter Digits",
        description="How many digits the counter should contain",
        default=4,
        min=0,
    )
    shot_counter_increment: bpy.props.IntProperty(  # type: ignore
        name="Shot Counter Increment",
        description="By which Increment counter should be increased",
        default=10,
        step=5,
        min=0,
    )
    pb_open_webbrowser: bpy.props.BoolProperty(  # type: ignore
        name="Open Webbrowser after Playblast",
        description="Toggle if the default webbrowser should be opened to kitsu after playblast creation",
        default=False,
    )

    pb_open_vse: bpy.props.BoolProperty(  # type: ignore
        name="Open Sequence Editor after Playblast",
        description="Toggle if the movie clip should be loaded in the seqeuence editor in a seperate scene after playblast creation",
        default=False,
    )

    media_update_search_paths: bpy.props.CollectionProperty(
        type=KITSU_media_update_search_paths
    )

    production_path: bpy.props.StringProperty(  # type: ignore
        name="Production Root",
        description="The location to load configuration files from when "
        "they couldn't be found in any parent folder of the current "
        "file. Folder must contain a sub-folder named `shot-builder` "
        "that holds the configuration files",
        subtype='DIR_PATH',
    )

    edit_export_dir: bpy.props.StringProperty(  # type: ignore
        name="Editorial Export Directory",
        options={"HIDDEN", "SKIP_SAVE"},
        description="Directory path to editorial's export folder containing storyboard/animatic exports. Path should be similar to '~/shared-{proj_name}/editorial/export/'",
        subtype="DIR_PATH",
    )

    edit_export_file_pattern: bpy.props.StringProperty(  # type: ignore
        name="Editorial Export File Pattern",
        options={"HIDDEN", "SKIP_SAVE"},
        description="File pattern to search for latest editorial export. Typically '{proj_name}_v\d\d\d.mp4'",
        default="petprojects_v\d\d\d.mp4",
       
    )

    edit_export_frame_offset: bpy.props.IntProperty(  # type: ignore
        name="Editorial Export Offset",
        description="Shift Editorial Export by this frame-range after set-up.",
        default=-102, #HARD CODED FOR PET PROJECTS BLENDER FILM
    )

    shot_builder_frame_offset: bpy.props.IntProperty(  # type: ignore
        name="Start Frame Offset",
        description="All Shots built by 'Shot_builder' should begin at this frame",
        default=101,
    )

    shot_builder_armature_prefix: bpy.props.StringProperty(  # type: ignore
        name="Armature Prefix",
        description="Naming convention prefix that exists on published assets containing armatures. Used to create/name actions during 'Shot_Build'. Armature name example:'{prefix}{base_name}'",
        default="RIG-",
    )

    shot_builder_action_prefix: bpy.props.StringProperty(  # type: ignore
        name="Action Prefix",
        description="Naming convention prefix to add to new actions. Actions will be named '{prefix}{base_name}.{shot_name}.v001' and set to fake user during 'Shot_Build'",
        default="ANI-",
    )

    user_exec_code: bpy.props.StringProperty(# type: ignore
        name="Post Execution Command",
        description="Run this command after shot_builder is complete, but before the file is saved.",
        default="",
    )

    session: Session = Session()

    tasks: bpy.props.CollectionProperty(type=KITSU_task)

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        project_active = cache.project_active_get()

        # Login.
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

        # Production.
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

        # Anim tools settings.
        box = layout.box()
        box.label(text="Animation Tools", icon="RENDER_ANIMATION")
        box.row().prop(self, "playblast_root_dir")
        box.row().prop(self, "pb_open_webbrowser")
        box.row().prop(self, "pb_open_vse")

        # Lookdev tools settings.
        self.lookdev.draw(context, layout)

        # Sequence editor include paths.
        box = layout.box()
        box.label(text="Media Update Search Paths", icon="SEQUENCE")
        box.label(
            text="Only the movie strips that have their source media coming from one of these folders (recursive) will be checked for media updates"
        )

        for i, item in enumerate(self.media_update_search_paths):
            row = box.row()
            row.prop(item, "filepath", text="")
            row.operator(
                KITSU_OT_prefs_media_search_path_remove.bl_idname,
                text="",
                icon="X",
                emboss=False,
            ).index = i
        row = box.row()
        row.alignment = "LEFT"
        row.operator(
            KITSU_OT_prefs_media_search_path_add.bl_idname,
            text="",
            icon="ADD",
            emboss=False,
        )
        
        # Shot_Builder settings.
        box = layout.box()
        box.label(text="Shot Builder", icon="MOD_BUILD")
        box.row().prop(self, "edit_export_dir")
        box.row().prop(self, "edit_export_file_pattern")
        box.row().prop(self, "edit_export_frame_offset")
        box.row().prop(self, "shot_builder_show_advanced")
        if self.shot_builder_show_advanced:
            start_frame_row = box.row()
            start_frame_row.label(text="Start Frame Offset")
            start_frame_row.prop(self, "shot_builder_frame_offset", text="")
            box.row().prop(self, "shot_builder_armature_prefix")
            box.row().prop(self, "shot_builder_action_prefix") 
            box.row().prop(self, "user_exec_code")

        # Misc settings.
        box = layout.box()
        box.label(text="Miscellaneous", icon="MODIFIER")
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
        if not self.project_root_dir:
            return False

        if not bpy.data.filepath and self.project_root_dir.startswith("//"):
            return False

        return True

    @property
    def is_config_dir_valid(self) -> bool:
        if not self.config_dir:
            return False

        if not bpy.data.filepath and self.config_dir.startswith("//"):
            return False

        return True
    
    @property
    def is_editorial_dir_valid(self) -> bool:
        if editorial_export_check_latest(bpy.context) is None:
            logger.error(
                    "Failed to initialize editorial export file model. Invalid path/pattern. Check addon preferences"
                )
            return False
        return True

def session_get(context: bpy.types.Context) -> Session:
    """
    Shortcut to get session from blender_kitsu addon preferences
    """
    prefs = context.preferences.addons["blender_kitsu"].preferences
    return prefs.session  # type: ignore


def addon_prefs_get(context: bpy.types.Context) -> bpy.types.AddonPreferences:
    """
    Shortcut to get blender_kitsu addon preferences
    """
    return context.preferences.addons["blender_kitsu"].preferences


def session_auth(context: bpy.types.Context) -> bool:
    """
    Shortcut to check if zession is authorized
    """
    return session_get(context).is_auth()


# ---------REGISTER ----------.

classes = [
    KITSU_OT_prefs_media_search_path_remove,
    KITSU_OT_prefs_media_search_path_add,
    KITSU_task,
    KITSU_media_update_search_paths,
    KITSU_addon_preferences,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():

    # Log user out.
    addon_prefs = bpy.context.preferences.addons["blender_kitsu"].preferences
    if addon_prefs.session.is_auth():
        addon_prefs.session.end()

    # Unregister classes.
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
