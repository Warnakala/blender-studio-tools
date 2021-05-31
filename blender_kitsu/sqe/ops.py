import contextlib
import colorsys
import random
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple, Any

import bpy

from blender_kitsu import gazu, cache, util, prefs, bkglobals
from blender_kitsu.sqe import push, pull, checkstrip, opsdata, checksqe

from blender_kitsu.logger import LoggerFactory
from blender_kitsu.types import (
    Cache,
    Sequence,
    Shot,
    Task,
    TaskStatus,
    TaskType,
)

logger = LoggerFactory.getLogger(name=__name__)


class KITSU_OT_sqe_push_shot_meta(bpy.types.Operator):
    """
    Operator that pushes metadata of all selected sequencce strips to sevrer
    after performing various checks. Metadata is saved in strip.kitsu.
    """

    bl_idname = "kitsu.sqe_push_shot_meta"
    bl_label = "Push Shot Metadata"
    bl_options = {"INTERNAL"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return bool(prefs.session_auth(context))

    def execute(self, context: bpy.types.Context) -> Set[str]:
        succeeded = []
        failed = []
        logger.info("-START- Pushing Metadata")

        # begin progress update
        selected_sequences = context.selected_sequences
        if not selected_sequences:
            selected_sequences = context.scene.sequence_editor.sequences_all

        context.window_manager.progress_begin(0, len(selected_sequences))

        # clear cache
        Cache.clear_all()

        for idx, strip in enumerate(selected_sequences):
            context.window_manager.progress_update(idx)

            if not checkstrip.is_valid_type(strip):
                # failed.append(strip)
                continue

            # only if strip is linked to sevrer
            if not checkstrip.is_linked(strip):
                # failed.append(strip)
                continue

            # check if shot is still available by id
            shot = checkstrip.shot_exists_by_id(strip, clear_cache=False)
            if not shot:
                failed.append(strip)
                continue

            # push update to shot
            push.shot_meta(strip, shot)
            succeeded.append(strip)

        # end progress update
        context.window_manager.progress_update(len(selected_sequences))
        context.window_manager.progress_end()

        # report
        report_str = f"Pushed Metadata of {len(succeeded)} Shots"
        report_state = "INFO"
        if failed:
            report_state = "WARNING"
            report_str += f" | Failed: {len(failed)}"

        self.report(
            {report_state},
            report_str,
        )

        # log
        logger.info("-END- Pushing Metadata")

        return {"FINISHED"}


class KITSU_OT_sqe_push_new_shot(bpy.types.Operator):
    """
    Operator that creates a new shot based on all selected sequencce strips to sevrer
    after performing various checks. Does not create shot if already exists to sevrer .
    """

    bl_idname = "kitsu.sqe_push_new_shot"
    bl_label = "Submit New Shot"
    bl_description = "Creates a new shot based on all selected sequencce strips on server. Checks if shot already exists on sevrer"

    confirm: bpy.props.BoolProperty(name="confirm")

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        # needs to be logged in, active project
        nr_of_shots = len(context.selected_sequences)
        if nr_of_shots == 1:
            strip = context.scene.sequence_editor.active_strip
            return bool(
                prefs.session_auth(context)
                and cache.project_active_get()
                and strip.kitsu.sequence_name
                and strip.kitsu.shot_name
            )

        return bool(prefs.session_auth(context) and cache.project_active_get())

    def execute(self, context: bpy.types.Context) -> Set[str]:

        if not self.confirm:
            self.report({"WARNING"}, "Submit new shots aborted.")
            return {"CANCELLED"}

        project_active = cache.project_active_get()
        succeeded = []
        failed = []
        logger.info("-START- Submitting new shots to: %s", project_active.name)

        # clear cache
        Cache.clear_all()

        # begin progress update
        selected_sequences = context.selected_sequences
        if not selected_sequences:
            selected_sequences = context.scene.sequence_editor.sequences_all

        context.window_manager.progress_begin(0, len(selected_sequences))

        for idx, strip in enumerate(selected_sequences):
            context.window_manager.progress_update(idx)

            if not checkstrip.is_valid_type(strip):
                # failed.append(strip)
                continue

            # check if user initialized shot
            if not checkstrip.is_initialized(strip):
                # failed.append(strip)
                continue

            # check if strip is already linked to sevrer
            if checkstrip.is_linked(strip):
                failed.append(strip)
                continue

            # check if user provided enough info
            if not checkstrip.has_meta(strip):
                failed.append(strip)
                continue

            # check if seq already to sevrer  > create it
            zseq = checkstrip.seq_exists_by_name(
                strip, project_active, clear_cache=False
            )
            if not zseq:
                zseq = push.new_sequence(strip, project_active)

            # check if shot already to sevrer  > create it
            shot = checkstrip.shot_exists_by_name(
                strip, project_active, zseq, clear_cache=False
            )
            if shot:
                failed.append(strip)
                continue

            # push update to shot
            shot = push.new_shot(strip, zseq, project_active)
            pull.shot_meta(strip, shot)
            succeeded.append(strip)

            # rename strip
            strip.name = shot.name

        # end progress update
        context.window_manager.progress_update(len(selected_sequences))
        context.window_manager.progress_end()

        # clear cache
        Cache.clear_all()

        # report
        report_str = f"Submitted {len(succeeded)} new shots"
        report_state = "INFO"
        if failed:
            report_state = "WARNING"
            report_str += f" | Failed: {len(failed)}"

        self.report(
            {report_state},
            report_str,
        )

        # log
        logger.info("-END- Submitting new shots to: %s", project_active.name)
        util.ui_redraw()
        return {"FINISHED"}

    def invoke(self, context, event):
        self.confirm = False
        return context.window_manager.invoke_props_dialog(self, width=500)

    def draw(self, context):
        project_active = cache.project_active_get()
        selected_sequences = context.selected_sequences

        if not selected_sequences:
            selected_sequences = context.scene.sequence_editor.sequences_all

        strips_to_submit = [
            s
            for s in selected_sequences
            if s.kitsu.initialized
            and not s.kitsu.linked
            and s.kitsu.shot_name
            and s.kitsu.sequence_name
        ]

        if len(selected_sequences) > 1:
            noun = "%i Shots" % len(strips_to_submit)
        else:
            noun = "this Shot"

        # UI
        layout = self.layout

        # Production
        row = layout.row()
        row.label(text=f"Production: {project_active.name}", icon="FILEBROWSER")

        # confirm dialog
        col = layout.column()
        col.prop(
            self,
            "confirm",
            text="Submit %s to server. Will skip shots if they already exist."
            % (noun.lower()),
        )


class KITSU_OT_sqe_push_new_sequence(bpy.types.Operator):
    """
    Operator with input dialog that creates a new sequence on server.
    Does not create sequence if already exists on server.
    """

    bl_idname = "kitsu.sqe_push_new_sequence"
    bl_label = "Submit New Sequence"
    bl_description = (
        "Creates new sequence on server. Will skip if sequence already exists."
    )

    sequence_name: bpy.props.StringProperty(
        name="Name", default="", description="Name of new sequence"
    )
    confirm: bpy.props.BoolProperty(name="confirm")

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        # needs to be logged in, active project
        return bool(prefs.session_auth(context) and cache.project_active_get())

    def execute(self, context: bpy.types.Context) -> Set[str]:

        if not self.confirm:
            self.report({"WARNING"}, "Submit new sequence aborted.")
            return {"CANCELLED"}

        if not self.sequence_name:
            self.report({"WARNING"}, "Invalid sequence name.")
            return {"CANCELLED"}

        project_active = cache.project_active_get()

        sequence = project_active.get_sequence_by_name(self.sequence_name)

        if sequence:
            self.report(
                {"WARNING"},
                f"Sequence: {sequence.name} already exists on server.",
            )
            return {"CANCELLED"}

        # create sequence
        sequence = project_active.create_sequence(self.sequence_name)

        # clear cache
        Cache.clear_all()

        self.report(
            {"INFO"},
            f"Submitted new sequence: {sequence.name}",
        )
        logger.info("Submitted new sequence: %s", sequence.name)
        return {"FINISHED"}

    def invoke(self, context, event):
        self.confirm = False
        return context.window_manager.invoke_props_dialog(self, width=300)

    def draw(self, context):
        # UI
        layout = self.layout
        project_active = cache.project_active_get()

        # Production
        row = layout.row()
        row.label(text=f"Production: {project_active.name}", icon="FILEBROWSER")

        # sequence name
        row = layout.row()
        row.prop(self, "sequence_name")

        # confirm dialog
        col = layout.column()
        col.prop(
            self,
            "confirm",
            text="Submit sequence to server. Will skip if already exists.",
        )


class KITSU_OT_sqe_init_strip(bpy.types.Operator):
    """
    Operator that initializes a regular sequence strip to a 'kitsu' shot.
    Only sets strip.kitsu.initialized = True. But this is required for further
    operations and to  differentiate between regular sequence strip and kitsu shot strip.
    """

    bl_idname = "kitsu.sqe_init_strip"
    bl_label = "Initialize Shot"
    bl_description = "Adds required shot metadata to selecetd strips"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return True

    def execute(self, context: bpy.types.Context) -> Set[str]:
        succeeded = []
        failed = []
        logger.info("-START- Initializing shots")

        selected_sequences = context.selected_sequences
        if not selected_sequences:
            selected_sequences = context.scene.sequence_editor.sequences_all

        for strip in selected_sequences:

            if not checkstrip.is_valid_type(strip):
                # failed.append(strip)
                continue

            if strip.kitsu.initialized:
                logger.info("%s already initialized.", strip.name)
                # failed.append(strip)
                continue

            strip.kitsu.initialized = True
            succeeded.append(strip)
            logger.info("Initiated strip: %s as shot.", strip.name)

        # report
        report_str = f"Initiated {len(succeeded)} shots"
        report_state = "INFO"
        if failed:
            report_state = "WARNING"
            report_str += f" | Failed: {len(failed)}"

        self.report(
            {report_state},
            report_str,
        )

        # log
        logger.info("-END- Initializing shots")
        util.ui_redraw()

        return {"FINISHED"}


class KITSU_OT_sqe_link_sequence(bpy.types.Operator):
    """
    Gets all sequences that are available in server for active production and let's user select. Invokes a search Popup (enum_prop) on click.
    """

    bl_idname = "kitsu.sqe_link_sequence"
    bl_label = "Link Sequence"
    bl_options = {"REGISTER", "UNDO"}
    bl_property = "enum_prop"

    enum_prop: bpy.props.EnumProperty(
        items=cache.get_sequences_enum_list,
    )  # type: ignore

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        strip = context.scene.sequence_editor.active_strip
        return bool(
            prefs.session_auth(context)
            and cache.project_active_get()
            and strip
            and context.selected_sequences
            and checkstrip.is_valid_type(strip)
        )

    def execute(self, context: bpy.types.Context) -> Set[str]:
        strip = context.scene.sequence_editor.active_strip
        sequence_id = self.enum_prop
        if not sequence_id:
            return {"CANCELLED"}

        # set sequence properties
        zseq = Sequence.by_id(sequence_id)
        strip.kitsu.sequence_name = zseq.name
        strip.kitsu.sequence_id = zseq.id

        util.ui_redraw()
        return {"FINISHED"}

    def invoke(self, context, event):
        context.window_manager.invoke_search_popup(self)
        return {"FINISHED"}


class KITSU_OT_sqe_link_shot(bpy.types.Operator):
    """
    Operator that invokes ui which shows user all available shots on server.
    It is used to 'link' a seqeunce strip to an alredy existent shot on server.
    Fills out all metadata after selecting shot.
    """

    bl_idname = "kitsu.sqe_link_shot"
    bl_label = "Link Shot"
    bl_description = (
        "Adds required shot metadata to selecetd strip based on data from server."
    )
    bl_options = {"REGISTER", "UNDO"}

    sequence_enum: bpy.props.EnumProperty(items=cache.get_sequences_enum_list, name="Sequence")  # type: ignore
    shots_enum: bpy.props.EnumProperty(items=opsdata.get_shots_enum_for_link_shot_op, name="Shot")  # type: ignore
    use_url: bpy.props.BoolProperty(
        name="Use URL",
        description="Use URL of shot on server to initiate strip. Paste complete URL.",
    )
    url: bpy.props.StringProperty(
        name="URL",
        description="Complete URL of shot on server that will be used to initiate strip",
        default="",
    )

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        strip = context.scene.sequence_editor.active_strip
        return bool(
            prefs.session_auth(context)
            and cache.project_active_get()
            and strip
            and context.selected_sequences
            and checkstrip.is_valid_type(strip)
        )

    def execute(self, context: bpy.types.Context) -> Set[str]:
        strip = context.scene.sequence_editor.active_strip

        shot_id = self.shots_enum

        # by url
        if self.use_url:
            # http://192.168.178.80/productions/4dda1c36-1f49-44c7-98c9-93b40ea37dcd/shots/5e69e2e0-c3c8-4fc2-a4a3-f18151adf9dc
            split = self.url.split("/")
            shot_id = split[-1]

        # by shot enum
        else:
            shot_id = self.shots_enum
            if not shot_id:
                self.report({"WARNING"}, "Invalid selection. Please choose a shot.")
                return {"CANCELLED"}

        # check if id availalbe on server (mainly for url option)
        try:
            shot = Shot.by_id(shot_id)

        except (TypeError, gazu.exception.ServerErrorException):
            self.report({"WARNING"}, "Invalid URL: %s" % self.url)
            return {"CANCELLED"}

        except gazu.exception.RouteNotFoundException:
            self.report({"WARNING"}, "ID not found on server: %s" % shot_id)
            return {"CANCELLED"}

        # pull shot meta
        pull.shot_meta(strip, shot)

        # rename strip
        strip.name = shot.name

        # log
        t = "Linked strip: %s to shot: %s with ID: %s" % (
            strip.name,
            shot.name,
            shot.id,
        )
        logger.info(t)
        self.report({"INFO"}, t)
        util.ui_redraw()

        return {"FINISHED"}

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event) -> Set[str]:
        if context.window_manager.clipboard:
            self.url = context.window_manager.clipboard

        return context.window_manager.invoke_props_dialog(  # type: ignore
            self, width=400
        )

    def draw(self, context):
        layout = self.layout

        row = layout.row()
        row.prop(self, "use_url")
        if self.use_url:
            row = layout.row()
            row.prop(self, "url", text="")
        else:
            row = layout.row()
            row.prop(self, "sequence_enum")
            row = layout.row()
            row.prop(self, "shots_enum")
            row = layout.row()


