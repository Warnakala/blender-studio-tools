import bpy

from . import propsdata
from .logger import ZLoggerFactory

logger = ZLoggerFactory.getLogger(name=__name__)


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

    def unlink(self):
        self.sequence_id = ""

        self.project_name = ""
        self.project_id = ""

        self.linked = False


class KITSU_property_group_scene(bpy.types.PropertyGroup):
    """"""

    sequence_active_id: bpy.props.StringProperty(  # type: ignore
        name="Active Sequence ID",
        description="ID that refers to the active sequence on server",
        default="",
        options={"HIDDEN", "SKIP_SAVE"},
    )
    shot_active_id: bpy.props.StringProperty(  # type: ignore
        name="Active Shot ID",
        description="IDthat refers to the active project on server",
        default="",
        options={"HIDDEN", "SKIP_SAVE"},
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

    def clear(self):
        self.sequence_active_id = ""
        self.shot_active_id = ""
        self.asset_active_id = ""
        self.asset_type_active_id = ""


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


# ----------------REGISTER--------------

classes = [KITSU_property_group_sequence, KITSU_property_group_scene]


def register():

    for cls in classes:
        bpy.utils.register_class(cls)

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
    # Window Manager Properties
    _add_window_manager_props()


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    # clear properties
    _clear_window_manager_props()
