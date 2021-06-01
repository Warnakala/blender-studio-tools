import contextlib
import webbrowser
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple, Any

import bpy
from bpy.app.handlers import persistent

from blender_kitsu import (
    cache,
    util,
    prefs,
    bkglobals,
)
from blender_kitsu.logger import LoggerFactory
from blender_kitsu.types import (
    Cache,
    Shot,
    Task,
    TaskStatus,
    TaskType,
)
from blender_kitsu.anim import opsdata

logger = LoggerFactory.getLogger(name=__name__)


class KITSU_OT_anim_create_playblast(bpy.types.Operator):
    """"""

    bl_idname = "kitsu.anim_create_playblast"
    bl_label = "Create Playblast"

    comment: bpy.props.StringProperty(
        name="Comment",
        description="Comment that will be appended to this playblast on kitsu.",
        default="",
    )
    confirm: bpy.props.BoolProperty(name="Confirm", default=False)

    task_status: bpy.props.EnumProperty(items=cache.get_all_task_statuses_enum)  # type: ignore

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return bool(
            prefs.session_auth(context)
            and cache.shot_active_get()
            and context.scene.camera
            and context.scene.kitsu.playblast_file
        )

    def execute(self, context: bpy.types.Context) -> Set[str]:

        addon_prefs = prefs.addon_prefs_get(context)

        if not self.task_status:
            self.report({"ERROR"}, "Failed to crate playblast. Missing task status.")
            return {"CANCELLED"}

        shot_active = cache.shot_active_get()

        # save playblast task status id for next time
        context.scene.kitsu.playblast_task_status_id = self.task_status

        logger.info("-START- Creating Playblast")

        context.window_manager.progress_begin(0, 2)
        context.window_manager.progress_update(0)

        # ----RENDER AND SAVE PLAYBLAST ------
        with self.override_render_settings(context):

            # get output path
            output_path = Path(context.scene.kitsu.playblast_file)

            # ensure folder exists
            Path(context.scene.kitsu.playblast_dir).mkdir(parents=True, exist_ok=True)

            # make opengl render
            bpy.ops.render.opengl(animation=True)

        context.window_manager.progress_update(1)

        # ----ULPOAD PLAYBLAST ------
        self._upload_playblast(context, output_path)

        context.window_manager.progress_update(2)
        context.window_manager.progress_end()

        # log
        self.report({"INFO"}, f"Created and uploaded playblast for {shot_active.name}")
        logger.info("-END- Creating Playblast")

        # redraw ui
        util.ui_redraw()

        # open webbrowser
        if addon_prefs.pb_open_webbrowser:
            self._open_webbrowser()

        return {"FINISHED"}

    def invoke(self, context, event):
        # initialize comment and playblast task status variable
        self.comment = ""

        prev_task_status_id = context.scene.kitsu.playblast_task_status_id
        if prev_task_status_id:
            self.task_status = prev_task_status_id

        return context.window_manager.invoke_props_dialog(self, width=500)

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        row = layout.row(align=True)
        row.prop(self, "task_status", text="Status")
        row = layout.row(align=True)
        row.prop(self, "comment")

    def _upload_playblast(self, context: bpy.types.Context, filepath: Path) -> None:
        # get shot
        shot = cache.shot_active_get()

        # get task status 'wip' and task type 'Animation'
        task_status = TaskStatus.by_id(self.task_status)
        task_type = TaskType.by_name("Animation")

        if not task_type:
            raise RuntimeError(
                "Failed to upload playblast. Task type: 'Animation' is missing."
            )

        # find / get latest task
        task = Task.by_name(shot, task_type)
        if not task:
            # turns out a entitiy on server can have 0 tasks even tough task types exist
            # you have to create a task first before being able to upload a thumbnail
            tasks = shot.get_all_tasks()  # list of tasks
            if not tasks:
                task = Task.new_task(shot, task_type, task_status=task_status)
            else:
                task = tasks[-1]

        # create a comment
        comment_text = self._gen_comment_text(context, shot)
        comment = task.add_comment(
            task_status,
            comment=comment_text,
        )

        # add_preview_to_comment
        preview = task.add_preview_to_comment(comment, filepath.as_posix())

        # preview.set_main_preview()
        logger.info(f"Uploaded playblast for shot: {shot.name} under: {task_type.name}")

    def _gen_comment_text(self, context: bpy.types.Context, shot: Shot) -> str:
        header = f"Playblast {shot.name}: {context.scene.kitsu.playblast_version}"
        if self.comment:
            return header + f"\n\n{self.comment}"
        return header

    def _open_webbrowser(self) -> None:
        addon_prefs = prefs.addon_prefs_get(bpy.context)
        # https://staging.kitsu.blender.cloud/productions/7838e728-312b-499a-937b-e22273d097aa/shots?search=010_0010_A

        host_url = addon_prefs.host
        if host_url.endswith("/api"):
            host_url = host_url[:-4]

        if host_url.endswith("/"):
            host_url = host_url[:-1]

        url = f"{host_url}/productions/{cache.project_active_get().id}/shots?search={cache.shot_active_get().name}"
        webbrowser.open(url)

    @contextlib.contextmanager
    def override_render_settings(self, context):
        """Overrides the render settings for playblast creation"""
        addon_prefs = prefs.addon_prefs_get(context)
        rd = context.scene.render
        sps = context.space_data.shading
        sp = context.space_data
        # get first last name for stamp note text
        session = prefs.session_get(context)
        first_name = session.data.user["first_name"]
        last_name = session.data.user["last_name"]
        # Remember current render settings in order to restore them later.

        # filepath
        filepath = rd.filepath

        # simplify
        # use_simplify = rd.use_simplify

        # format render settings
        percentage = rd.resolution_percentage
        file_format = rd.image_settings.file_format
        ffmpeg_constant_rate = rd.ffmpeg.constant_rate_factor
        ffmpeg_codec = rd.ffmpeg.codec
        ffmpeg_format = rd.ffmpeg.format
        ffmpeg_audio_codec = rd.ffmpeg.audio_codec

        # stamp metadata settings
        metadata_input = rd.metadata_input
        use_stamp_date = rd.use_stamp_date
        use_stamp_time = rd.use_stamp_time
        use_stamp_render_time = rd.use_stamp_render_time
        use_stamp_frame = rd.use_stamp_frame
        use_stamp_frame_range = rd.use_stamp_frame_range
        use_stamp_memory = rd.use_stamp_memory
        use_stamp_hostname = rd.use_stamp_hostname
        use_stamp_camera = rd.use_stamp_camera
        use_stamp_lens = rd.use_stamp_lens
        use_stamp_scene = rd.use_stamp_scene
        use_stamp_marker = rd.use_stamp_marker
        use_stamp_marker = rd.use_stamp_marker
        use_stamp_note = rd.use_stamp_note
        stamp_note_text = rd.stamp_note_text
        use_stamp = rd.use_stamp
        stamp_font_size = rd.stamp_font_size
        stamp_foreground = rd.stamp_foreground
        stamp_background = rd.stamp_background
        use_stamp_labels = rd.use_stamp_labels

        # space data settings
        shading_type = sps.type
        shading_light = sps.light
        studio_light = sps.studio_light
        color_type = sps.color_type
        background_type = sps.background_type

        show_backface_culling = sps.show_backface_culling
        show_xray = sps.show_xray
        show_shadows = sps.show_shadows
        show_cavity = sps.show_cavity
        use_dof = sps.use_dof
        show_object_outline = sps.show_object_outline
        show_specular_highlight = sps.show_specular_highlight

        show_gizmo = sp.show_gizmo

        try:
            # filepath
            rd.filepath = context.scene.kitsu.playblast_file

            # simplify
            # rd.use_simplify = False

            # format render settings
            rd.resolution_percentage = 100
            rd.image_settings.file_format = "FFMPEG"
            rd.ffmpeg.constant_rate_factor = "HIGH"
            rd.ffmpeg.codec = "H264"
            rd.ffmpeg.format = "MPEG4"
            rd.ffmpeg.audio_codec = "AAC"

            # stamp metadata settings
            rd.metadata_input = "SCENE"
            rd.use_stamp_date = False
            rd.use_stamp_time = False
            rd.use_stamp_render_time = False
            rd.use_stamp_frame = True
            rd.use_stamp_frame_range = False
            rd.use_stamp_memory = False
            rd.use_stamp_hostname = False
            rd.use_stamp_camera = False
            rd.use_stamp_lens = True
            rd.use_stamp_scene = False
            rd.use_stamp_marker = False
            rd.use_stamp_marker = False
            rd.use_stamp_note = True
            rd.stamp_note_text = f"Animator: {first_name} {last_name}"
            rd.use_stamp = True
            rd.stamp_font_size = 12
            rd.stamp_foreground = (0.8, 0.8, 0.8, 1)
            rd.stamp_background = (0, 0, 0, 0.25)
            rd.use_stamp_labels = True

            # space data settings
            sps.type = "SOLID"
            sps.light = "STUDIO"
            sps.studio_light = "Default"
            sps.color_type = "MATERIAL"
            sps.background_type = "THEME"

            sps.show_backface_culling = False
            sps.show_xray = False
            sps.show_shadows = False
            sps.show_cavity = False
            sps.use_dof = False
            sps.show_object_outline = False
            sps.show_specular_highlight = True

            sp.show_gizmo = False

            yield

        finally:
            # filepath
            rd.filepath = filepath

            # simplify
            # rd.use_simplify = use_simplify

            # Return the render settings to normal.
            rd.resolution_percentage = percentage
            rd.image_settings.file_format = file_format
            rd.ffmpeg.codec = ffmpeg_codec
            rd.ffmpeg.constant_rate_factor = ffmpeg_constant_rate
            rd.ffmpeg.format = ffmpeg_format
            rd.ffmpeg.audio_codec = ffmpeg_audio_codec

            # stamp metadata settings
            rd.metadata_input = metadata_input
            rd.use_stamp_date = use_stamp_date
            rd.use_stamp_time = use_stamp_time
            rd.use_stamp_render_time = use_stamp_render_time
            rd.use_stamp_frame = use_stamp_frame
            rd.use_stamp_frame_range = use_stamp_frame_range
            rd.use_stamp_memory = use_stamp_memory
            rd.use_stamp_hostname = use_stamp_hostname
            rd.use_stamp_camera = use_stamp_camera
            rd.use_stamp_lens = use_stamp_lens
            rd.use_stamp_scene = use_stamp_scene
            rd.use_stamp_marker = use_stamp_marker
            rd.use_stamp_marker = use_stamp_marker
            rd.use_stamp_note = use_stamp_note
            rd.stamp_note_text = stamp_note_text
            rd.use_stamp = use_stamp
            rd.stamp_font_size = stamp_font_size
            rd.stamp_foreground = stamp_foreground
            rd.stamp_background = stamp_background
            rd.use_stamp_labels = use_stamp_labels

            # space data settings
            sps.type = shading_type
            sps.light = shading_light
            sps.studio_light = studio_light
            sps.color_type = color_type
            sps.background_type = background_type

            sps.show_backface_culling = show_backface_culling
            sps.show_xray = show_xray
            sps.show_shadows = show_shadows
            sps.show_cavity = show_cavity
            sps.use_dof = use_dof
            sps.show_object_outline = show_object_outline
            sps.show_specular_highlight = show_specular_highlight

            sp.show_gizmo = show_gizmo


