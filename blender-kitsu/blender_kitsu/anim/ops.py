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
    Shot,
    Task,
    TaskStatus,
    TaskType,
)
from blender_kitsu.anim import opsdata
from bpy.types import Scene

logger = LoggerFactory.getLogger(name=__name__)


class KITSU_OT_anim_create_playblast(bpy.types.Operator):
    bl_idname = "kitsu.anim_create_playblast"
    bl_label = "Create Playblast"
    bl_description = (
        "Creates a openGl render of the window in which the operator was triggered. "
        "Saves the set version to disk and uploads it to kitsu with the specified "
        "comment and task type. Overrides some render settings during export. "
        "Opens webbrowser or vse after playblast if set in addon preferences"
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
            self.report({"ERROR"}, "Failed to crate playblast. Missing task status")
            return {"CANCELLED"}

        shot_active = cache.shot_active_get()

        # Save playblast task status id for next time.
        context.scene.kitsu.playblast_task_status_id = self.task_status

        logger.info("-START- Creating Playblast")

        context.window_manager.progress_begin(0, 2)
        context.window_manager.progress_update(0)

        # ----RENDER AND SAVE PLAYBLAST ------.
        with self.override_render_settings(context):

            # Get output path.
            output_path = Path(context.scene.kitsu.playblast_file)

            # Ensure folder exists.
            Path(context.scene.kitsu.playblast_dir).mkdir(parents=True, exist_ok=True)

            # Make opengl render.
            bpy.ops.render.opengl(animation=True)

        context.window_manager.progress_update(1)

        # ----ULPOAD PLAYBLAST ------.
        self._upload_playblast(context, output_path)

        context.window_manager.progress_update(2)
        context.window_manager.progress_end()

        # Log.
        self.report({"INFO"}, f"Created and uploaded playblast for {shot_active.name}")
        logger.info("-END- Creating Playblast")

        # Redraw ui.
        util.ui_redraw()

        # ---- POST PLAYBLAST -----.

        # Open webbrowser.
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
                blender_version = bpy.app.version  # gets (3, 0, 0)
                blender_version_str = f"{blender_version[0]}.{blender_version[1]}"
                ws_filepath = (
                    Path(bpy.path.abspath(bpy.app.binary_path)).parent
                    / blender_version_str
                    / "scripts/startup/bl_app_templates_system/Video_Editing/startup.blend"
                )
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

        # Get task status 'wip' and task type 'Animation'.
        task_status = TaskStatus.by_id(self.task_status)
        task_type = TaskType.by_name("Animation")

        if not task_type:
            raise RuntimeError(
                "Failed to upload playblast. Task type: 'Animation' is missing"
            )

        # Find / get latest task.
        task = Task.by_name(shot, task_type)
        if not task:
            # turns out a entitiy on server can have 0 tasks even tough task types exist
            # you have to create a task first before being able to upload a thumbnail
            tasks = shot.get_all_tasks()  # list of tasks
            if not tasks:
                task = Task.new_task(shot, task_type, task_status=task_status)
            else:
                task = tasks[-1]

        # Create a comment.
        comment_text = self._gen_comment_text(context, shot)
        comment = task.add_comment(
            task_status,
            comment=comment_text,
        )

        # Add_preview_to_comment.
        preview = task.add_preview_to_comment(comment, filepath.as_posix())

        # Preview.set_main_preview().
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
        # Get first last name for stamp note text.
        session = prefs.session_get(context)
        first_name = session.data.user["first_name"]
        last_name = session.data.user["last_name"]
        # Remember current render settings in order to restore them later.

        # Filepath.
        filepath = rd.filepath

        # Format render settings.
        percentage = rd.resolution_percentage
        file_format = rd.image_settings.file_format
        ffmpeg_constant_rate = rd.ffmpeg.constant_rate_factor
        ffmpeg_codec = rd.ffmpeg.codec
        ffmpeg_format = rd.ffmpeg.format
        ffmpeg_audio_codec = rd.ffmpeg.audio_codec

        # Stamp metadata settings.
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

        # Space data settings.
        shading_type = sps.type
        shading_light = sps.light
        studio_light = sps.studio_light
        color_type = sps.color_type
        background_type = sps.background_type

        show_backface_culling = sps.show_backface_culling
        show_xray = sps.show_xray
        show_shadows = sps.show_shadows
        show_cavity = sps.show_cavity
        show_object_outline = sps.show_object_outline
        show_specular_highlight = sps.show_specular_highlight

        show_gizmo = sp.show_gizmo

        try:
            # Filepath.
            rd.filepath = context.scene.kitsu.playblast_file

            # Format render settings.
            rd.resolution_percentage = 100
            rd.image_settings.file_format = "FFMPEG"
            rd.ffmpeg.constant_rate_factor = "HIGH"
            rd.ffmpeg.codec = "H264"
            rd.ffmpeg.format = "MPEG4"
            rd.ffmpeg.audio_codec = "AAC"

            # Stamp metadata settings.
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

            # Space data settings.
            sps.type = "SOLID"
            sps.light = "STUDIO"
            sps.studio_light = "Default"
            sps.color_type = "MATERIAL"
            sps.background_type = "THEME"

            sps.show_backface_culling = False
            sps.show_xray = False
            sps.show_shadows = False
            sps.show_cavity = False
            sps.show_object_outline = False
            sps.show_specular_highlight = True

            sp.show_gizmo = False

            yield

        finally:
            # Filepath.
            rd.filepath = filepath

            # Return the render settings to normal.
            rd.resolution_percentage = percentage
            rd.image_settings.file_format = file_format
            rd.ffmpeg.codec = ffmpeg_codec
            rd.ffmpeg.constant_rate_factor = ffmpeg_constant_rate
            rd.ffmpeg.format = ffmpeg_format
            rd.ffmpeg.audio_codec = ffmpeg_audio_codec

            # Stamp metadata settings.
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

            # Space data settings.
            sps.type = shading_type
            sps.light = shading_light
            sps.studio_light = studio_light
            sps.color_type = color_type
            sps.background_type = background_type

            sps.show_backface_culling = show_backface_culling
            sps.show_xray = show_xray
            sps.show_shadows = show_shadows
            sps.show_cavity = show_cavity
            sps.show_object_outline = show_object_outline
            sps.show_specular_highlight = show_specular_highlight

            sp.show_gizmo = show_gizmo


class KITSU_OT_anim_set_playblast_version(bpy.types.Operator):
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


class KITSU_OT_anim_pull_frame_range(bpy.types.Operator):
    bl_idname = "kitsu.anim_pull_frame_range"
    bl_label = "Update Frame Range"
    bl_options = {"REGISTER", "UNDO"}
    bl_description = (
        "Pulls frame range of active shot from server "
        "and sets the one of current scene to it"
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


class KITSU_OT_anim_increment_playblast_version(bpy.types.Operator):
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


class KITSU_OT_anim_quick_duplicate(bpy.types.Operator):
    bl_idname = "kitsu.anim_quick_duplicate"
    bl_label = "Quick Duplicate"
    bl_description = (
        "Duplicate the active collection and add it to the "
        "output collection of the current scene "
    )

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        act_coll = context.view_layer.active_layer_collection.collection

        return bool(
            cache.shot_active_get()
            and context.view_layer.active_layer_collection.collection
            and not opsdata.is_item_local(act_coll)
        )

    def execute(self, context: bpy.types.Context) -> Set[str]:

        act_coll = context.view_layer.active_layer_collection.collection
        shot_active = cache.shot_active_get()
        amount = context.window_manager.kitsu.quick_duplicate_amount

        if not act_coll:
            self.report({"ERROR"}, f"No collection selected")
            return {"CANCELLED"}

        # Check if output colletion exists in scene.
        try:
            output_coll = bpy.data.collections[
                opsdata.get_output_coll_name(shot_active)
            ]

        except KeyError:
            self.report(
                {"ERROR"},
                f"Missing output collection: {opsdata.get_output_coll_name(shot_active)}",
            )
            return {"CANCELLED"}

        # Get ref coll.
        ref_coll = opsdata.get_ref_coll(act_coll)

        for i in range(amount):
            # Create library override.
            coll = ref_coll.override_hierarchy_create(
                context.scene, context.view_layer, reference=act_coll
            )

            # Set color tag to be the same.
            coll.color_tag = act_coll.color_tag

            # Link coll in output collection.
            if coll not in list(output_coll.children):
                output_coll.children.link(coll)

        # Report.
        self.report(
            {"INFO"},
            f"Created {amount} Duplicates of: {act_coll.name} and added to {output_coll.name}",
        )

        util.ui_redraw()
        return {"FINISHED"}


class KITSU_OT_anim_check_action_names(bpy.types.Operator):
    bl_idname = "kitsu.anim_check_action_names"
    bl_label = "Check Action Names "
    bl_options = {"REGISTER", "UNDO"}
    bl_description = (
        "Inspects all action names of .blend file and checks "
        "if they follow the Blender Studio naming convention"
    )
    wrong: List[Tuple[bpy.types.Action, str]] = []
    # List of tuples that contains the action on index 0 with the wrong name
    # and the name it should have on index 1.

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return bool(cache.shot_active_get())

    def execute(self, context: bpy.types.Context) -> Set[str]:
        existing_action_names = [a.name for a in bpy.data.actions]
        failed = []
        succeeded = []

        # Rename actions.
        for action, name in self.wrong:
            if name in existing_action_names:
                logger.warning(
                    "Failed to rename action %s to %s. Action with that name already exists",
                    action.name,
                    name,
                )
                failed.append(action)
                continue

            old_name = action.name
            action.name = name
            existing_action_names.append(action.name)
            succeeded.append(action)
            logger.info("Renamed action %s to %s", old_name, action.name)

        # Report.
        report_str = f"Renamed actions: {len(succeeded)}"
        report_state = "INFO"
        if failed:
            report_state = "WARNING"
            report_str += f" | Failed: {len(failed)}"

        self.report(
            {report_state},
            report_str,
        )

        # Clear action names cache.
        opsdata.action_names_cache.clear()

        return {"FINISHED"}

    def invoke(self, context, event):
        shot_active = cache.shot_active_get()
        self.wrong.clear()
        no_action = []
        correct = []

        # Clear action names cache.
        opsdata.action_names_cache.clear()
        opsdata.action_names_cache.extend([a.name for a in bpy.data.actions])

        # Find all asset collections in .blend.
        asset_colls = opsdata.find_asset_collections()

        if not asset_colls:
            self.report(
                {"WARNING"},
                f"Failed to find any asset collections",
            )
            return {"CANCELLED"}

        # Find rig of each asset collection.
        asset_rigs: List[Tuple[bpy.types.Collection, bpy.types.Armature]] = []
        for coll in asset_colls:
            rig = opsdata.find_rig(coll, log=False)
            if rig:
                asset_rigs.append((coll, rig))

        if not asset_rigs:
            self.report(
                {"WARNING"},
                f"Failed to find any valid rigs",
            )
            return {"CANCELLED"}

        # For each rig check the current action name if it matches the convention.
        for coll, rig in asset_rigs:
            if not rig.animation_data or not rig.animation_data.action:
                logger.info("%s has no animation data", rig.name)
                no_action.append(rig)
                continue

            action_name_should = opsdata.gen_action_name(rig, coll, shot_active)
            action_name_is = rig.animation_data.action.name

            # If action name does not follow convention append it to wrong list.
            if action_name_is != action_name_should:
                logger.warning(
                    "Action %s should be named %s", action_name_is, action_name_should
                )
                self.wrong.append((rig.animation_data.action, action_name_should))

                # Extend action_names_cache list so any follow up items in loop can
                # access that information and adjust postfix accordingly.
                opsdata.action_names_cache.append(action_name_should)
                continue

            # Action name of rig is correct.
            correct.append(rig)

        if not self.wrong:
            self.report({"INFO"}, "All actions names are correct")
            return {"FINISHED"}

        self.report(
            {"INFO"},
            f"Checked Rigs: {len(asset_rigs)} | Wrong Actions {len(correct)} | Correct Actions: {len(correct)} | No Actions: {len(no_action)}",
        )
        return context.window_manager.invoke_props_dialog(self, width=500)

    def draw(self, context):
        layout = self.layout

        for action, name in self.wrong:
            row = layout.row()
            row.label(text=action.name)
            row.label(text="", icon="FORWARD")
            row.label(text=name)


class KITSU_OT_anim_update_output_coll(bpy.types.Operator):
    bl_idname = "kitsu.anim_update_output_coll"
    bl_label = "Update Output Collection"
    bl_options = {"REGISTER", "UNDO"}
    bl_description = (
        "Scans scene for any collections that are not in output collection yet"
    )

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        active_shot = cache.shot_active_get()
        output_coll_name = opsdata.get_output_coll_name(active_shot)
        try:
            output_coll = bpy.data.collections[output_coll_name]
        except KeyError:
            output_coll = None

        return bool(active_shot and output_coll)

    def execute(self, context: bpy.types.Context) -> Set[str]:
        active_shot = cache.shot_active_get()
        output_coll_name = opsdata.get_output_coll_name(active_shot)
        output_coll = bpy.data.collections[output_coll_name]
        asset_colls = opsdata.find_asset_collections_in_scene(context.scene)
        missing: List[bpy.types.Collection] = []
        output_coll_childs = list(opsdata.traverse_collection_tree(output_coll))

        # Check if all found asset colls are in output coll.
        for coll in asset_colls:
            if coll in output_coll_childs:
                continue
            missing.append(coll)

        # Only take parent colls.
        childs = []
        for i in range(len(missing)):
            coll = missing[i]
            coll_childs = list(opsdata.traverse_collection_tree(coll))
            for j in range(i + 1, len(missing)):
                coll_comp = missing[j]
                if coll_comp in coll_childs:
                    childs.append(coll_comp)

        parents = [coll for coll in missing if coll not in childs]
        for coll in parents:
            output_coll.children.link(coll)
            logger.info("%s linked in %s", coll.name, output_coll.name)

        self.report(
            {"INFO"},
            f"Found Asset Collections: {len(asset_colls)} | Added to output collection: {len(parents)}",
        )
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
    created and could cause problems.
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
            if rna_path in ['active_material_index', 'active_material']:
                props.remove(prop)
                linked_value = getattr(override.reference, rna_path)
                setattr(o, rna_path, linked_value)
                o.property_unset(rna_path)

# ---------REGISTER ----------.

classes = [
    KITSU_OT_anim_create_playblast,
    KITSU_OT_anim_set_playblast_version,
    KITSU_OT_anim_increment_playblast_version,
    KITSU_OT_anim_pull_frame_range,
    KITSU_OT_anim_quick_duplicate,
    KITSU_OT_anim_check_action_names,
    KITSU_OT_anim_update_output_coll,
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
