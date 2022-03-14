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


from typing import Any, Union, List, Dict, Optional

import bpy
from bpy.app.handlers import persistent

from blender_kitsu import propsdata, bkglobals
from blender_kitsu.logger import LoggerFactory

logger = LoggerFactory.getLogger()


class KITSU_sequence_colors(bpy.types.PropertyGroup):
    # name: StringProperty() -> Instantiated by default
    color: bpy.props.FloatVectorProperty(
        name="Sequence Color",
        subtype="COLOR",
        default=(1.0, 1.0, 1.0),
        min=0.0,
        max=1.0,
        description="Sequence color that will be used as line overlay",
    )


class KITSU_property_group_sequence(bpy.types.PropertyGroup):
    """
    Property group that will be registered on sequence strips.
    They hold metadata that will be used to compose a data structure that can
    be pushed to backend.
    """

    def _get_shot_description(self):
        return self.shot_description

    def _get_sequence_name(self):
        return self.sequence_name

    # Shot.
    shot_id: bpy.props.StringProperty(name="Shot ID")  # type: ignore
    shot_name: bpy.props.StringProperty(name="Shot", default="")  # type: ignore
    shot_description: bpy.props.StringProperty(name="Description", default="", options={"HIDDEN"})  # type: ignore

    # Sequence.
    sequence_name: bpy.props.StringProperty(name="Sequence", default="")  # type: ignore
    sequence_id: bpy.props.StringProperty(name="Seq ID", default="")  # type: ignore

    # Project.
    project_name: bpy.props.StringProperty(name="Project", default="")  # type: ignore
    project_id: bpy.props.StringProperty(name="Project ID", default="")  # type: ignore

    # Meta.
    initialized: bpy.props.BoolProperty(  # type: ignore
        name="Initialized", default=False, description="Is Kitsu shot"
    )
    linked: bpy.props.BoolProperty(  # type: ignore
        name="Linked", default=False, description="Is linked to an ID on server"
    )

    # Frame range.
    frame_start_offset: bpy.props.IntProperty(name="Frame Start Offset")

    # Media.
    media_outdated: bpy.props.BoolProperty(
        name="Source Media Outdated",
        default=False,
        description="Indicated if there is a newer version of the source media available",
    )

    # Display props.
    shot_description_display: bpy.props.StringProperty(name="Description", get=_get_shot_description)  # type: ignore
    sequence_name_display: bpy.props.StringProperty(name="Sequence", get=_get_sequence_name)  # type: ignore

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.shot,
            "sequence_name": self.sequence,
            "description": self.description,
        }

    def clear(self):
        self.shot_id = ""
        self.shot_name = ""
        self.shot_description = ""

        self.sequence_id = ""
        self.sequence_name = ""

        self.project_name = ""
        self.project_id = ""

        self.initialized = False
        self.linked = False

        self.frame_start_offset = 0

    def unlink(self):
        self.sequence_id = ""

        self.project_name = ""
        self.project_id = ""

        self.linked = False


class KITSU_property_group_scene(bpy.types.PropertyGroup):
    """"""

    category: bpy.props.EnumProperty(  # type: ignore
        items=(
            ("ASSETS", "Assets", "Asset related tasks", "FILE_3D", 0),
            ("SHOTS", "Shots", "Shot related tasks", "FILE_MOVIE", 1),
        ),
        default="SHOTS",
        update=propsdata.reset_task_type,
    )

    # Context props.

    sequence_active_id: bpy.props.StringProperty(  # type: ignore
        name="Active Sequence ID",
        description="ID that refers to the active sequence on server",
        default="",
    )
    shot_active_id: bpy.props.StringProperty(  # type: ignore
        name="Active Shot ID",
        description="IDthat refers to the active shot on server",
        default="",
        update=propsdata.on_shot_change,
    )
    asset_active_id: bpy.props.StringProperty(  # type: ignore
        name="Active Asset ID",
        description="ID that refers to the active asset on server",
        default="",
    )
    asset_type_active_id: bpy.props.StringProperty(  # type: ignore
        name="Active Asset Type ID",
        description="ID that refers to the active asset type on server",
        default="",
    )

    task_type_active_id: bpy.props.StringProperty(  # type: ignore
        name="Active Task Type ID",
        description="ID that refers to the active task type on server",
        default="",
    )

    # Thumbnail props.
    task_type_thumbnail_id: bpy.props.StringProperty(  # type: ignore
        name="Thumbnail Task Type ID",
        description="ID that refers to the task type on server for which thumbnails will be uploaded",
        default="",
    )

    task_type_thumbnail_name: bpy.props.StringProperty(  # type: ignore
        name="Thumbnail Task Type Name",
        description="Name that refers to the task type on server for which thumbnails will be uploaded",
        default="",
    )

    # Sqe render props.
    task_type_sqe_render_id: bpy.props.StringProperty(  # type: ignore
        name="Sqe Render Task Type ID",
        description="ID that refers to the task type on server for which the sqe render will be uploaded",
        default="",
    )

    task_type_sqe_render_name: bpy.props.StringProperty(  # type: ignore
        name="Sqe Render Task Type Name",
        description="Name that refers to the task type on server for which the sqe render will be uploaded",
        default="",
    )

    # Playblast props.

    playblast_version: bpy.props.StringProperty(name="Version", default="v001")

    playblast_dir: bpy.props.StringProperty(  # type: ignore
        name="Playblast Directory",
        description="Directory in which playblasts will be saved",
        default="",
        subtype="DIR_PATH",
        get=propsdata.get_playblast_dir,
    )

    playblast_file: bpy.props.StringProperty(  # type: ignore
        name="Playblast Filepath",
        description="Output filepath of playblast",
        default="",
        subtype="FILE_PATH",
        get=propsdata.get_playblast_file,
    )

    playblast_task_status_id: bpy.props.StringProperty(  # type: ignore
        name="Plablast Task Status ID",
        description="ID that refers to the task status on server which the playblast will set",
        default="",
    )

    # Sequence editor tools.
    pull_edit_channel: bpy.props.IntProperty(
        name="Channel",
        description="On which channel the operator will create the color strips",
        default=1,
        min=1,
        max=32,
    )

    sequence_colors: bpy.props.CollectionProperty(type=KITSU_sequence_colors)