class KITSU_OT_sqe_multi_edit_strip(bpy.types.Operator):
    """"""

    bl_idname = "kitsu.sqe_multi_edit_strip"
    bl_label = "Multi Edit Strip"
    bl_options = {"INTERNAL"}
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        # only if all selected strips are initialized but not linked
        # and they all have the same sequence name
        sel_shots = context.selected_sequences
        nr_of_shots = len(sel_shots)

        if not nr_of_shots > 1:
            return False

        seq_name = sel_shots[0].kitsu.sequence_name
        for s in sel_shots:
            if (
                s.kitsu.linked
                or not s.kitsu.initialized
                or not checkstrip.is_valid_type(s)
            ):
                return False
            if s.kitsu.sequence_name != seq_name:
                return False
        return True

    def execute(self, context: bpy.types.Context) -> Set[str]:
        addon_prefs = prefs.addon_prefs_get(context)
        shot_counter_increment = addon_prefs.shot_counter_increment
        shot_counter_digits = addon_prefs.shot_counter_digits
        shot_counter_start = context.window_manager.shot_counter_start
        shot_pattern = addon_prefs.shot_pattern
        strip = context.scene.sequence_editor.active_strip
        sequence = context.window_manager.sequence_enum
        var_project = (
            addon_prefs.var_project_custom
            if context.window_manager.var_use_custom_project
            else context.window_manager.var_project_active
        )
        var_sequence = (
            context.window_manager.var_sequence_custom
            if context.window_manager.var_use_custom_seq
            else sequence
        )
        succeeded = []
        failed = []
        logger.info("-START- Multi Edit Shot")

        # sort sequence after frame in
        selected_sequences = context.selected_sequences
        selected_sequences = sorted(
            selected_sequences, key=lambda x: x.frame_final_start
        )

        for idx, strip in enumerate(selected_sequences):

            # gen data for resolver
            counter_number = shot_counter_start + (shot_counter_increment * idx)
            counter = str(counter_number).rjust(shot_counter_digits, "0")
            var_lookup_table = {
                "Sequence": var_sequence,
                "Project": var_project,
                "Counter": counter,
            }

            # run shot name resolver
            shot = opsdata.resolve_pattern(shot_pattern, var_lookup_table)

            # set metadata
            strip.kitsu.sequence_name = sequence
            strip.kitsu.shot_name = shot

            succeeded.append(strip)
            logger.info(
                "Strip: %s Assign sequence: %s Assign shot: %s"
                % (strip.name, sequence, shot)
            )

        # report
        report_str = f"Assigned {len(succeeded)} Shots"
        report_state = "INFO"
        if failed:
            report_state = "WARNING"
            report_str += f" | Failed: {len(failed)}"

        self.report(
            {report_state},
            report_str,
        )

        # log
        logger.info("-END- Multi Edit Shot")
        util.ui_redraw()
        return {"FINISHED"}