class KITSU_OT_anim_set_playblast_version(bpy.types.Operator):
    """"""

    bl_idname = "kitsu.anim_set_playblast_version"
    bl_label = "Version"
    bl_property = "versions"

    versions: bpy.props.EnumProperty(
        items=opsdata.get_playblast_versions_enum_list, name="Versions"
    )

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        addon_prefs = prefs.addon_prefs_get(context)
        return bool(context.scene.kitsu.playblast_dir)

    def execute(self, context: bpy.types.Context) -> Set[str]:
        version = self.versions

        if not version:
            return {"CANCELLED"}

        if context.scene.kitsu.playblast_version == version:
            return {"CANCELLED"}

        # update global scene cache version prop
        context.scene.kitsu.playblast_version = version
        logger.info("Set playblast version to %s", version)

        # redraw ui
        util.ui_redraw()

        return {"FINISHED"}

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event) -> Set[str]:
        context.window_manager.invoke_search_popup(self)  # type: ignore
        return {"FINISHED"}


class KITSU_OT_anim_pull_frame_range(bpy.types.Operator):
    """"""

    bl_idname = "kitsu.anim_pull_frame_range"
    bl_label = "Update Frame Range"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return bool(prefs.session_auth(context) and cache.shot_active_get())

    def execute(self, context: bpy.types.Context) -> Set[str]:
        active_shot = cache.shot_active_pull_update()

        if "3d_in" not in active_shot.data or "3d_out" not in active_shot.data:
            self.report(
                {"ERROR"},
                f"Failed to pull frame range. Shot {active_shot.name} missing '3d_in', '3d_out' attribute on server.",
            )
            return {"CANCELLED"}

        frame_in = int(active_shot.data["3d_in"])
        frame_out = int(active_shot.data["3d_out"])

        # check if current frame range matches the one for active shot
        if (
            frame_in == context.scene.frame_start
            and frame_out == context.scene.frame_end
        ):
            self.report({"INFO"}, f"Frame range already up to date")
            return {"FINISHED"}

        # update scene frame range
        context.scene.frame_start = frame_in
        context.scene.frame_end = frame_out

        # update error prop
        context.scene.kitsu_error.frame_range = False

        # log
        self.report({"INFO"}, f"Updated frame range {frame_in} - {frame_out}")
        return {"FINISHED"}


