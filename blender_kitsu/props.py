import bpy

from blender_kitsu import propsdata, bkglobals
from blender_kitsu.logger import LoggerFactory

logger = LoggerFactory.getLogger(name=__name__)


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

    def _cal_frame_duration(self):
        return self.frame_end - self.frame_start + 1

    # shot
    shot_id: bpy.props.StringProperty(name="Shot ID")  # type: ignore
    shot_name: bpy.props.StringProperty(name="Shot", default="")  # type: ignore
    shot_description: bpy.props.StringProperty(name="Description", default="", options={"HIDDEN"})  # type: ignore

    # sequence
    sequence_name: bpy.props.StringProperty(name="Sequence", default="")  # type: ignore
    sequence_id: bpy.props.StringProperty(name="Seq ID", default="")  # type: ignore

    # project
    project_name: bpy.props.StringProperty(name="Project", default="")  # type: ignore
    project_id: bpy.props.StringProperty(name="Project ID", default="")  # type: ignore

    # meta
    initialized: bpy.props.BoolProperty(  # type: ignore
        name="Initialized", default=False, description="Is Kitsu shot"
    )
    linked: bpy.props.BoolProperty(  # type: ignore
        name="Linked", default=False, description="Is linked to an ID on server"
    )

    # frame range
    frame_start_offset: bpy.props.IntProperty(name="Frame Start Offset")
    frame_end_offset: bpy.props.IntProperty(name="Frame End Offset")
    frame_start: bpy.props.IntProperty(name="Frame Start")
    frame_end: bpy.props.IntProperty(name="Frame End")
    frame_duration: bpy.props.IntProperty(
        name="Frame Duration", get=_cal_frame_duration
    )

    # display props
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
        self.frame_end_offset = 0

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

    # context props

    sequence_active_id: bpy.props.StringProperty(  # type: ignore
        name="Active Sequence ID",
        description="ID that refers to the active sequence on server",
        default="",
        options={"HIDDEN", "SKIP_SAVE"},
    )
    shot_active_id: bpy.props.StringProperty(  # type: ignore
        name="Active Shot ID",
        description="IDthat refers to the active shot on server",
        default="",
        options={"HIDDEN", "SKIP_SAVE"},
        update=propsdata.on_shot_change,
    )
    asset_active_id: bpy.props.StringProperty(  # type: ignore
        name="Active Asset ID",
        description="ID that refers to the active asset on server",
        default="",
        options={"HIDDEN", "SKIP_SAVE"},
    )
    asset_type_active_id: bpy.props.StringProperty(  # type: ignore
        name="Active Asset Type ID",
        description="ID that refers to the active asset type on server",
        default="",
        options={"HIDDEN", "SKIP_SAVE"},
    )

    task_type_active_id: bpy.props.StringProperty(  # type: ignore
        name="Active Task Type ID",
        description="ID that refers to the active task type on server",
        default="",
        options={"HIDDEN", "SKIP_SAVE"},
    )

    # thubnail props
    task_type_thumbnail_id: bpy.props.StringProperty(  # type: ignore
        name="Thubmnail Task Type ID",
        description="ID that refers to the task type on server for which thumbnails will be uploaded",
        default="",
        options={"HIDDEN", "SKIP_SAVE"},
    )

    task_type_thumbnail_name: bpy.props.StringProperty(  # type: ignore
        name="Thubmnail Task Type Name",
        description="Name that refers to the task type on server for which thumbnails will be uploaded",
        default="",
        options={"HIDDEN", "SKIP_SAVE"},
    )

    # sqe render props
    task_type_sqe_render_id: bpy.props.StringProperty(  # type: ignore
        name="Sqe Render Task Type ID",
        description="ID that refers to the task type on server for which the sqe render will be uploaded",
        default="",
        options={"HIDDEN", "SKIP_SAVE"},
    )

    task_type_sqe_render_name: bpy.props.StringProperty(  # type: ignore
        name="Sqe Render Task Type Name",
        description="Name that refers to the task type on server for which the sqe render will be uploaded",
        default="",
        options={"HIDDEN", "SKIP_SAVE"},
    )

    # playblast props

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
        description="Output filepath of playblast.",
        default="",
        subtype="FILE_PATH",
        get=propsdata.get_playblast_file,
    )

    playblast_task_status_id: bpy.props.StringProperty(  # type: ignore
        name="Plablast Task Status ID",
        description="ID that refers to the task status on server which the playblast will set",
        default="",
        options={"HIDDEN", "SKIP_SAVE"},
    )

    # sequence editor tools
    pull_edit_channel: bpy.props.IntProperty(
        name="Channel",
        description="On which channel the operator will create the color strips.",
        default=1,
        min=1,
        max=32,
    )


class KITSU_property_group_error(bpy.types.PropertyGroup):
    """"""

    frame_range: bpy.props.BoolProperty(  # type: ignore
        name="Frame Range Error",
        description="Indicates if the scene frame range does not match the one in kitsu",
        default=False,
    )


class KITSU_property_group_window(bpy.types.PropertyGroup):
    """"""

    multi_edit_seq: bpy.props.StringProperty(  # type: ignore
        name="Sequence",
        description="",
        default="",
    )

    def clear(self):
        self.multi_edit_seq = ""