class KITSU_OT_sqe_pull_shot_meta(bpy.types.Operator):
    """
    Operator that pulls metadata of all selected sequencce strips from server
    after performing various checks. Metadata will be saved in strip.kitsu.
    """

    bl_idname = "kitsu.sqe_pull_shot_meta"
    bl_label = "Pull Shot Metadata"
    bl_options = {"INTERNAL"}
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return bool(prefs.session_auth(context))

    def execute(self, context: bpy.types.Context) -> Set[str]:
        succeeded = []
        failed = []
        logger.info("-START- Pulling shot metadata")

        # begin progress update
        selected_sequences = context.selected_sequences
        if not selected_sequences:
            selected_sequences = context.scene.sequence_editor.sequences_all

        context.window_manager.progress_begin(0, len(selected_sequences))

        # clear cache once
        Cache.clear_all()

        for idx, strip in enumerate(selected_sequences):
            context.window_manager.progress_update(idx)

            if not checkstrip.is_valid_type(strip):
                # failed.append(strip)
                continue

            # only if strip is linked to sevrer
            if not checkstrip.is_linked(strip):
                # failed.append(strip)
                continue

            # check if shot is still available by id
            shot = checkstrip.shot_exists_by_id(strip, clear_cache=False)
            if not shot:
                failed.append(strip)
                continue

            # push update to shot
            pull.shot_meta(strip, shot, clear_cache=False)
            succeeded.append(strip)

        # end progress update
        context.window_manager.progress_update(len(selected_sequences))
        context.window_manager.progress_end()

        # report
        report_str = f"Pulled metadata for {len(succeeded)} shots"
        report_state = "INFO"
        if failed:
            report_state = "WARNING"
            report_str += f" | Failed: {len(failed)}"

        self.report(
            {report_state},
            report_str,
        )

        # log
        logger.info("-END- Pulling shot metadata")
        util.ui_redraw()
        return {"FINISHED"}