class KITSU_OT_anim_increment_playblast_version(bpy.types.Operator):
    """"""

    bl_idname = "kitsu.anim_increment_playblast_version"
    bl_label = "Add Version Increment"

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return True

    def execute(self, context: bpy.types.Context) -> Set[str]:

        # incremenet version
        version = opsdata.add_playblast_version_increment(context)

        # update cache_version prop
        context.scene.kitsu.playblast_version = version

        # report
        self.report({"INFO"}, f"Add playblast version {version}")

        util.ui_redraw()
        return {"FINISHED"}


@persistent
def load_post_handler_init_version_model(dummy: Any) -> None:
    opsdata.init_playblast_file_model(bpy.context)


@persistent
def load_post_handler_check_frame_range(dummy: Any) -> None:
    """
    Compares current scenes frame range with the active shot one on kitsu.
    If mismatch sets kitsu_error.frame_range -> True. This will enable
    a warning in the Animation Tools Tab UI
    """
    active_shot = cache.shot_active_get()
    if not active_shot:
        return

    # pull update for shot
    cache.shot_active_pull_update()

    if "3d_in" not in active_shot.data or "3d_out" not in active_shot.data:
        logger.warning(
            "Failed to check frame range. Shot %s missing '3d_in', '3d_out' attribute on server.",
            active_shot.name,
        )
        return

    frame_in = int(active_shot.data["3d_in"])
    frame_out = int(active_shot.data["3d_out"])

    if (
        frame_in == bpy.context.scene.frame_start
        and frame_out == bpy.context.scene.frame_end
    ):
        bpy.context.scene.kitsu_error.frame_range = False
        return

    bpy.context.scene.kitsu_error.frame_range = True
    logger.warning("Current frame range is outdated!")


# ---------REGISTER ----------

classes = [
    KITSU_OT_anim_create_playblast,
    KITSU_OT_anim_set_playblast_version,
    KITSU_OT_anim_increment_playblast_version,
    KITSU_OT_anim_pull_frame_range,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    # init model
    # init_playblast_file_model(bpy.context) #not working because of restr. context

    # handlers
    bpy.app.handlers.load_post.append(load_post_handler_init_version_model)
    bpy.app.handlers.load_post.append(load_post_handler_check_frame_range)


def unregister():

    # clear handlers
    bpy.app.handlers.load_post.remove(load_post_handler_check_frame_range)
    bpy.app.handlers.load_post.remove(load_post_handler_init_version_model)

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