def _add_window_manager_props():

    # Multi Edit Properties
    bpy.types.WindowManager.show_advanced = bpy.props.BoolProperty(
        name="Show Advanced",
        description="Shows advanced options to fine control shot pattern.",
        default=False,
    )

    bpy.types.WindowManager.var_use_custom_seq = bpy.props.BoolProperty(
        name="Use Custom",
        description="Enables to type in custom sequence name for <Sequence> wildcard.",
        default=False,
    )

    bpy.types.WindowManager.var_use_custom_project = bpy.props.BoolProperty(
        name="Use Custom",
        description="Enables to type in custom project name for <Project> wildcard",
        default=False,
    )

    bpy.types.WindowManager.var_sequence_custom = bpy.props.StringProperty(  # type: ignore
        name="Custom Sequence Variable",
        description="Value that will be used to insert in <Sequence> wildcard if custom sequence is enabled.",
        default="",
    )

    bpy.types.WindowManager.var_project_custom = bpy.props.StringProperty(  # type: ignore
        name="Custom Project Variable",
        description="Value that will be used to insert in <Project> wildcard if custom project is enabled.",
        default="",
    )

    bpy.types.WindowManager.shot_counter_start = bpy.props.IntProperty(
        description="Value that defines where the shot counter starts.",
        step=10,
        min=0,
    )

    bpy.types.WindowManager.shot_preview = bpy.props.StringProperty(
        name="Shot Pattern",
        description="Preview result of current settings on how a shot will be named.",
        get=propsdata._gen_shot_preview,
    )

    bpy.types.WindowManager.var_project_active = bpy.props.StringProperty(
        name="Active Project",
        description="Value that will be inserted in <Project> wildcard.",
        get=propsdata._get_project_active,
    )

    bpy.types.WindowManager.sequence_enum = bpy.props.EnumProperty(
        name="Sequences",
        items=propsdata._get_sequences,
        description="Name of Sequence the generated Shots will be assinged to.",
    )

    # advanced delete props
    bpy.types.WindowManager.advanced_delete = bpy.props.BoolProperty(
        name="Advanced Delete",
        description="Checkbox to show advanced shot deletion operations.",
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


def _calc_kitsu_frame_start_old(self):
    offset_start = self.frame_final_start - self.frame_start

    self.kitsu.frame_start = self.kitsu.frame_start_init + offset_start
    return self.kitsu.frame_start


def _calc_kitsu_frame_end_old(self):

    frame_end = self.frame_start + self.frame_duration
    offset_end = self.frame_final_end - frame_end

    self.kitsu.frame_end = self.kitsu.frame_end_init + offset_end
    return self.kitsu.frame_end


def _calc_kitsu_frame_start(self):
    # self.frame_final_start = 50
    # self.frame_start = 60
    # self.kitsu.frame_start_offset = 10

    offset_start = self.frame_final_start - self.frame_start  # 50 - 60 = -10

    self.kitsu.frame_start = (
        bkglobals.FRAME_START
        - self.kitsu.frame_start_offset
        + offset_start  # 101 - (-10) +(-10) = 101
    )
    return self.kitsu.frame_start


def _calc_kitsu_frame_end(self):
    # self.kitsu.frame_end_offset = -939
    """
    -> when user hits initialize frame range this is the offset of the total duration of the clip
    to the 'new ending' it gets calculated in the KITSU_OT_sqe_init_strip_frame_range op:
    -frame_end = strip.frame_start + strip.frame_duration
    -strip.kitsu.frame_end_offset = strip.frame_final_end - frame_end
    """

    # bkglobals.FRAME_START = 101
    # self.frame_duration = 1000
    # self.frame_start = 50
    # self.kitsu.frame_start_offset = 10
    """
    frame_end_init is the end frame of the strip when it was originally initialized
    that is our reference point for any further frame shifts, trims or changes
    """
    frame_end_init = (
        bkglobals.FRAME_START
        + self.frame_duration
        + (self.kitsu.frame_end_offset - 1)  # TODO: can be discarded
        - self.kitsu.frame_start_offset
    )  # 101 + 1000 + (-939 -1)  - 10 = 151

    offset_end_init = self.kitsu.frame_end_offset  # -939 #TODO: can be discarded

    frame_end_global = self.frame_start + self.frame_duration  # (50 + 1000 = 1050)
    offset_end_global = self.frame_final_end - frame_end_global  # 101 - 1050 = -939)

    offset_end_total = offset_end_global - offset_end_init
    frame_end_final = frame_end_init + offset_end_total  # 150 + 0 = 150)

    self.kitsu.frame_end = frame_end_final
    return self.kitsu.frame_end


# ----------------REGISTER--------------

classes = [
    KITSU_property_group_sequence,
    KITSU_property_group_scene,
    KITSU_property_group_error,
]


def register():

    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Sequence.calc_kitsu_frame_start = bpy.props.IntProperty(
        name="Testi",
        get=_calc_kitsu_frame_start,
    )
    bpy.types.Sequence.calc_kitsu_frame_end = bpy.props.IntProperty(
        name="Testi",
        get=_calc_kitsu_frame_end,
    )

    # Sequence Properties
    bpy.types.Sequence.kitsu = bpy.props.PointerProperty(
        name="Kitsu",
        type=KITSU_property_group_sequence,
        description="Metadata that is required for blender_kitsu",
    )
    # Scene Properties
    bpy.types.Scene.kitsu = bpy.props.PointerProperty(
        name="Kitsu",
        type=KITSU_property_group_scene,
        description="Metadata that is required for blender_kitsu",
    )

    # Error Properties
    bpy.types.Scene.kitsu_error = bpy.props.PointerProperty(
        name="Kitsu Error",
        type=KITSU_property_group_error,
        description="Error property group",
    )

    # Window Manager Properties
    _add_window_manager_props()


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    # clear properties
    _clear_window_manager_props()