class KITSU_OT_sqe_uninit_strip(bpy.types.Operator):
    """
    Operator that deletes all  metadata of all selected sequencce strips
    after performing various checks. It does NOT change anything on server.
    """

    bl_idname = "kitsu.sqe_uninit_strip"
    bl_label = "Uninitialize"
    bl_description = "Uninitialize selecetd strips. Only affects Sequence Editor. "
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return bool(context.selected_sequences)

    def execute(self, context: bpy.types.Context) -> Set[str]:

        failed: List[bpy.types.Sequence] = []
        succeeded: List[bpy.types.Sequence] = []
        logger.info("-START- Uninitializing strips")

        for strip in context.selected_sequences:

            if not checkstrip.is_valid_type(strip):
                # failed.append(strip)
                continue

            if not checkstrip.is_initialized(strip):
                # failed.append(strip)
                continue

            if checkstrip.is_linked(strip):
                # failed.append(strip)
                continue

            # clear kitsu properties
            strip.kitsu.clear()
            succeeded.append(strip)
            logger.info("Uninitialized strip: %s", strip.name)

        # report
        report_str = f"Uninitialized {len(succeeded)} strips"
        report_state = "INFO"
        if failed:
            report_state = "WARNING"
            report_str += f" | Failed: {len(failed)}"

        self.report(
            {report_state},
            report_str,
        )

        # log
        logger.info("-END- Uninitializing strips")
        util.ui_redraw()
        return {"FINISHED"}


class KITSU_OT_sqe_unlink_shot(bpy.types.Operator):
    """
    Operator that deletes all  metadata of all selected sequencce strips
    after performing various checks. It does NOT change anything on server.
    """

    bl_idname = "kitsu.sqe_unlink_shot"
    bl_label = "Unlink"
    bl_description = (
        "Deletes link to the server of selecetd shots. Only affects Sequence Editor."
    )
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return bool(context.selected_sequences)

    def execute(self, context: bpy.types.Context) -> Set[str]:
        failed: List[bpy.types.Sequence] = []
        succeeded: List[bpy.types.Sequence] = []
        logger.info("-START- Unlinking shots")

        for strip in context.selected_sequences:

            if not checkstrip.is_valid_type(strip):
                # failed.append(strip)
                continue

            if not checkstrip.is_initialized(strip):
                # failed.append(strip)
                continue

            if not checkstrip.is_linked(strip):
                # failed.append(strip)
                continue

            # clear kitsu properties
            shot_name = strip.kitsu.shot_name
            strip.kitsu.unlink()
            succeeded.append(strip)
            logger.info("Unlinked shot: %s", shot_name)

        # report
        report_str = f"Unlinked {len(succeeded)} shots"
        report_state = "INFO"
        if failed:
            report_state = "WARNING"
            report_str += f" | Failed: {len(failed)}"

        self.report(
            {report_state},
            report_str,
        )

        # log
        logger.info("-END- Unlinking shots")
        util.ui_redraw()
        return {"FINISHED"}


class KITSU_OT_sqe_push_del_shot(bpy.types.Operator):
    """
    Operator that deletes all  metadata of all selected sequencce strips
    after performing various checks. It does NOT change anything on server.
    """

    bl_idname = "kitsu.sqe_push_del_shot"
    bl_label = "Delete Shot"
    bl_description = "Deletes shot on server and clears metadata of selected strips."

    confirm: bpy.props.BoolProperty(name="Confirm")

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return bool(prefs.session_auth(context) and context.selected_sequences)

    def execute(self, context: bpy.types.Context) -> Set[str]:
        if not self.confirm:
            self.report({"WARNING"}, "Push delete aborted.")
            return {"CANCELLED"}

        succeeded = []
        failed = []
        logger.info("-START- Deleting shots")

        # clear cache
        Cache.clear_all()

        # begin progress update
        selected_sequences = context.selected_sequences

        context.window_manager.progress_begin(0, len(selected_sequences))

        for idx, strip in enumerate(selected_sequences):
            context.window_manager.progress_update(idx)

            if not checkstrip.is_valid_type(strip):
                # failed.append(strip)
                continue

            # check if strip is already linked to sevrer
            if not checkstrip.is_linked(strip):
                # failed.append(strip)
                continue

            # check if shot still exists to sevrer
            shot = checkstrip.shot_exists_by_id(strip, clear_cache=False)
            if not shot:
                failed.append(strip)
                continue

            # delete shot
            push.delete_shot(strip, shot)
            succeeded.append(strip)

        # end progress update
        context.window_manager.progress_update(len(selected_sequences))
        context.window_manager.progress_end()

        # report
        report_str = f"Deleted {len(succeeded)} shots"
        report_state = "INFO"
        if failed:
            report_state = "WARNING"
            report_str += f" | Failed: {len(failed)}"

        self.report(
            {report_state},
            report_str,
        )

        # log
        logger.info("-END- Deleting shots")
        util.ui_redraw()
        return {"FINISHED"}

    def invoke(self, context, event):
        self.confirm = False
        return context.window_manager.invoke_props_dialog(self, width=500)

    def draw(self, context):
        layout = self.layout
        col = layout.column()

        selshots = context.selected_sequences
        strips_to_delete = [s for s in selshots if s.kitsu.linked]

        if len(selshots) > 1:
            noun = "%i shots" % len(strips_to_delete)
        else:
            noun = "this shot"

        col.prop(
            self,
            "confirm",
            text="Delete %s on server." % noun,
        )


class KITSU_OT_sqe_set_thumbnail_task_type(bpy.types.Operator):
    """
    Gets all sequences that are available in server for active production and let's user select. Invokes a search Popup (enum_prop) on click.
    """

    bl_idname = "kitsu.set_thumbnail_task_type"
    bl_label = "Set Thumbnail Task Type"
    bl_options = {"INTERNAL"}
    bl_property = "enum_prop"

    enum_prop: bpy.props.EnumProperty(items=cache.get_shot_task_types_enum)  # type: ignore

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return bool(prefs.session_auth(context) and cache.project_active_get())

    def execute(self, context: bpy.types.Context) -> Set[str]:

        # task type selected by user
        task_type_id = self.enum_prop

        if not task_type_id:
            return {"CANCELLED"}

        task_type = TaskType.by_id(task_type_id)

        # update scene properties
        context.scene.kitsu.task_type_thumbnail_name = task_type.name
        context.scene.kitsu.task_type_thumbnail_id = task_type_id

        util.ui_redraw()
        return {"FINISHED"}

    def invoke(self, context, event):
        context.window_manager.invoke_search_popup(self)
        return {"FINISHED"}


