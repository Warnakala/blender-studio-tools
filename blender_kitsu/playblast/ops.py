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
# (c) 2023, Blender Foundation

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
    Shot,
    Task,
    TaskStatus,
    TaskType,
)
from blender_kitsu.playblast.core import override_render_settings
from blender_kitsu.playblast import opsdata

logger = LoggerFactory.getLogger()


class KITSU_OT_playblast_create(bpy.types.Operator):
    bl_idname = "kitsu.playblast_create"
    bl_label = "Create Playblast"
    bl_description = (
        "Creates an openGl render of the window in which the operator was triggered. "
        "Saves the set version to disk and uploads it to Kitsu with the specified "
        "comment and task type. Overrides some render settings during export. "
        "Opens web browser or VSE after playblast if set in addon preferences"
    )

    comment: bpy.props.StringProperty(
        name="Comment",
        description="Comment that will be appended to this playblast on Kitsu",
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
            self.report({"ERROR"}, "Failed to create playblast. Missing task status")
            return {"CANCELLED"}

        shot_active = cache.shot_active_get()

        # Save playblast task status id for next time.
        context.scene.kitsu.playblast_task_status_id = self.task_status

        logger.info("-START- Creating Playblast")

        context.window_manager.progress_begin(0, 2)
        context.window_manager.progress_update(0)

        # Render and save playblast
        with override_render_settings(self, context, context.scene.kitsu.playblast_file):

            # Get output path.
            output_path = Path(context.scene.kitsu.playblast_file)

            # Ensure folder exists.
            Path(context.scene.kitsu.playblast_dir).mkdir(parents=True, exist_ok=True)

            # Make opengl render.
            bpy.ops.render.opengl(animation=True)

        context.window_manager.progress_update(1)

        # Upload playblast
        self._upload_playblast(context, output_path)

        context.window_manager.progress_update(2)
        context.window_manager.progress_end()

        self.report({"INFO"}, f"Created and uploaded playblast for {shot_active.name}")
        logger.info("-END- Creating Playblast")

        # Redraw UI
        util.ui_redraw()

        # Post playblast

        # Open web browser
        if addon_prefs.pb_open_webbrowser:
            self._open_webbrowser()

        # Open playblast in second scene video sequence editor.
        if addon_prefs.pb_open_vse:
            # Create new scene.
            scene_orig = bpy.context.scene
            try:
                scene_pb = bpy.data.scenes[bkglobals.SCENE_NAME_PLAYBLAST]
            except KeyError:
                # Create scene.
                bpy.ops.scene.new(type="EMPTY")  # changes active scene
                scene_pb = bpy.context.scene
                scene_pb.name = bkglobals.SCENE_NAME_PLAYBLAST

                logger.info(
                    "Created new scene for playblast playback: %s", scene_pb.name
                )
            else:
                logger.info(
                    "Use existing scene for playblast playback: %s", scene_pb.name
                )
                # Change scene.
                context.window.scene = scene_pb

            # Init video sequence editor.
            if not context.scene.sequence_editor:
                context.scene.sequence_editor_create()  # what the hell

            # Setup video sequence editor space.
            if "Video Editing" not in [ws.name for ws in bpy.data.workspaces]:
                scripts_path = bpy.utils.script_paths(use_user=False)[0]
                template_path = "/startup/bl_app_templates_system/Video_Editing/startup.blend"
                ws_filepath = Path(scripts_path + template_path)
                bpy.ops.workspace.append_activate(
                    idname="Video Editing",
                    filepath=ws_filepath.as_posix(),
                )
            else:
                context.window.workspace = bpy.data.workspaces["Video Editing"]

            # Add movie strip
            # load movie strip file in sequence editor
            # in this case we make use of ops.sequencer.movie_strip_add because
            # it provides handy auto placing,would be hard to achieve with
            # context.scene.sequence_editor.sequences.new_movie().
            override = context.copy()
            for window in bpy.context.window_manager.windows:
                screen = window.screen

                for area in screen.areas:
                    if area.type == "SEQUENCE_EDITOR":
                        override["window"] = window
                        override["screen"] = screen
                        override["area"] = area

            bpy.ops.sequencer.movie_strip_add(
                override,
                filepath=scene_orig.kitsu.playblast_file,
                frame_start=context.scene.frame_start,
            )

            # Playback.
            context.scene.frame_current = context.scene.frame_start
            bpy.ops.screen.animation_play()

        return {"FINISHED"}

    def invoke(self, context, event):
        # Initialize comment and playblast task status variable.
        self.comment = ""

        prev_task_status_id = context.scene.kitsu.playblast_task_status_id
        if prev_task_status_id:
            self.task_status = prev_task_status_id
        else:
            # Find todo.
            todo_status = TaskStatus.by_name(bkglobals.PLAYBLAST_DEFAULT_STATUS)
            if todo_status:
                self.task_status = todo_status.id

        return context.window_manager.invoke_props_dialog(self, width=500)

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        row = layout.row(align=True)
        row.prop(self, "task_status", text="Status")
        row = layout.row(align=True)
        row.prop(self, "comment")

    def _upload_playblast(self, context: bpy.types.Context, filepath: Path) -> None:
        # Get shot.
        shot = cache.shot_active_get()
        task_type_name = cache.task_type_active_get().name

        # Get task status 'wip' and task type 'Animation'.
        task_status = TaskStatus.by_id(self.task_status)
        task_type = TaskType.by_name(task_type_name)

        if not task_type:
            raise RuntimeError(
                "Failed to upload playblast. Task type: 'Animation' is missing"
            )

        # Find / get latest task
        task = Task.by_name(shot, task_type)
        if not task:
            # An Entity on the server can have 0 tasks even tough task types exist.
            # We have to create a task first before being able to upload a thumbnail.
            task = Task.new_task(shot, task_type, task_status=task_status)

        # Create a comment
        comment_text = self._gen_comment_text(context, shot)
        comment = task.add_comment(
            task_status,
            comment=comment_text,
        )

        # Add_preview_to_comment
        task.add_preview_to_comment(comment, filepath.as_posix())

        # Preview.set_main_preview()
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



class KITSU_OT_playblast_set_version(bpy.types.Operator):
    bl_idname = "kitsu.anim_set_playblast_version"
    bl_label = "Version"
    bl_property = "versions"
    bl_description = (
        "Sets version of playblast. Warning triangle in ui "
        "indicates that version already exists on disk"
    )

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

        # Update global scene cache version prop.
        context.scene.kitsu.playblast_version = version
        logger.info("Set playblast version to %s", version)

        # Redraw ui.
        util.ui_redraw()

        return {"FINISHED"}

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event) -> Set[str]:
        context.window_manager.invoke_search_popup(self)  # type: ignore
        return {"FINISHED"}