class KITSU_property_group_error(bpy.types.PropertyGroup):
    """"""

    frame_range: bpy.props.BoolProperty(  # type: ignore
        name="Frame Range Error",
        description="Indicates if the scene frame range does not match the one in Kitsu",
        default=False,
    )


class KITSU_property_group_window_manager(bpy.types.PropertyGroup):
    """"""

    tasks_index: bpy.props.IntProperty(name="Tasks Index", default=0)

    quick_duplicate_amount: bpy.props.IntProperty(
        name="Amount",
        default=1,
        min=1,
        description="Specifies the number of copies that will be created",
    )

    def clear(self):
        pass


def _add_window_manager_props():

    # Multi Edit Properties.
    bpy.types.WindowManager.show_advanced = bpy.props.BoolProperty(
        name="Show Advanced",
        description="Shows advanced options to fine control shot pattern",
        default=False,
    )

    bpy.types.WindowManager.var_use_custom_seq = bpy.props.BoolProperty(
        name="Use Custom",
        description="Enables to type in custom sequence name for <Sequence> wildcard",
        default=False,
    )

    bpy.types.WindowManager.var_use_custom_project = bpy.props.BoolProperty(
        name="Use Custom",
        description="Enables to type in custom project name for <Project> wildcard",
        default=False,
    )

    bpy.types.WindowManager.var_sequence_custom = bpy.props.StringProperty(  # type: ignore
        name="Custom Sequence Variable",
        description="Value that will be used to insert in <Sequence> wildcard if custom sequence is enabled",
        default="",
    )

    bpy.types.WindowManager.var_project_custom = bpy.props.StringProperty(  # type: ignore
        name="Custom Project Variable",
        description="Value that will be used to insert in <Project> wildcard if custom project is enabled",
        default="",
    )

    bpy.types.WindowManager.shot_counter_start = bpy.props.IntProperty(
        description="Value that defines where the shot counter starts",
        step=10,
        min=0,
    )

    bpy.types.WindowManager.shot_preview = bpy.props.StringProperty(
        name="Shot Pattern",
        description="Preview result of current settings on how a shot will be named",
        get=propsdata._gen_shot_preview,
    )

    bpy.types.WindowManager.var_project_active = bpy.props.StringProperty(
        name="Active Project",
        description="Value that will be inserted in <Project> wildcard",
        get=propsdata._get_project_active,
    )

    bpy.types.WindowManager.sequence_enum = bpy.props.EnumProperty(
        name="Sequences",
        items=propsdata._get_sequences,
        description="Name of Sequence the generated Shots will be assinged to",
    )

    # Advanced delete props.
    bpy.types.WindowManager.advanced_delete = bpy.props.BoolProperty(
        name="Advanced Delete",
        description="Checkbox to show advanced shot deletion operations",
        default=False,
    )


def _clear_window_manager_props():
    del bpy.types.WindowManager.show_advanced
    del bpy.types.WindowManager.var_use_custom_seq
    del bpy.types.WindowManager.var_use_custom_project
    del bpy.types.WindowManager.var_sequence_custom
    del bpy.types.WindowManager.var_project_custom
    del bpy.types.WindowManager.shot_counter_start
    del bpy.types.WindowManager.shot_preview
    del bpy.types.WindowManager.var_project_active
    del bpy.types.WindowManager.sequence_enum


def _calc_kitsu_frame_start(self):
    """
    Calculates strip.kitsu_frame_start, little hack because it seems like we cant access the strip from a property group
    But we need acess to seqeuence properties.
    """
    # self.frame_final_start = 50
    # self.frame_start = 60
    # self.kitsu.frame_start_offset = 10

    offset_start = self.frame_final_start - self.frame_start  # 50 - 60 = -10

    frame_start_final = (
        bkglobals.FRAME_START - self.kitsu.frame_start_offset + offset_start
    )
    # 101 - (-10) +(-10) = 101.

    return frame_start_final