class KITSU_OT_sqe_set_sqe_render_task_type(bpy.types.Operator):
    """
    Gets all sequences that are available in server for active production and let's user select. Invokes a search Popup (enum_prop) on click.
    """

    bl_idname = "kitsu.set_sqe_render_task_type"
    bl_label = "Set Sqe Render Task Type"
    bl_options = {"INTERNAL"}
    bl_property = "enum_prop"

    enum_prop: bpy.props.EnumProperty(items=cache.get_shot_task_types_enum)  # type: ignore

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return bool(prefs.session_auth(context) and cache.project_active_get())

    def execute(self, context: bpy.types.Context) -> Set[str]:

        # task type selected by user
        task_type_id = self.enum_prop

        if not task_type_id:
            return {"CANCELLED"}

        task_type = TaskType.by_id(task_type_id)

        # update scene properties
        context.scene.kitsu.task_type_sqe_render_name = task_type.name
        context.scene.kitsu.task_type_sqe_render_id = task_type_id

        util.ui_redraw()
        return {"FINISHED"}

    def invoke(self, context, event):
        context.window_manager.invoke_search_popup(self)
        return {"FINISHED"}


class KITSU_OT_sqe_push_thumbnail(bpy.types.Operator):
    """
    Operator that takes thumbnail of all selected sequencce strips and saves them
    in tmp directory. Loops through all thumbnails and uploads them to sevrer .
    uses Animation task type to create task and set main thumbnail in wip state.
    """

    bl_idname = "kitsu.sqe_push_thumbnail"
    bl_label = "Push Thumbnail"
    bl_options = {"INTERNAL"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return bool(
            prefs.session_auth(context) and context.scene.kitsu.task_type_thumbnail_id
        )

    def execute(self, context: bpy.types.Context) -> Set[str]:
        nr_of_strips: int = len(context.selected_sequences)
        do_multishot: bool = nr_of_strips > 1
        failed = []
        upload_queue: List[Path] = []  # will be used as successed list
        # get task stype by id from user selection enum property
        task_type = TaskType.by_id(context.scene.kitsu.task_type_thumbnail_id)

        logger.info("-START- Pushing shot thumbnails")

        # clear cache
        Cache.clear_all()

        with self.override_render_settings(context):
            with self.temporary_current_frame(context) as original_curframe:

                # ----RENDER AND SAVE THUMBNAILS ------

                # begin first progress update
                selected_sequences = context.selected_sequences
                if not selected_sequences:
                    selected_sequences = context.scene.sequence_editor.sequences_all

                context.window_manager.progress_begin(0, len(selected_sequences))

                for idx, strip in enumerate(selected_sequences):
                    context.window_manager.progress_update(idx)

                    if not checkstrip.is_valid_type(strip):
                        # failed.append(strip)
                        continue

                    # only if strip is linked to sevrer
                    if not checkstrip.is_linked(strip):
                        # failed.append(strip)
                        continue

                    # check if shot is still available by id
                    shot = checkstrip.shot_exists_by_id(strip, clear_cache=False)
                    if not shot:
                        failed.append(strip)
                        continue

                    # if only one strip is selected,
                    if not do_multishot:
                        # if active strip is not contained in the current frame, use middle frame of active strip
                        # otherwise don't change frame and use current one
                        if not checkstrip.contains(strip, original_curframe):
                            self.set_middle_frame(context, strip)
                    else:
                        self.set_middle_frame(context, strip)

                    path = self.make_thumbnail(context, strip)
                    upload_queue.append(path)

                # end first progress update
                context.window_manager.progress_update(len(upload_queue))
                context.window_manager.progress_end()

        # ----ULPOAD THUMBNAILS ------

        # begin second progress update
        context.window_manager.progress_begin(0, len(upload_queue))

        # process thumbnail queue
        for idx, filepath in enumerate(upload_queue):
            context.window_manager.progress_update(idx)
            opsdata.upload_preview(
                context, filepath, task_type, comment="Update thumbnail"
            )

        # end second progress update
        context.window_manager.progress_update(len(upload_queue))
        context.window_manager.progress_end()

        # report
        report_str = f"Created thumbnails for {len(upload_queue)} shots"
        report_state = "INFO"
        if failed:
            report_state = "WARNING"
            report_str += f" | Failed: {len(failed)}"

        self.report(
            {report_state},
            report_str,
        )

        # log
        logger.info("-END- Pushing shot thumbnails")
        return {"FINISHED"}

    def make_thumbnail(
        self, context: bpy.types.Context, strip: bpy.types.Sequence
    ) -> Path:
        bpy.ops.render.render()
        file_name = f"{strip.kitsu.shot_id}_{str(context.scene.frame_current)}.jpg"
        path = self._save_render(bpy.data.images["Render Result"], file_name)
        logger.info(
            f"Saved thumbnail of shot {strip.kitsu.shot_name} to {path.as_posix()}"
        )
        return path

    def _save_render(self, datablock: bpy.types.Image, file_name: str) -> Path:
        """Save the current render image to disk"""

        addon_prefs = prefs.addon_prefs_get(bpy.context)
        folder_name = addon_prefs.thumbnail_dir

        # Ensure folder exists
        folder_path = Path(folder_name).absolute()
        folder_path.mkdir(parents=True, exist_ok=True)

        path = folder_path.joinpath(file_name)
        datablock.save_render(str(path))
        return path.absolute()

    @contextlib.contextmanager
    def override_render_settings(self, context, thumbnail_width=256):
        """Overrides the render settings for thumbnail size in a 'with' block scope."""

        rd = context.scene.render

        # Remember current render settings in order to restore them later.
        percentage = rd.resolution_percentage
        file_format = rd.image_settings.file_format
        quality = rd.image_settings.quality

        try:
            # Set the render settings to thumbnail size.
            # Update resolution % instead of the actual resolution to scale text strips properly.
            rd.resolution_percentage = round(thumbnail_width * 100 / rd.resolution_x)
            rd.image_settings.file_format = "JPEG"
            rd.image_settings.quality = 80
            yield

        finally:
            # Return the render settings to normal.
            rd.resolution_percentage = percentage
            rd.image_settings.file_format = file_format
            rd.image_settings.quality = quality

    @contextlib.contextmanager
    def temporary_current_frame(self, context):
        """Allows the context to set the scene current frame, restores it on exit.

        Yields the initial current frame, so it can be used for reference in the context.
        """
        current_frame = context.scene.frame_current
        try:
            yield current_frame
        finally:
            context.scene.frame_current = current_frame

    @staticmethod
    def set_middle_frame(
        context: bpy.types.Context,
        strip: bpy.types.Sequence,
    ) -> int:
        """Sets the current frame to the middle frame of the strip."""

        middle = round((strip.frame_final_start + strip.frame_final_end) / 2)
        context.scene.frame_set(middle)
        return middle


class KITSU_OT_sqe_push_render(bpy.types.Operator):
    """"""

    bl_idname = "kitsu.sqe_push_render"
    bl_label = "Push Render"
    bl_options = {"INTERNAL"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return bool(
            prefs.session_auth(context) and context.scene.kitsu.task_type_sqe_render_id
        )

    def execute(self, context: bpy.types.Context) -> Set[str]:
        failed = []
        upload_queue: List[Path] = []  # will be used as successed list
        # get task stype by id from user selection enum property
        task_type = TaskType.by_id(context.scene.kitsu.task_type_sqe_render_id)

        logger.info("-START- Pushing Sequence Render")

        # clear cache
        Cache.clear_all()

        with self.override_render_settings(context):

            # ----RENDER AND SAVE SQE ------

            # begin first progress update
            selected_sequences = context.selected_sequences
            if not selected_sequences:
                selected_sequences = context.scene.sequence_editor.sequences_all

            context.window_manager.progress_begin(0, len(selected_sequences))

            for idx, strip in enumerate(selected_sequences):
                context.window_manager.progress_update(idx)

                if not checkstrip.is_valid_type(strip):
                    # failed.append(strip)
                    continue

                # only if strip is linked to sevrer
                if not checkstrip.is_linked(strip):
                    # failed.append(strip)
                    continue

                # check if shot is still available by id
                shot = checkstrip.shot_exists_by_id(strip, clear_cache=False)
                if not shot:
                    failed.append(strip)
                    continue

                # output path
                output_path = self._gen_output_path(strip, task_type)
                context.scene.render.filepath = output_path.as_posix()

                # frame range
                context.scene.frame_start = strip.frame_final_start
                context.scene.frame_end = strip.frame_final_end - 1

                # ensure folder exists
                output_path.parent.mkdir(parents=True, exist_ok=True)

                # make opengl render
                bpy.ops.render.opengl(animation=True, sequencer=True)

                # append path to upload queue
                upload_queue.append(output_path)

            # end first progress update
            context.window_manager.progress_update(len(upload_queue))
            context.window_manager.progress_end()

        # ----ULPOAD SQE RENDER ------

        # begin second progress update
        context.window_manager.progress_begin(0, len(upload_queue))

        # process thumbnail queue
        for idx, filepath in enumerate(upload_queue):
            context.window_manager.progress_update(idx)
            opsdata.upload_preview(
                context, filepath, task_type, comment="Sequence Editor Render"
            )

        # end second progress update
        context.window_manager.progress_update(len(upload_queue))
        context.window_manager.progress_end()

        # report
        report_str = f"Uploaded sequence editor render for {len(upload_queue)} shots"
        report_state = "INFO"
        if failed:
            report_state = "WARNING"
            report_str += f" | Failed: {len(failed)}"

        self.report(
            {report_state},
            report_str,
        )

        # log
        logger.info("-END- Pushing Sequence Editor Render")
        return {"FINISHED"}

    def _gen_output_path(self, strip: bpy.types.Sequence, task_type: TaskType) -> Path:
        addon_prefs = prefs.addon_prefs_get(bpy.context)
        folder_name = addon_prefs.sqe_render_dir
        file_name = f"{strip.kitsu.shot_id}_{strip.kitsu.shot_name}.{(task_type.name).lower()}.mp4"
        return Path(folder_name).absolute().joinpath(file_name)

    @contextlib.contextmanager
    def override_render_settings(self, context, thumbnail_width=256):
        """Overrides the render settings for thumbnail size in a 'with' block scope."""

        rd = context.scene.render

        # Remember current render settings in order to restore them later.

        # filepath
        filepath = rd.filepath

        # format render settings
        percentage = rd.resolution_percentage
        file_format = rd.image_settings.file_format
        ffmpeg_constant_rate = rd.ffmpeg.constant_rate_factor
        ffmpeg_codec = rd.ffmpeg.codec
        ffmpeg_format = rd.ffmpeg.format
        ffmpeg_audio_codec = rd.ffmpeg.audio_codec

        # scene settings
        frame_start = context.scene.frame_start
        frame_end = context.scene.frame_end
        current_frame = context.scene.frame_current

        try:
            # format render settings
            rd.resolution_percentage = 100
            rd.image_settings.file_format = "FFMPEG"
            rd.ffmpeg.constant_rate_factor = "MEDIUM"
            rd.ffmpeg.codec = "H264"
            rd.ffmpeg.format = "MPEG4"
            rd.ffmpeg.audio_codec = "AAC"
            yield

        finally:
            # filepath
            rd.filepath = filepath

            # Return the render settings to normal.
            rd.resolution_percentage = percentage
            rd.image_settings.file_format = file_format
            rd.ffmpeg.codec = ffmpeg_codec
            rd.ffmpeg.constant_rate_factor = ffmpeg_constant_rate
            rd.ffmpeg.format = ffmpeg_format
            rd.ffmpeg.audio_codec = ffmpeg_audio_codec

            # scene settings
            context.scene.frame_start = frame_start
            context.scene.frame_end = frame_end
            context.scene.frame_current = current_frame


class KITSU_OT_sqe_debug_duplicates(bpy.types.Operator):
    """"""

    bl_idname = "kitsu.sqe_debug_duplicates"
    bl_label = "Debug Duplicates"
    bl_property = "duplicates"
    bl_options = {"REGISTER", "UNDO"}

    duplicates: bpy.props.EnumProperty(
        items=opsdata.sqe_get_duplicates, name="Duplicates"
    )

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return True

    def execute(self, context: bpy.types.Context) -> Set[str]:
        strip_name = self.duplicates

        if not strip_name:
            return {"CANCELLED"}

        # deselect all if something is selected
        if context.selected_sequences:
            bpy.ops.sequencer.select_all()

        strip = context.scene.sequence_editor.sequences_all[strip_name]
        strip.select = True
        bpy.ops.sequencer.select()
        return {"FINISHED"}

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event) -> Set[str]:
        opsdata._sqe_duplicates[:] = opsdata.sqe_update_duplicates(context)
        return context.window_manager.invoke_props_popup(self, event)  # type: ignore


class KITSU_OT_sqe_debug_not_linked(bpy.types.Operator):
    """"""

    bl_idname = "kitsu.sqe_debug_not_linked"
    bl_label = "Debug Not Linked"
    bl_property = "not_linked"
    bl_options = {"REGISTER", "UNDO"}

    not_linked: bpy.props.EnumProperty(
        items=opsdata.sqe_get_not_linked, name="Not Linked"
    )

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return True

    def execute(self, context: bpy.types.Context) -> Set[str]:
        strip_name = self.not_linked

        if not strip_name:
            return {"CANCELLED"}

        # deselect all if something is selected
        if context.selected_sequences:
            bpy.ops.sequencer.select_all()

        strip = context.scene.sequence_editor.sequences_all[strip_name]
        strip.select = True
        bpy.ops.sequencer.select()

        return {"FINISHED"}

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event) -> Set[str]:
        opsdata._sqe_not_linked[:] = opsdata.sqe_update_not_linked(context)
        return context.window_manager.invoke_props_popup(self, event)  # type: ignore