class KITSU_OT_pull_frame_range(bpy.types.Operator):
    bl_idname = "kitsu.pull_frame_range"
    bl_label = "Update Frame Range"
    bl_options = {"REGISTER", "UNDO"}
    bl_description = (
        "Pulls frame range of active shot from the server "
        "and set the current scene's frame range to it"
    )

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return bool(prefs.session_auth(context) and cache.shot_active_get())

    def execute(self, context: bpy.types.Context) -> Set[str]:
        active_shot = cache.shot_active_pull_update()

        if "3d_in" not in active_shot.data or "3d_out" not in active_shot.data:
            self.report(
                {"ERROR"},
                f"Failed to pull frame range. Shot {active_shot.name} missing '3d_in', '3d_out' attribute on server",
            )
            return {"CANCELLED"}

        frame_in = int(active_shot.data["3d_in"])
        frame_out = int(active_shot.data["3d_out"])

        # Check if current frame range matches the one for active shot.
        if (
            frame_in == context.scene.frame_start
            and frame_out == context.scene.frame_end
        ):
            self.report({"INFO"}, f"Frame range already up to date")
            return {"FINISHED"}

        # Update scene frame range.
        context.scene.frame_start = frame_in
        context.scene.frame_end = frame_out

        # Update error prop.
        context.scene.kitsu_error.frame_range = False

        # Log.
        self.report({"INFO"}, f"Updated frame range {frame_in} - {frame_out}")
        return {"FINISHED"}


class KITSU_OT_playblast_increment_playblast_version(bpy.types.Operator):
    bl_idname = "kitsu.anim_increment_playblast_version"
    bl_label = "Add Version Increment"
    bl_description = "Increment the playblast version by one"

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return True

    def execute(self, context: bpy.types.Context) -> Set[str]:

        # Incremenet version.
        version = opsdata.add_playblast_version_increment(context)

        # Update cache_version prop.
        context.scene.kitsu.playblast_version = version

        # Report.
        self.report({"INFO"}, f"Add playblast version {version}")

        util.ui_redraw()
        return {"FINISHED"}


@persistent
def load_post_handler_init_version_model(dummy: Any) -> None:
    opsdata.init_playblast_file_model(bpy.context)


@persistent
def load_post_handler_check_frame_range(dummy: Any) -> None:
    """
    Compare the current scene's frame range with that of the active shot on kitsu.
    If there's a mismatch, set kitsu_error.frame_range -> True. This will enable
    a warning in the Animation Tools Tab UI.
    """
    active_shot = cache.shot_active_get()
    if not active_shot:
        return

    # Pull update for shot.
    cache.shot_active_pull_update()

    if "3d_in" not in active_shot.data or "3d_out" not in active_shot.data:
        logger.warning(
            "Failed to check frame range. Shot %s missing '3d_in', '3d_out' attribute on server",
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


@persistent
def save_pre_handler_clean_overrides(dummy: Any) -> None:
    """
    Removes some Library Override properties that could be accidentally
    created and cause problems.
    """
    for o in bpy.data.objects:
        if not o.override_library:
            continue
        if o.library:
            continue
        override = o.override_library
        props = override.properties
        for prop in props[:]:
            rna_path = prop.rna_path
            if rna_path in ["active_material_index", "active_material"]:
                props.remove(prop)
                linked_value = getattr(override.reference, rna_path)
                setattr(o, rna_path, linked_value)
                o.property_unset(rna_path)


# ---------REGISTER ----------.

classes = [
    KITSU_OT_playblast_create,
    KITSU_OT_playblast_set_version,
    KITSU_OT_playblast_increment_playblast_version,
    KITSU_OT_pull_frame_range,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    # init_playblast_file_model(bpy.context) not working because of restricted context.

    # Handlers.
    bpy.app.handlers.load_post.append(load_post_handler_init_version_model)
    bpy.app.handlers.load_post.append(load_post_handler_check_frame_range)

    bpy.app.handlers.save_pre.append(save_pre_handler_clean_overrides)


def unregister():

    # Clear handlers.
    bpy.app.handlers.load_post.remove(load_post_handler_check_frame_range)
    bpy.app.handlers.load_post.remove(load_post_handler_init_version_model)

    bpy.app.handlers.save_pre.remove(save_pre_handler_clean_overrides)

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
