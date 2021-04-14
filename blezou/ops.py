import contextlib
from pathlib import Path
from typing import Dict, List, Set

import bpy

from . import gazu, cache, opsdata, prefs, push, pull, checkstrip
from .logger import ZLoggerFactory
from .types import (
    ZCache,
    ZSequence,
    ZShot,
    ZTask,
    ZTaskStatus,
    ZTaskType,
)

logger = ZLoggerFactory.getLogger(name=__name__)


def ui_redraw() -> None:
    """
    Forces blender to redraw the UI.
    """
    for screen in bpy.data.screens:
        for area in screen.areas:
            area.tag_redraw()


class BLEZOU_OT_session_start(bpy.types.Operator):
    """
    Starts the ZSession, which  is stored in Blezou addon preferences.
    Authenticates user with server until session ends.
    Host, email and password are retrieved from Blezou addon preferences.
    """

    bl_idname = "blezou.session_start"
    bl_label = "Start Gazou Session"
    bl_options = {"INTERNAL"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return True

    def execute(self, context: bpy.types.Context) -> Set[str]:
        zsession = prefs.zsession_get(context)

        zsession.set_config(self.get_config(context))
        zsession.start()

        # init cache variables, will skip if cache already initiated
        cache.init_cache_variables()

        return {"FINISHED"}

    def get_config(self, context: bpy.types.Context) -> Dict[str, str]:
        addon_prefs = prefs.addon_prefs_get(context)
        return {
            "email": addon_prefs.email,
            "host": addon_prefs.host,
            "passwd": addon_prefs.passwd,
        }


class BLEZOU_OT_session_end(bpy.types.Operator):
    """
    Ends the ZSession which is stored in Blezou addon preferences.
    """

    bl_idname = "blezou.session_end"
    bl_label = "End Gazou Session"
    bl_options = {"INTERNAL"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return prefs.zsession_auth(context)

    def execute(self, context: bpy.types.Context) -> Set[str]:
        zsession = prefs.zsession_get(context)
        zsession.end()
        # clear cache variables
        cache.clear_cache_variables()
        return {"FINISHED"}


class BLEZOU_OT_productions_load(bpy.types.Operator):
    """
    Gets all productions that are available in server and let's user select. Invokes a search Popup (enum_prop) on click.
    """

    bl_idname = "blezou.productions_load"
    bl_label = "Productions Load"
    bl_options = {"INTERNAL"}
    bl_property = "enum_prop"

    enum_prop: bpy.props.EnumProperty(items=opsdata._get_projects)  # type: ignore

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return prefs.zsession_auth(context)

    def execute(self, context: bpy.types.Context) -> Set[str]:
        # store vars to check if project / seq / shot changed
        project_prev_id = cache.zproject_active_get().id

        # update blezou metadata
        cache.zproject_active_set_by_id(context, self.enum_prop)

        # clear active shot when sequence changes
        if self.enum_prop != project_prev_id:
            cache.zsequence_active_reset(context)
            cache.zasset_type_active_reset(context)
            cache.zshot_active_reset(context)
            cache.zasset_active_reset(context)

        ui_redraw()
        return {"FINISHED"}

    def invoke(self, context, event):
        context.window_manager.invoke_search_popup(self)
        return {"FINISHED"}


class BLEZOU_OT_sequences_load(bpy.types.Operator):
    """
    Gets all sequences that are available in server for active production and let's user select. Invokes a search Popup (enum_prop) on click.
    """

    bl_idname = "blezou.sequences_load"
    bl_label = "Sequences Load"
    bl_options = {"INTERNAL"}
    bl_property = "enum_prop"

    # TODO: reduce api request to one, we request in _get_sequences and also in execute to set sequence_active

    enum_prop: bpy.props.EnumProperty(items=opsdata._get_sequences)  # type: ignore

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return bool(prefs.zsession_auth(context) and cache.zproject_active_get())

    def execute(self, context: bpy.types.Context) -> Set[str]:

        # store vars to check if project / seq / shot changed
        zseq_prev_id = cache.zsequence_active_get().id

        # update blezou metadata
        cache.zsequence_active_set_by_id(context, self.enum_prop)

        # clear active shot when sequence changes
        if self.enum_prop != zseq_prev_id:
            cache.zshot_active_reset(context)

        ui_redraw()
        return {"FINISHED"}

    def invoke(self, context, event):
        context.window_manager.invoke_search_popup(self)
        return {"FINISHED"}


class BLEZOU_OT_shots_load(bpy.types.Operator):
    """
    Gets all sequences that are available in server for active production and let's user select. Invokes a search Popup (enum_prop) on click.
    """

    bl_idname = "blezou.shots_load"
    bl_label = "Shots Load"
    bl_options = {"INTERNAL"}
    bl_property = "enum_prop"

    # TODO: reduce api request to one, we request in _get_shots and also in execute to set active shot

    enum_prop: bpy.props.EnumProperty(items=opsdata._get_shots_from_active_seq)  # type: ignore

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        # only if session is auth active_project and active sequence selected
        return bool(
            prefs.zsession_auth(context)
            and cache.zsequence_active_get()
            and cache.zproject_active_get()
        )

    def execute(self, context: bpy.types.Context) -> Set[str]:
        # update blezou metadata
        if self.enum_prop:
            cache.zshot_active_set_by_id(context, self.enum_prop)
        ui_redraw()
        return {"FINISHED"}

    def invoke(self, context, event):
        context.window_manager.invoke_search_popup(self)
        return {"FINISHED"}


class BLEZOU_OT_asset_types_load(bpy.types.Operator):
    """
    Gets all sequences that are available in server for active production and let's user select. Invokes a search Popup (enum_prop) on click.
    """

    bl_idname = "blezou.asset_types_load"
    bl_label = "Assettyes Load"
    bl_options = {"INTERNAL"}
    bl_property = "enum_prop"

    # TODO: reduce api request to one, we request in _get_sequences and also in execute to set sequence_active

    enum_prop: bpy.props.EnumProperty(items=opsdata._get_assets_from_active_asset_type)  # type: ignore

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return bool(prefs.zsession_auth(context) and cache.zproject_active_get())

    def execute(self, context: bpy.types.Context) -> Set[str]:
        # store vars to check if project / seq / shot changed
        asset_type_prev_id = cache.zasset_type_active_get().id

        # update blezou metadata
        cache.zasset_type_active_set_by_id(context, self.enum_prop)

        # clear active shot when sequence changes
        if self.enum_prop != asset_type_prev_id:
            cache.zasset_active_reset(context)

        ui_redraw()
        return {"FINISHED"}

    def invoke(self, context, event):
        context.window_manager.invoke_search_popup(self)
        return {"FINISHED"}


class BLEZOU_OT_assets_load(bpy.types.Operator):
    """
    Gets all sequences that are available in server for active production and let's user select. Invokes a search Popup (enum_prop) on click.
    """

    bl_idname = "blezou.assets_load"
    bl_label = "Assets Load"
    bl_options = {"INTERNAL"}
    bl_property = "enum_prop"

    # TODO: reduce api request to one, we request in _get_sequences and also in execute to set sequence_active
    enum_prop: bpy.props.EnumProperty(items=opsdata._get_assets_from_active_asset_type)  # type: ignore

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return bool(
            prefs.zsession_auth(context)
            and cache.zproject_active_get()
            and cache.zasset_type_active_get()
        )

    def execute(self, context: bpy.types.Context) -> Set[str]:
        if not self.enum_prop:
            return {"CANCELLED"}

        # update blezou metadata
        cache.zasset_active_set_by_id(context, self.enum_prop)
        ui_redraw()
        return {"FINISHED"}

    def invoke(self, context, event):
        context.window_manager.invoke_search_popup(self)
        return {"FINISHED"}


class BLEZOU_OT_sqe_push_shot_meta(bpy.types.Operator):
    """
    Operator that pushes metadata of all selected sequencce strips to sevrer
    after performing various checks. Metadata is saved in strip.blezou.
    """

    bl_idname = "blezou.sqe_push_shot_meta"
    bl_label = "Push Shot Metadata"
    bl_options = {"INTERNAL"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return bool(prefs.zsession_auth(context))

    def execute(self, context: bpy.types.Context) -> Set[str]:
        succeeded = []
        failed = []
        logger.info("-START- Blezou Pushing Metadata")
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

            # only if strip is linked to sevrer
            if not checkstrip.is_linked(strip):
                # failed.append(strip)
                continue

            # check if shot is still available by id
            zshot = checkstrip.shot_exists_by_id(strip)
            if not zshot:
                failed.append(strip)
                continue

            # push update to shot
            push.shot_meta(strip, zshot)
            succeeded.append(strip)

        # end progress update
        context.window_manager.progress_update(len(selected_sequences))
        context.window_manager.progress_end()

        self.report(
            {"INFO"},
            f"Pushed Metadata of {len(succeeded)} Shots | Failed: {len(failed)}.",
        )
        logger.info("-END- Blezou Pushing Metadata")
        return {"FINISHED"}


class BLEZOU_OT_sqe_push_new_shot(bpy.types.Operator):
    """
    Operator that creates a new shot based on all selected sequencce strips to sevrer
    after performing various checks. Does not create shot if already exists to sevrer .
    """

    bl_idname = "blezou.sqe_push_new_shot"
    bl_label = "Submit New Shot"
    bl_options = {"INTERNAL"}

    confirm: bpy.props.BoolProperty(name="confirm")

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        # needs to be logged in, active project
        nr_of_shots = len(context.selected_sequences)
        if nr_of_shots == 1:
            strip = context.scene.sequence_editor.active_strip
            return bool(
                prefs.zsession_auth(context)
                and cache.zproject_active_get()
                and strip.blezou.sequence_name
                and strip.blezou.shot_name
            )

        return bool(prefs.zsession_auth(context) and cache.zproject_active_get())

    def execute(self, context: bpy.types.Context) -> Set[str]:

        if not self.confirm:
            self.report({"WARNING"}, "Submit new shots aborted.")
            return {"CANCELLED"}

        zproject_active = cache.zproject_active_get()
        succeeded = []
        failed = []
        logger.info("-START- Blezou submitting new shots to: %s", zproject_active.name)

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
            zseq = checkstrip.seq_exists_by_name(strip, zproject_active)
            if not zseq:
                zseq = push.new_sequence(strip, zproject_active)

            # check if shot already to sevrer  > create it
            zshot = checkstrip.shot_exists_by_name(strip, zproject_active, zseq)
            if zshot:
                failed.append(strip)
                continue

            # push update to shot
            zshot = push.new_shot(strip, zseq, zproject_active)
            pull.shot_meta(strip, zshot)
            succeeded.append(strip)

        # end progress update
        context.window_manager.progress_update(len(selected_sequences))
        context.window_manager.progress_end()

        # clear cache
        ZCache.clear_all()

        self.report(
            {"INFO"},
            f"Submitted {len(succeeded)} new shots | Failed: {len(failed)}",
        )
        logger.info("-END- Blezou submitting new shots to: %s", zproject_active.name)
        ui_redraw()
        return {"FINISHED"}

    def invoke(self, context, event):
        self.confirm = False
        return context.window_manager.invoke_props_dialog(self, width=500)

    def draw(self, context):
        zproject_active = cache.zproject_active_get()
        selected_sequences = context.selected_sequences

        if not selected_sequences:
            selected_sequences = context.scene.sequence_editor.sequences_all

        strips_to_submit = [
            s
            for s in selected_sequences
            if s.blezou.initialized
            and not s.blezou.linked
            and s.blezou.shot_name
            and s.blezou.sequence_name
        ]

        if len(selected_sequences) > 1:
            noun = "%i Shots" % len(strips_to_submit)
        else:
            noun = "this Shot"

        # UI
        layout = self.layout

        # Production
        row = layout.row()
        row.label(text=f"Production: {zproject_active.name}", icon="FILEBROWSER")

        # confirm dialog
        col = layout.column()
        col.prop(
            self,
            "confirm",
            text="Submit %s to server. Will skip shots if they already exist."
            % (noun.lower()),
        )


class BLEZOU_OT_sqe_push_new_sequence(bpy.types.Operator):
    """
    Operator with input dialog that creates a new sequence on server.
    Does not create sequence if already exists on server.
    """

    bl_idname = "blezou.sqe_push_new_sequence"
    bl_label = "Submit New Sequence"
    bl_options = {"INTERNAL"}

    sequence_name: bpy.props.StringProperty(
        name="Name", default="", description="Name of new sequence"
    )
    confirm: bpy.props.BoolProperty(name="confirm")

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        # needs to be logged in, active project
        return bool(prefs.zsession_auth(context) and cache.zproject_active_get())

    def execute(self, context: bpy.types.Context) -> Set[str]:

        if not self.confirm:
            self.report({"WARNING"}, "Submit new sequence aborted.")
            return {"CANCELLED"}

        if not self.sequence_name:
            self.report({"WARNING"}, "Invalid sequence name.")
            return {"CANCELLED"}

        zproject_active = cache.zproject_active_get()

        zsequence = zproject_active.get_sequence_by_name(self.sequence_name)

        if zsequence:
            self.report(
                {"WARNING"},
                f"Sequence: {zsequence.name} already exists on server.",
            )
            return {"CANCELLED"}

        # create sequence
        zsequence = zproject_active.create_sequence(self.sequence_name)

        # clear cache
        ZCache.clear_all()

        self.report(
            {"INFO"},
            f"Submitted new sequence: {zsequence.name}",
        )
        logger.info("Submitted new sequence: %s", zsequence.name)
        return {"FINISHED"}

    def invoke(self, context, event):
        self.confirm = False
        return context.window_manager.invoke_props_dialog(self, width=300)

    def draw(self, context):
        # UI
        layout = self.layout
        zproject_active = cache.zproject_active_get()

        # Production
        row = layout.row()
        row.label(text=f"Production: {zproject_active.name}", icon="FILEBROWSER")

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


class BLEZOU_OT_sqe_init_strip(bpy.types.Operator):
    """
    Operator that initializes a regular sequence strip to a 'blezou' shot.
    Only sets strip.blezou.initialized = True. But this is required for further
    operations and to  differentiate between regular sequence strip and blezou shot strip.
    """

    bl_idname = "blezou.sqe_init_strip"
    bl_label = "Initialize Shot"
    bl_description = "Adds required shot metadata to selecetd strips"

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

            if strip.blezou.initialized:
                logger.info("%s already initialized.", strip.name)
                # failed.append(strip)
                continue

            strip.blezou.initialized = True
            succeeded.append(strip)
            logger.info("Initiated strip: %s as shot.", strip.name)

        self.report(
            {"INFO"},
            f"Initiated {len(succeeded)} shots | Failed: {len(failed)}.",
        )
        logger.info("-END- Initializing shots")
        ui_redraw()
        return {"FINISHED"}


class BLEZOU_OT_sqe_link_sequence(bpy.types.Operator):
    """
    Gets all sequences that are available in server for active production and let's user select. Invokes a search Popup (enum_prop) on click.
    """

    bl_idname = "blezou.sqe_link_sequence"
    bl_label = "Link Sequence"
    bl_options = {"INTERNAL"}
    bl_property = "enum_prop"

    enum_prop: bpy.props.EnumProperty(
        items=opsdata._get_sequences,
    )  # type: ignore

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        strip = context.scene.sequence_editor.active_strip
        return bool(
            prefs.zsession_auth(context)
            and cache.zproject_active_get()
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
        zseq = ZSequence.by_id(sequence_id)
        strip.blezou.sequence_name = zseq.name
        strip.blezou.sequence_id = zseq.id

        ui_redraw()
        return {"FINISHED"}

    def invoke(self, context, event):
        context.window_manager.invoke_search_popup(self)
        return {"FINISHED"}


class BLEZOU_OT_sqe_link_shot(bpy.types.Operator):
    """
    Operator that invokes ui which shows user all available shots on server.
    It is used to 'link' a seqeunce strip to an alredy existent shot on server.
    Fills out all metadata after selecting shot.
    """

    bl_idname = "blezou.sqe_link_shot"
    bl_label = "Link Shot"
    bl_description = (
        "Adds required shot metadata to selecetd strip based on data from server."
    )

    sequence_enum: bpy.props.EnumProperty(items=opsdata._get_sequences, name="Sequence")  # type: ignore
    shots_enum: bpy.props.EnumProperty(items=opsdata._get_shots_from_op_enum, name="Shot")  # type: ignore
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
            prefs.zsession_auth(context)
            and cache.zproject_active_get()
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
            zshot = ZShot.by_id(shot_id)

        except (TypeError, gazu.exception.ServerErrorException):
            self.report({"WARNING"}, "Invalid URL: %s" % self.url)
            return {"CANCELLED"}

        except gazu.exception.RouteNotFoundException:
            self.report({"WARNING"}, "ID not found on server: %s" % shot_id)
            return {"CANCELLED"}

        # pull shot meta
        pull.shot_meta(strip, zshot)

        t = "Linked strip: %s to shot: %s with ID: %s" % (
            strip.name,
            zshot.name,
            zshot.id,
        )
        logger.info(t)
        self.report({"INFO"}, t)
        ui_redraw()

        return {"FINISHED"}

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event) -> Set[str]:
        self.use_url = False
        return context.window_manager.invoke_props_dialog(  # type: ignore
            self, width=300
        )

    def draw(self, context):
        layout = self.layout

        row = layout.row()
        row.prop(self, "use_url")
        if self.use_url:
            row.prop(self, "url")
        else:
            row = layout.row()
            row.prop(self, "sequence_enum")
            row = layout.row()
            row.prop(self, "shots_enum")
            row = layout.row()


class BLEZOU_OT_sqe_multi_edit_strip(bpy.types.Operator):
    """"""

    bl_idname = "blezou.sqe_multi_edit_strip"
    bl_label = "Multi Edit Strip"
    bl_options = {"INTERNAL"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        # only if all selected strips are initialized but not linked
        # and they all have the same sequence name
        sel_shots = context.selected_sequences
        nr_of_shots = len(sel_shots)

        if not nr_of_shots > 1:
            return False

        seq_name = sel_shots[0].blezou.sequence_name
        for s in sel_shots:
            if (
                s.blezou.linked
                or not s.blezou.initialized
                or not checkstrip.is_valid_type(s)
            ):
                return False
            if s.blezou.sequence_name != seq_name:
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
            shot = opsdata._resolve_pattern(shot_pattern, var_lookup_table)

            # set metadata
            strip.blezou.sequence_name = sequence
            strip.blezou.shot_name = shot

            succeeded.append(strip)
            logger.info(
                "Strip: %s Assign sequence: %s Assign shot: %s"
                % (strip.name, sequence, shot)
            )

        self.report(
            {"INFO"},
            f"Assigned {len(succeeded)} Shots | Failed: {len(failed)}.",
        )
        logger.info("-END- Multi Edit Shot")
        ui_redraw()
        return {"FINISHED"}


class BLEZOU_OT_sqe_pull_shot_meta(bpy.types.Operator):
    """
    Operator that pulls metadata of all selected sequencce strips from server
    after performing various checks. Metadata will be saved in strip.blezou.
    """

    bl_idname = "blezou.sqe_pull_shot_meta"
    bl_label = "Pull Shot Metadata"
    bl_options = {"INTERNAL"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return bool(prefs.zsession_auth(context))

    def execute(self, context: bpy.types.Context) -> Set[str]:
        succeeded = []
        failed = []
        logger.info("-START- Pulling shot metadata")

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

            # only if strip is linked to sevrer
            if not checkstrip.is_linked(strip):
                # failed.append(strip)
                continue

            # check if shot is still available by id
            zshot = checkstrip.shot_exists_by_id(strip)
            if not zshot:
                failed.append(strip)
                continue

            # push update to shot
            pull.shot_meta(strip, zshot)
            succeeded.append(strip)

        # end progress update
        context.window_manager.progress_update(len(selected_sequences))
        context.window_manager.progress_end()
        self.report(
            {"INFO"},
            f"Pulled metadata for {len(succeeded)} shots | Failed: {len(failed)}.",
        )
        logger.info("-END- Pulling shot metadata")
        ui_redraw()
        return {"FINISHED"}


class BLEZOU_OT_sqe_uninit_strip(bpy.types.Operator):
    """
    Operator that deletes all  metadata of all selected sequencce strips
    after performing various checks. It does NOT change anything on server.
    """

    bl_idname = "blezou.sqe_uninit_strip"
    bl_label = "Uninitialize"
    bl_description = "c selecetd strips. Only affects Sequence Editor. "
    confirm: bpy.props.BoolProperty(name="Confirm")

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return bool(context.selected_sequences)

    def execute(self, context: bpy.types.Context) -> Set[str]:
        if not self.confirm:
            self.report({"WARNING"}, "Uninitializing aborted.")
            return {"CANCELLED"}

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

            # clear blezou properties
            strip.blezou.clear()
            succeeded.append(strip)
            logger.info("Uninitialized strip: %s", strip.name)

        self.report(
            {"INFO"},
            f"Uninitialized {len(succeeded)} strips | Failed: {len(failed)}.",
        )
        logger.info("-END- Uninitializing strips")
        ui_redraw()
        return {"FINISHED"}

    def invoke(self, context, event):
        self.confirm = False
        return context.window_manager.invoke_props_dialog(self, width=500)

    def draw(self, context):
        layout = self.layout
        col = layout.column()

        selshots = context.selected_sequences
        strips_to_uninit = [
            s for s in selshots if s.blezou.initialized and not s.blezou.linked
        ]

        if len(strips_to_uninit) > 1:
            noun = "%i shots" % len(strips_to_uninit)
        else:
            noun = "this shot"

        col.prop(
            self,
            "confirm",
            text="Uninitialize %s. Only affects Sequence Editor." % noun,
        )


class BLEZOU_OT_sqe_unlink_shot(bpy.types.Operator):
    """
    Operator that deletes all  metadata of all selected sequencce strips
    after performing various checks. It does NOT change anything on server.
    """

    bl_idname = "blezou.sqe_unlink_shot"
    bl_label = "Unlink"
    bl_description = (
        "Deletes link to the server of selecetd shots. Only affects Sequence Editor."
    )
    confirm: bpy.props.BoolProperty(name="Confirm")

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return bool(context.selected_sequences)

    def execute(self, context: bpy.types.Context) -> Set[str]:
        if not self.confirm:
            self.report({"WARNING"}, "Unlinking aborted.")
            return {"CANCELLED"}

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

            # clear blezou properties
            shot_name = strip.blezou.shot_name
            strip.blezou.unlink()
            succeeded.append(strip)
            logger.info("Unlinked shot: %s", shot_name)

        self.report(
            {"INFO"},
            f"Unlinked {len(succeeded)} shots | Failed: {len(failed)}.",
        )
        logger.info("-END- Unlinking shots")
        ui_redraw()
        return {"FINISHED"}

    def invoke(self, context, event):
        self.confirm = False
        return context.window_manager.invoke_props_dialog(self, width=500)

    def draw(self, context):
        layout = self.layout
        col = layout.column()

        selshots = context.selected_sequences
        strips_to_unlink = [s for s in selshots if s.blezou.linked]

        if len(strips_to_unlink) > 1:
            noun = "%i shots" % len(strips_to_unlink)
        else:
            noun = "this shot"

        col.prop(
            self,
            "confirm",
            text="Deletes link to server of %s. Only affects Sequence Editor." % noun,
        )


class BLEZOU_OT_sqe_push_del_shot(bpy.types.Operator):
    """
    Operator that deletes all  metadata of all selected sequencce strips
    after performing various checks. It does NOT change anything on server.
    """

    bl_idname = "blezou.sqe_push_del_shot"
    bl_label = "Delete Shot"
    bl_description = "Deletes shot on server and clears metadata of selected strips."

    confirm: bpy.props.BoolProperty(name="Confirm")

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return bool(prefs.zsession_auth(context) and context.selected_sequences)

    def execute(self, context: bpy.types.Context) -> Set[str]:
        if not self.confirm:
            self.report({"WARNING"}, "Push delete aborted.")
            return {"CANCELLED"}

        succeeded = []
        failed = []
        logger.info("-START- Blezou deleting shots")

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
            zshot = checkstrip.shot_exists_by_id(strip)
            if not zshot:
                failed.append(strip)
                continue

            # delete shot
            push.delete_shot(strip, zshot)
            succeeded.append(strip)

        # end progress update
        context.window_manager.progress_update(len(selected_sequences))
        context.window_manager.progress_end()

        self.report(
            {"INFO"},
            f"Deleted {len(succeeded)} shots | Failed: {len(failed)}",
        )
        logger.info("-END- Blezou deleting shots")
        ui_redraw()
        return {"FINISHED"}

    def invoke(self, context, event):
        self.confirm = False
        return context.window_manager.invoke_props_dialog(self, width=500)

    def draw(self, context):
        layout = self.layout
        col = layout.column()

        selshots = context.selected_sequences
        strips_to_delete = [s for s in selshots if s.blezou.linked]

        if len(selshots) > 1:
            noun = "%i shots" % len(strips_to_delete)
        else:
            noun = "this shot"

        col.prop(
            self,
            "confirm",
            text="Delete %s on server." % noun,
        )


class BLEZOU_OT_sqe_push_thumbnail(bpy.types.Operator):
    """
    Operator that takes thumbnail of all selected sequencce strips and saves them
    in tmp directory. Loops through all thumbnails and uploads them to sevrer .
    uses Animation task type to create task and set main thumbnail in wip state.
    """

    bl_idname = "blezou.sqe_push_thumbnail"
    bl_label = "Push Thumbnail"
    bl_options = {"INTERNAL"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return bool(prefs.zsession_auth(context))

    def execute(self, context: bpy.types.Context) -> Set[str]:
        nr_of_strips: int = len(context.selected_sequences)
        do_multishot: bool = nr_of_strips > 1
        failed = []
        upload_queue: List[Path] = []  # will be used as successed list

        logger.info("-START- Pushing shot thumbnails")
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
                    zshot = checkstrip.shot_exists_by_id(strip)
                    if not zshot:
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
                    self._upload_thumbnail(filepath)

                # end second progress update
                context.window_manager.progress_update(len(upload_queue))
                context.window_manager.progress_end()

        self.report(
            {"INFO"},
            f"Created thumbnails for {len(upload_queue)} shots | Failed: {len(failed)}",
        )
        logger.info("-END- Pushing shot thumbnails")
        return {"FINISHED"}

    def make_thumbnail(
        self, context: bpy.types.Context, strip: bpy.types.Sequence
    ) -> Path:
        bpy.ops.render.render()
        file_name = f"{strip.blezou.shot_id}_{str(context.scene.frame_current)}.jpg"
        path = self._save_render(bpy.data.images["Render Result"], file_name)
        logger.info(
            f"Saved thumbnail of shot {strip.blezou.shot_name} to {path.as_posix()}"
        )
        return path

    def _save_render(self, datablock: bpy.types.Image, file_name: str) -> Path:
        """Save the current render image to disk"""

        addon_prefs = prefs.addon_prefs_get(bpy.context)
        folder_name = addon_prefs.folder_thumbnail

        # Ensure folder exists
        folder_path = Path(folder_name).absolute()
        folder_path.mkdir(parents=True, exist_ok=True)

        path = folder_path.joinpath(file_name)
        datablock.save_render(str(path))
        return path.absolute()

    def _upload_thumbnail(self, filepath: Path) -> None:
        # get shot by id which is in filename of thumbnail
        shot_id = filepath.name.split("_")[0]
        zshot = ZShot.by_id(shot_id)

        # get task status 'wip' and task type 'Animation'
        ztask_status = ZTaskStatus.by_short_name("wip")
        ztask_type = ZTaskType.by_name("Animation")

        if not ztask_status:
            raise RuntimeError(
                "Failed to upload thumbnails. Task status: 'wip' is missing."
            )
        if not ztask_type:
            raise RuntimeError(
                "Failed to upload thumbnails. Task type: 'Animation' is missing."
            )

        # find / get latest task
        ztask = ZTask.by_name(zshot, ztask_type)
        if not ztask:
            # turns out a entitiy on server can have 0 tasks even tough task types exist
            # you have to create a task first before being able to upload a thumbnail
            ztasks = zshot.get_all_tasks()  # list of ztasks
            if not ztasks:
                ztask = ZTask.new_task(zshot, ztask_type, ztask_status=ztask_status)
            else:
                ztask = ztasks[-1]

        # create a comment, e.G 'set main thumbnail'
        zcomment = ztask.add_comment(ztask_status, comment="set main thumbnail")

        # add_preview_to_comment
        zpreview = ztask.add_preview_to_comment(zcomment, filepath.as_posix())

        # preview.set_main_preview()
        zpreview.set_main_preview()
        logger.info(
            f"Uploaded thumbnail for shot: {zshot.name} under: {ztask_type.name}"
        )

    @contextlib.contextmanager
    def override_render_settings(self, context, thumbnail_width=256):
        """Overrides the render settings for thumbnail size in a 'with' block scope."""

        rd = context.scene.render

        # Remember current render settings in order to restore them later.
        orig_percentage = rd.resolution_percentage
        orig_file_format = rd.image_settings.file_format
        orig_quality = rd.image_settings.quality

        try:
            # Set the render settings to thumbnail size.
            # Update resolution % instead of the actual resolution to scale text strips properly.
            rd.resolution_percentage = round(thumbnail_width * 100 / rd.resolution_x)
            rd.image_settings.file_format = "JPEG"
            rd.image_settings.quality = 80
            yield

        finally:
            # Return the render settings to normal.
            rd.resolution_percentage = orig_percentage
            rd.image_settings.file_format = orig_file_format
            rd.image_settings.quality = orig_quality

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


class BLEZOU_OT_sqe_debug_duplicates(bpy.types.Operator):
    """"""

    bl_idname = "blezou.sqe_debug_duplicates"
    bl_label = "Debug Duplicates"
    bl_options = {"REGISTER", "UNDO"}
    bl_property = "duplicates"

    duplicates: bpy.props.EnumProperty(
        items=opsdata._sqe_get_duplicates, name="Duplicates"
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
        opsdata._sqe_duplicates[:] = opsdata._sqe_update_duplicates(context)
        return context.window_manager.invoke_props_popup(self, event)  # type: ignore


class BLEZOU_OT_sqe_debug_not_linked(bpy.types.Operator):
    """"""

    bl_idname = "blezou.sqe_debug_not_linked"
    bl_label = "Debug Not Linked"
    bl_options = {"REGISTER", "UNDO"}
    bl_property = "not_linked"

    not_linked: bpy.props.EnumProperty(
        items=opsdata._sqe_get_not_linked, name="Not Linked"
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
        opsdata._sqe_not_linked[:] = opsdata._sqe_update_not_linked(context)
        return context.window_manager.invoke_props_popup(self, event)  # type: ignore


class BLEZOU_OT_sqe_debug_multi_project(bpy.types.Operator):
    """"""

    bl_idname = "blezou.sqe_debug_multi_project"
    bl_label = "Debug Multi Projects"
    bl_options = {"REGISTER", "UNDO"}
    bl_property = "multi_project"

    multi_project: bpy.props.EnumProperty(
        items=opsdata._sqe_get_multi_project, name="Multi Project"
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
        opsdata._sqe_multi_project[:] = opsdata._sqe_update_multi_project(context)
        return context.window_manager.invoke_props_popup(self, event)  # type: ignore


# ---------REGISTER ----------

classes = [
    BLEZOU_OT_session_start,
    BLEZOU_OT_session_end,
    BLEZOU_OT_productions_load,
    BLEZOU_OT_sequences_load,
    BLEZOU_OT_shots_load,
    BLEZOU_OT_asset_types_load,
    BLEZOU_OT_assets_load,
    BLEZOU_OT_sqe_push_new_sequence,
    BLEZOU_OT_sqe_push_new_shot,
    BLEZOU_OT_sqe_push_shot_meta,
    BLEZOU_OT_sqe_uninit_strip,
    BLEZOU_OT_sqe_unlink_shot,
    BLEZOU_OT_sqe_init_strip,
    BLEZOU_OT_sqe_link_shot,
    BLEZOU_OT_sqe_link_sequence,
    BLEZOU_OT_sqe_push_thumbnail,
    BLEZOU_OT_sqe_push_del_shot,
    BLEZOU_OT_sqe_pull_shot_meta,
    BLEZOU_OT_sqe_multi_edit_strip,
    BLEZOU_OT_sqe_debug_duplicates,
    BLEZOU_OT_sqe_debug_not_linked,
    BLEZOU_OT_sqe_debug_multi_project,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