class KITSU_OT_sqe_debug_multi_project(bpy.types.Operator):
    """"""

    bl_idname = "kitsu.sqe_debug_multi_project"
    bl_label = "Debug Multi Projects"
    bl_property = "multi_project"
    bl_options = {"REGISTER", "UNDO"}

    multi_project: bpy.props.EnumProperty(
        items=opsdata.sqe_get_multi_project, name="Multi Project"
    )

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return True

    def execute(self, context: bpy.types.Context) -> Set[str]:
        strip_name = self.multi_project

        if not strip_name:
            return {"CANCELLED"}

        # deselect all if something is selected
        if context.selected_sequences:
            bpy.ops.sequencer.select_all()

        strip = context.scene.sequence_editor.sequences_all[strip_name]
        strip.select = True
        bpy.ops.sequencer.select()

        return {"FINISHED"}

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event) -> Set[str]:
        opsdata._sqe_multi_project[:] = opsdata.sqe_update_multi_project(context)
        return context.window_manager.invoke_props_popup(self, event)  # type: ignore


class KITSU_OT_sqe_pull_edit(bpy.types.Operator):
    """
    Operator that invokes ui which shows user all available shots on server.
    It is used to 'link' a seqeunce strip to an alredy existent shot on server.
    Fills out all metadata after selecting shot.
    """

    bl_idname = "kitsu.sqe_pull_edit"
    bl_label = "Pull Edit"
    bl_description = (
        "Pulls the entire edit from kitsu and creates color strips for each shot. "
        "Does not change existing strips. Only places new strips if there is space"
    )
    bl_options = {"REGISTER", "UNDO", "UNDO_GROUPED"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        addon_prefs = prefs.addon_prefs_get(context)
        return bool(
            prefs.session_auth(context)
            and cache.project_active_get()
            and addon_prefs.metastrip_file
        )

    def execute(self, context: bpy.types.Context) -> Set[str]:
        addon_prefs = prefs.addon_prefs_get(context)
        failed = []
        created = []
        succeeded = []
        existing = []
        channel = context.scene.kitsu.pull_edit_channel
        active_project = cache.project_active_get()
        sequences = active_project.get_sequences_all()
        shot_strips = checksqe.get_shot_strips(context)
        occupied_ranges = checksqe.get_occupied_ranges(context)
        all_shots = active_project.get_shots_all()

        logger.info("-START- Pulling Edit")

        # begin progress update
        context.window_manager.progress_begin(0, len(all_shots))
        progress_idx = 0

        # process sequence after sequence
        for seq in sequences:
            print("\n" * 2)
            logger.info("Processing Sequence %s", seq.name)
            shots = seq.get_all_shots()

            # process all shots for sequence
            for shot in shots:
                context.window_manager.progress_update(progress_idx)
                progress_idx += 1

                # get frame range information
                frame_start = shot.data["frame_in"]
                frame_end = shot.data["frame_out"]

                # continue if frame range information is missing
                if not frame_start or not frame_end:
                    failed.append(shot)
                    logger.error(
                        "Failed to create shot %s. Missing frame range information.",
                        shot.name,
                    )
                    continue

                # frame info comes in str format from kitsu
                frame_start = int(frame_start)
                frame_end = int(frame_end)
                shot_range = range(frame_start, frame_end + 1)

                # try to find existing strip that is already linked to that shot
                strip = self._find_shot_strip(shot_strips, shot.id)

                # check if on the specified channel there is space to put the strip
                if str(channel) in occupied_ranges:
                    if checksqe.is_range_occupied(
                        shot_range, occupied_ranges[str(channel)]
                    ):
                        failed.append(shot)
                        logger.error(
                            "Failed to create shot %s. Channel: %i Range: %i - %i is occupied.",
                            shot.name,
                            channel,
                            frame_start,
                            frame_end,
                        )
                        continue

                if not strip:
                    # create new strip
                    strip = context.scene.sequence_editor.sequences.new_movie(
                        shot.name,
                        addon_prefs.metastrip_file,
                        channel,
                        frame_start,
                    )
                    strip.frame_final_end = frame_end

                    # apply strip.kitsu.frame_end_offset & strip.kitsu.frame_start_offset
                    opsdata.init_meta_strip_frame_offsets(strip)

                    created.append(shot)
                    logger.info("Shot %s created new strip", shot.name)

                else:
                    # update properties of existing strip
                    strip.channel = channel
                    # strip.frame_final_start = frame_start
                    # strip.frame_final_end = frame_end
                    logger.info("Shot %s use existing strip: %s", shot.name, strip.name)
                    existing.append(strip)

                # set blend alpha
                strip.blend_alpha = 0

                # pull shot meta and link shot
                pull.shot_meta(strip, shot, clear_cache=False)

                succeeded.append(shot)

        # end progress update
        context.window_manager.progress_update(len(all_shots))
        context.window_manager.progress_end()

        # report
        report_str = f"Shots: Succeded:{len(succeeded)} | Created  {len(created)} | Existing: {len(existing)}"
        report_state = "INFO"
        if failed:
            report_state = "WARNING"
            report_str += f" | Failed: {len(failed)}"

        self.report(
            {report_state},
            report_str,
        )

        # log
        logger.info("-END- Pulling Edit")

        return {"FINISHED"}

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event) -> Set[str]:
        return context.window_manager.invoke_props_dialog(  # type: ignore
            self, width=300
        )

    def draw(self, context):
        layout = self.layout

        row = layout.row()
        row.label(text="Set channel in which the entire edit should be created.")
        row = layout.row()
        row.prop(context.scene.kitsu, "pull_edit_channel")

    def _find_shot_strip(
        self, shot_strips: List[bpy.types.Sequence], shot_id: str
    ) -> Optional[bpy.types.Sequence]:
        for strip in shot_strips:
            if strip.kitsu.shot_id == shot_id:
                return strip

        return None

    def _get_random_pastel_color_rgb(self) -> Tuple[float, float, float]:
        """Returns a randomly generated color with high brightness and low saturation."""

        hue = random.random()
        saturation = random.uniform(0.25, 0.33)
        brightness = random.uniform(0.75, 0.83)

        color = colorsys.hsv_to_rgb(hue, saturation, brightness)
        return (color[0], color[1], color[2])