def _calc_kitsu_frame_end(self):
    """
    Calculates strip.kitsu_frame_end, little hack because it seems like we cant access the strip from a property group
    But we need acess to seqeuence properties.
    """
    # example strip goes from frame 50 - 101 (endpoint picture 100 > 51 frames duration) is trimmed
    # 10 frames in beginning and -939 in the end
    # bkglobals.FRAME_START = 101
    # self.frame_duration = 1000
    # self.frame_start = 40 (cause of trim in beginning)
    # self.kitsu.frame_start_offset = 10

    frame_end_global = self.frame_start + self.frame_duration  # (40 + 1000 = 1040)

    frame_end_final = (
        bkglobals.FRAME_START
        + self.frame_duration
        - self.kitsu.frame_start_offset
        + ((self.frame_final_end - 1) - frame_end_global)
    )
    # 101 + 1000 - 10 + ((101 -1) - 1040) = 151.

    return frame_end_final


def _get_frame_final_duration(self):
    return self.frame_final_duration


def _get_strip_filepath(self):
    return self.filepath


@persistent
def update_sequence_colors_coll_prop(dummy: Any) -> None:
    sqe = bpy.context.scene.sequence_editor
    if not sqe:
        return
    sequences = sqe.sequences_all
    sequence_colors = bpy.context.scene.kitsu.sequence_colors
    existings_seq_ids: List[str] = []

    # Append missing sequences to scene.kitsu.seqeuence_colors.
    for seq in sequences:

        if not seq.kitsu.sequence_id:
            continue

        if seq.kitsu.sequence_id not in sequence_colors.keys():
            logger.info(
                "Added %s to scene.kitsu.seqeuence_colors", seq.kitsu.sequence_name
            )
            item = sequence_colors.add()
            item.name = seq.kitsu.sequence_id

        existings_seq_ids.append(seq.kitsu.sequence_id)

    # Delete sequence colors that are not in edit anymore.
    existings_seq_ids = set(existings_seq_ids)

    to_be_removed = [
        seq_id for seq_id in sequence_colors.keys() if seq_id not in existings_seq_ids
    ]

    for seq_id in to_be_removed:
        idx = sequence_colors.find(seq_id)
        if idx == -1:
            continue

        sequence_colors.remove(idx)
        logger.info(
            "Removed %s from scene.kitsu.seqeuence_colors. Is not used in the sequence editor anymore",
            seq_id,
        )


# ----------------REGISTER--------------.

classes = [
    KITSU_sequence_colors,
    KITSU_property_group_sequence,
    KITSU_property_group_scene,
    KITSU_property_group_error,
    KITSU_property_group_window_manager,
]


def register():

    for cls in classes:
        bpy.utils.register_class(cls)

    # FRAME RANGE PROPERTIES
    # because we cant acess strip properties from a sequence group we need to create this properties
    # directly on the strip, as we need strip properties to calculate
    bpy.types.Sequence.kitsu_frame_start = bpy.props.IntProperty(
        name="3D In",
        get=_calc_kitsu_frame_start,
    )

    bpy.types.Sequence.kitsu_frame_end = bpy.props.IntProperty(
        name="3D Out",
        get=_calc_kitsu_frame_end,
    )
    bpy.types.Sequence.kitsu_frame_duration = bpy.props.IntProperty(
        name="Duration",
        get=_get_frame_final_duration,
    )

    # Used in general tools panel next to sqe_change_strip_source operator.
    bpy.types.MovieSequence.filepath_display = bpy.props.StringProperty(
        name="Filepath Display", get=_get_strip_filepath
    )

    # Sequence Properties.
    bpy.types.Sequence.kitsu = bpy.props.PointerProperty(
        name="Kitsu",
        type=KITSU_property_group_sequence,
        description="Metadata that is required for blender_kitsu",
    )

    # Scene Properties.
    bpy.types.Scene.kitsu = bpy.props.PointerProperty(
        name="Kitsu",
        type=KITSU_property_group_scene,
        description="Metadata that is required for blender_kitsu",
    )
    # Window Manager.
    bpy.types.WindowManager.kitsu = bpy.props.PointerProperty(
        name="Kitsu",
        type=KITSU_property_group_window_manager,
        description="Metadata that is required for blender_kitsu",
    )

    # Error Properties.
    bpy.types.Scene.kitsu_error = bpy.props.PointerProperty(
        name="Kitsu Error",
        type=KITSU_property_group_error,
        description="Error property group",
    )

    # Window Manager Properties.
    _add_window_manager_props()

    # Handlers.
    bpy.app.handlers.load_post.append(update_sequence_colors_coll_prop)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    # Clear properties.
    _clear_window_manager_props()

    # Handlers.
    bpy.app.handlers.load_post.remove(update_sequence_colors_coll_prop)