class KITSU_OT_sqe_init_strip_frame_range(bpy.types.Operator):
    """"""

    bl_idname = "kitsu.sqe_init_strip_frame_range"
    bl_label = "Initialize Shot Frame Range"
    bl_description = "Adds required shot metadata to selecetd strips"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return True

    def execute(self, context: bpy.types.Context) -> Set[str]:
        succeeded = []
        failed = []
        logger.info("-START- Initializing strip frame ranges")

        selected_sequences = context.selected_sequences
        if not selected_sequences:
            selected_sequences = context.scene.sequence_editor.sequences_all

        for strip in selected_sequences:

            if not checkstrip.is_valid_type(strip):
                # failed.append(strip)
                continue

            if not strip.kitsu.initialized:
                logger.info("%s not initialized.", strip.name)
                # failed.append(strip)
                continue

            # apply strip.kitsu.frame_end_offset & strip.kitsu.frame_start_offset
            opsdata.init_meta_strip_frame_offsets(strip)

            succeeded.append(strip)
            logger.info(
                "%s initiated strip frame range: (%i, %i)",
                strip.name,
                strip.kitsu.frame_start_offset,
                strip.kitsu.frame_end_offset,
            )

        # report
        report_str = f"Initiated frame range of {len(succeeded)} strips"
        report_state = "INFO"
        if failed:
            report_state = "WARNING"
            report_str += f" | Failed: {len(failed)}"

        self.report(
            {report_state},
            report_str,
        )

        # log
        logger.info("-END- Initializing strip frame ranges")
        util.ui_redraw()

        return {"FINISHED"}


class KITSU_OT_sqe_create_meta_strip(bpy.types.Operator):
    """"""

    bl_idname = "kitsu.sqe_create_meta_strip"
    bl_label = "Create Meta Strip"
    bl_description = "Adds meta strip for each selected strip"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        addon_prefs = prefs.addon_prefs_get(context)
        return bool(context.selected_sequences and addon_prefs.metastrip_file)

    def execute(self, context: bpy.types.Context) -> Set[str]:
        addon_prefs = prefs.addon_prefs_get(context)
        failed = []
        created = []
        occupied_ranges = checksqe.get_occupied_ranges(context)
        logger.info("-START- Creating Meta Strips")

        selected_sequences = context.selected_sequences

        for strip in selected_sequences:

            # get frame range information from current strip
            strip_range = range(strip.frame_final_start, strip.frame_final_end)
            channel = strip.channel + 1

            # check if one channel above strip there is space to put the meta strip
            if str(channel) in occupied_ranges:
                if checksqe.is_range_occupied(
                    strip_range, occupied_ranges[str(channel)]
                ):
                    failed.append(strip)
                    logger.error(
                        "Failed to create metastrip for %s. Channel: %i Range: %i - %i is occupied.",
                        strip.name,
                        channel,
                        strip.frame_final_start,
                        strip.frame_final_end,
                    )
                    continue

            # create new meta strip
            # TODO: frame range of metastrip is 1000 which is problematic because it needs to fit
            # on the frist try, EDIT: seems to work maybe per python overlaps of sequences possible?
            meta_strip = context.scene.sequence_editor.sequences.new_movie(
                f"{strip.name}_metastrip",
                addon_prefs.metastrip_file,
                strip.channel + 1,
                strip.frame_final_start,
            )
            created.append(meta_strip)

            # set blend alpha
            meta_strip.blend_alpha = 0

            # set frame in and out
            meta_strip.frame_final_start = strip.frame_final_start
            meta_strip.frame_final_end = strip.frame_final_end
            meta_strip.channel = strip.channel + 1

            # frame start offset
            offset_start = meta_strip.frame_final_start - meta_strip.frame_start
            meta_strip.kitsu.frame_start_offset = offset_start

            # frame end offset
            frame_end = meta_strip.frame_start + meta_strip.frame_duration
            offset_end = meta_strip.frame_final_end - frame_end
            meta_strip.kitsu.frame_end_offset = offset_end

            logger.info(
                "%s created metastrip: %s",
                strip.name,
                meta_strip.name,
            )

        # report
        report_str = f"Created {len(created)} meta strips"
        report_state = "INFO"
        if failed:
            report_state = "WARNING"
            report_str += f" | Failed: {len(failed)}"

        self.report(
            {report_state},
            report_str,
        )

        # log
        logger.info("-END- Creating Meta Strips")
        util.ui_redraw()

        return {"FINISHED"}


# ---------REGISTER ----------

classes = [
    KITSU_OT_sqe_push_new_sequence,
    KITSU_OT_sqe_push_new_shot,
    KITSU_OT_sqe_push_shot_meta,
    KITSU_OT_sqe_uninit_strip,
    KITSU_OT_sqe_unlink_shot,
    KITSU_OT_sqe_init_strip,
    KITSU_OT_sqe_link_shot,
    KITSU_OT_sqe_link_sequence,
    KITSU_OT_sqe_set_thumbnail_task_type,
    KITSU_OT_sqe_set_sqe_render_task_type,
    KITSU_OT_sqe_push_thumbnail,
    KITSU_OT_sqe_push_render,
    KITSU_OT_sqe_push_del_shot,
    KITSU_OT_sqe_pull_shot_meta,
    KITSU_OT_sqe_multi_edit_strip,
    KITSU_OT_sqe_debug_duplicates,
    KITSU_OT_sqe_debug_not_linked,
    KITSU_OT_sqe_debug_multi_project,
    KITSU_OT_sqe_pull_edit,
    KITSU_OT_sqe_init_strip_frame_range,
    KITSU_OT_sqe_create_meta_strip,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
