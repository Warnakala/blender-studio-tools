import contextlib
from pathlib import Path
from typing import Dict, List, Set

import bpy

from . import gazu, cache, opsdata, prefs, push, pull, checkstrip
from .logger import ZLoggerFactory
from .types import (
    Cache,
    Sequence,
    Shot,
    Task,
    TaskStatus,
    TaskType,
)

logger = ZLoggerFactory.getLogger(name=__name__)


def ui_redraw() -> None:
    """
    Forces blender to redraw the UI.
    """
    for screen in bpy.data.screens:
        for area in screen.areas:
            area.tag_redraw()


class KITSU_OT_session_start(bpy.types.Operator):
    """
    Starts the ZSession, which  is stored in blender_kitsu addon preferences.
    Authenticates user with server until session ends.
    Host, email and password are retrieved from blender_kitsu addon preferences.
    """

    bl_idname = "kitsu.session_start"
    bl_label = "Start Kitsu Session"
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


class KITSU_OT_session_end(bpy.types.Operator):
    """
    Ends the ZSession which is stored in blender_kitsu addon preferences.
    """

    bl_idname = "kitsu.session_end"
    bl_label = "End Kitsu Session"
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


class KITSU_OT_productions_load(bpy.types.Operator):
    """
    Gets all productions that are available in server and let's user select. Invokes a search Popup (enum_prop) on click.
    """

    bl_idname = "kitsu.productions_load"
    bl_label = "Productions Load"
    bl_options = {"INTERNAL"}
    bl_property = "enum_prop"

    enum_prop: bpy.props.EnumProperty(items=opsdata._get_projects)  # type: ignore

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return prefs.zsession_auth(context)

    def execute(self, context: bpy.types.Context) -> Set[str]:
        # store vars to check if project / seq / shot changed
        project_prev_id = cache.project_active_get().id

        # update kitsu metadata
        cache.project_active_set_by_id(context, self.enum_prop)

        # clear active shot when sequence changes
        if self.enum_prop != project_prev_id:
            cache.sequence_active_reset(context)
            cache.asset_type_active_reset(context)
            cache.shot_active_reset(context)
            cache.asset_active_reset(context)

        ui_redraw()
        return {"FINISHED"}

    def invoke(self, context, event):
        context.window_manager.invoke_search_popup(self)
        return {"FINISHED"}


class KITSU_OT_sequences_load(bpy.types.Operator):
    """
    Gets all sequences that are available in server for active production and let's user select. Invokes a search Popup (enum_prop) on click.
    """

    bl_idname = "kitsu.sequences_load"
    bl_label = "Sequences Load"
    bl_options = {"INTERNAL"}
    bl_property = "enum_prop"

    # TODO: reduce api request to one, we request in _get_sequences and also in execute to set sequence_active

    enum_prop: bpy.props.EnumProperty(items=opsdata._get_sequences)  # type: ignore

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return bool(prefs.zsession_auth(context) and cache.project_active_get())

    def execute(self, context: bpy.types.Context) -> Set[str]:

        # store vars to check if project / seq / shot changed
        zseq_prev_id = cache.sequence_active_get().id

        # update kitsu metadata
        cache.sequence_active_set_by_id(context, self.enum_prop)

        # clear active shot when sequence changes
        if self.enum_prop != zseq_prev_id:
            cache.shot_active_reset(context)

        ui_redraw()
        return {"FINISHED"}

    def invoke(self, context, event):
        context.window_manager.invoke_search_popup(self)
        return {"FINISHED"}


class KITSU_OT_shots_load(bpy.types.Operator):
    """
    Gets all sequences that are available in server for active production and let's user select. Invokes a search Popup (enum_prop) on click.
    """

    bl_idname = "kitsu.shots_load"
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
            and cache.sequence_active_get()
            and cache.project_active_get()
        )

    def execute(self, context: bpy.types.Context) -> Set[str]:
        # update kitsu metadata
        if self.enum_prop:
            cache.shot_active_set_by_id(context, self.enum_prop)
        ui_redraw()
        return {"FINISHED"}

    def invoke(self, context, event):
        context.window_manager.invoke_search_popup(self)
        return {"FINISHED"}


class KITSU_OT_asset_types_load(bpy.types.Operator):
    """
    Gets all sequences that are available in server for active production and let's user select. Invokes a search Popup (enum_prop) on click.
    """

    bl_idname = "kitsu.asset_types_load"
    bl_label = "Assettyes Load"
    bl_options = {"INTERNAL"}
    bl_property = "enum_prop"

    # TODO: reduce api request to one, we request in _get_sequences and also in execute to set sequence_active

    enum_prop: bpy.props.EnumProperty(items=opsdata._get_assets_from_active_asset_type)  # type: ignore

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return bool(prefs.zsession_auth(context) and cache.project_active_get())

    def execute(self, context: bpy.types.Context) -> Set[str]:
        # store vars to check if project / seq / shot changed
        asset_type_prev_id = cache.asset_type_active_get().id

        # update kitsu metadata
        cache.asset_type_active_set_by_id(context, self.enum_prop)

        # clear active shot when sequence changes
        if self.enum_prop != asset_type_prev_id:
            cache.asset_active_reset(context)

        ui_redraw()
        return {"FINISHED"}

    def invoke(self, context, event):
        context.window_manager.invoke_search_popup(self)
        return {"FINISHED"}


class KITSU_OT_assets_load(bpy.types.Operator):
    """
    Gets all sequences that are available in server for active production and let's user select. Invokes a search Popup (enum_prop) on click.
    """

    bl_idname = "kitsu.assets_load"
    bl_label = "Assets Load"
    bl_options = {"INTERNAL"}
    bl_property = "enum_prop"

    # TODO: reduce api request to one, we request in _get_sequences and also in execute to set sequence_active
    enum_prop: bpy.props.EnumProperty(items=opsdata._get_assets_from_active_asset_type)  # type: ignore

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return bool(
            prefs.zsession_auth(context)
            and cache.project_active_get()
            and cache.asset_type_active_get()
        )

    def execute(self, context: bpy.types.Context) -> Set[str]:
        if not self.enum_prop:
            return {"CANCELLED"}

        # update kitsu metadata
        cache.asset_active_set_by_id(context, self.enum_prop)
        ui_redraw()
        return {"FINISHED"}

    def invoke(self, context, event):
        context.window_manager.invoke_search_popup(self)
        return {"FINISHED"}


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
        return bool(prefs.zsession_auth(context))

    def execute(self, context: bpy.types.Context) -> Set[str]:
        succeeded = []
        failed = []
        logger.info("-START- Pushing Metadata")
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
            shot = checkstrip.shot_exists_by_id(strip)
            if not shot:
                failed.append(strip)
                continue

            # push update to shot
            push.shot_meta(strip, shot)
            succeeded.append(strip)

        # end progress update
        context.window_manager.progress_update(len(selected_sequences))
        context.window_manager.progress_end()

        self.report(
            {"INFO"},
            f"Pushed Metadata of {len(succeeded)} Shots | Failed: {len(failed)}.",
        )
        logger.info("-END- Pushing Metadata")
        return {"FINISHED"}


class KITSU_OT_sqe_push_new_shot(bpy.types.Operator):
    """
    Operator that creates a new shot based on all selected sequencce strips to sevrer
    after performing various checks. Does not create shot if already exists to sevrer .
    """

    bl_idname = "kitsu.sqe_push_new_shot"
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
                and cache.project_active_get()
                and strip.kitsu.sequence_name
                and strip.kitsu.shot_name
            )

        return bool(prefs.zsession_auth(context) and cache.project_active_get())

    def execute(self, context: bpy.types.Context) -> Set[str]:

        if not self.confirm:
            self.report({"WARNING"}, "Submit new shots aborted.")
            return {"CANCELLED"}

        project_active = cache.project_active_get()
        succeeded = []
        failed = []
        logger.info("-START- Submitting new shots to: %s", project_active.name)

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
            zseq = checkstrip.seq_exists_by_name(strip, project_active)
            if not zseq:
                zseq = push.new_sequence(strip, project_active)

            # check if shot already to sevrer  > create it
            shot = checkstrip.shot_exists_by_name(strip, project_active, zseq)
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

        self.report(
            {"INFO"},
            f"Submitted {len(succeeded)} new shots | Failed: {len(failed)}",
        )
        logger.info("-END- Submitting new shots to: %s", project_active.name)
        ui_redraw()
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
    bl_options = {"INTERNAL"}

    sequence_name: bpy.props.StringProperty(
        name="Name", default="", description="Name of new sequence"
    )
    confirm: bpy.props.BoolProperty(name="confirm")

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        # needs to be logged in, active project
        return bool(prefs.zsession_auth(context) and cache.project_active_get())

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

        self.report(
            {"INFO"},
            f"Initiated {len(succeeded)} shots | Failed: {len(failed)}.",
        )
        logger.info("-END- Initializing shots")
        ui_redraw()
        return {"FINISHED"}


class KITSU_OT_sqe_link_sequence(bpy.types.Operator):
    """
    Gets all sequences that are available in server for active production and let's user select. Invokes a search Popup (enum_prop) on click.
    """

    bl_idname = "kitsu.sqe_link_sequence"
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

        ui_redraw()
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


class KITSU_OT_sqe_multi_edit_strip(bpy.types.Operator):
    """"""

    bl_idname = "kitsu.sqe_multi_edit_strip"
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
            shot = opsdata._resolve_pattern(shot_pattern, var_lookup_table)

            # set metadata
            strip.kitsu.sequence_name = sequence
            strip.kitsu.shot_name = shot

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


class KITSU_OT_sqe_pull_shot_meta(bpy.types.Operator):
    """
    Operator that pulls metadata of all selected sequencce strips from server
    after performing various checks. Metadata will be saved in strip.kitsu.
    """

    bl_idname = "kitsu.sqe_pull_shot_meta"
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
            shot = checkstrip.shot_exists_by_id(strip)
            if not shot:
                failed.append(strip)
                continue

            # push update to shot
            pull.shot_meta(strip, shot)
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


class KITSU_OT_sqe_uninit_strip(bpy.types.Operator):
    """
    Operator that deletes all  metadata of all selected sequencce strips
    after performing various checks. It does NOT change anything on server.
    """

    bl_idname = "kitsu.sqe_uninit_strip"
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

            # clear kitsu properties
            strip.kitsu.clear()
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
            s for s in selshots if s.kitsu.initialized and not s.kitsu.linked
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

            # clear kitsu properties
            shot_name = strip.kitsu.shot_name
            strip.kitsu.unlink()
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
        strips_to_unlink = [s for s in selshots if s.kitsu.linked]

        if len(strips_to_unlink) > 1:
            noun = "%i shots" % len(strips_to_unlink)
        else:
            noun = "this shot"

        col.prop(
            self,
            "confirm",
            text="Deletes link to server of %s. Only affects Sequence Editor." % noun,
        )


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
        return bool(prefs.zsession_auth(context) and context.selected_sequences)

    def execute(self, context: bpy.types.Context) -> Set[str]:
        if not self.confirm:
            self.report({"WARNING"}, "Push delete aborted.")
            return {"CANCELLED"}

        succeeded = []
        failed = []
        logger.info("-START- Deleting shots")

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
            shot = checkstrip.shot_exists_by_id(strip)
            if not shot:
                failed.append(strip)
                continue

            # delete shot
            push.delete_shot(strip, shot)
            succeeded.append(strip)

        # end progress update
        context.window_manager.progress_update(len(selected_sequences))
        context.window_manager.progress_end()

        self.report(
            {"INFO"},
            f"Deleted {len(succeeded)} shots | Failed: {len(failed)}",
        )
        logger.info("-END- Deleting shots")
        ui_redraw()
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
                    shot = checkstrip.shot_exists_by_id(strip)
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
        file_name = f"{strip.kitsu.shot_id}_{str(context.scene.frame_current)}.jpg"
        path = self._save_render(bpy.data.images["Render Result"], file_name)
        logger.info(
            f"Saved thumbnail of shot {strip.kitsu.shot_name} to {path.as_posix()}"
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
        shot = Shot.by_id(shot_id)

        # get task status 'wip' and task type 'Animation'
        task_status = TaskStatus.by_short_name("wip")
        task_type = TaskType.by_name("Animation")

        if not task_status:
            raise RuntimeError(
                "Failed to upload thumbnails. Task status: 'wip' is missing."
            )
        if not task_type:
            raise RuntimeError(
                "Failed to upload thumbnails. Task type: 'Animation' is missing."
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

        # create a comment, e.G 'set main thumbnail'
        comment = task.add_comment(task_status, comment="set main thumbnail")

        # add_preview_to_comment
        preview = task.add_preview_to_comment(comment, filepath.as_posix())

        # preview.set_main_preview()
        preview.set_main_preview()
        logger.info(f"Uploaded thumbnail for shot: {shot.name} under: {task_type.name}")

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


class KITSU_OT_create_playblast(bpy.types.Operator):
    """"""

    bl_idname = "kitsu.create_playblast"
    bl_label = "Create Playblast"

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return bool(prefs.zsession_auth(context) and cache.shot_active_get())

    def execute(self, context: bpy.types.Context) -> Set[str]:

        addon_prefs = prefs.addon_prefs_get(bpy.context)
        upload_queue: List[Path] = []  # will be used as successed list
        shot_active = cache.shot_active_get()
        noun = "Created"
        if addon_prefs.playblast_upload:
            noun = "Created and uploaded"

        logger.info("-START- Creating Playblast")

        context.window_manager.progress_begin(0, 2)

        # ----RENDER AND SAVE PLAYBLAST ------
        with self.override_render_settings(context):

            output_path = self._gen_playlast_path(context)
            bpy.ops.render.render(animation=True)
            upload_queue.append(output_path)

        context.window_manager.progress_update(1)

        # ----ULPOAD PLAYBLAST ------
        if addon_prefs.playblast_upload:
            # process thumbnail queue
            for idx, filepath in enumerate(upload_queue):
                self._upload_playblast(filepath)

        context.window_manager.progress_update(2)
        context.window_manager.progress_end()

        self.report({"INFO"}, f"{noun} playblast for {shot_active.name}")
        logger.info("-END- Creating Playblast")
        return {"FINISHED"}

    def _upload_playblast(self, filepath: Path) -> None:
        # get shot by id which is in filename of thumbnail
        shot_id = filepath.name.split("_")[0]
        shot = Shot.by_id(shot_id)

        # get task status 'wip' and task type 'Animation'
        task_status = TaskStatus.by_short_name("wip")
        task_type = TaskType.by_name("Animation")

        if not task_status:
            raise RuntimeError(
                "Failed to upload playblast. Task status: 'wip' is missing."
            )
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

        # create a comment, e.G 'set main thumbnail'
        comment = task.add_comment(task_status, comment="playblast")

        # add_preview_to_comment
        preview = task.add_preview_to_comment(comment, filepath.as_posix())
        # preview.set_main_preview()
        logger.info(f"Uploaded playblast for shot: {shot.name} under: {task_type.name}")

    def _gen_playlast_path(self, context: bpy.types.Context) -> Path:
        addon_prefs = prefs.addon_prefs_get(bpy.context)
        folder_name = addon_prefs.folder_playblasts

        # filename
        filename = self._gen_playblast_filename(context)

        # ensure folder exists
        folder_path = Path(folder_name).absolute()
        folder_path.mkdir(parents=True, exist_ok=True)

        path = folder_path.joinpath(filename)
        return path

    def _gen_playblast_filename(self, context: bpy.types.Context) -> str:
        version = "v001"
        shot_ative = cache.shot_active_get()
        file_name = f"{shot_ative.id}_{shot_ative.name}.{version}.mp4"
        return file_name

    @contextlib.contextmanager
    def override_render_settings(self, context):
        """Overrides the render settings for playblast creation"""
        addon_prefs = prefs.addon_prefs_get(context)
        rd = context.scene.render

        # Remember current render settings in order to restore them later.

        # filepath
        filepath = rd.filepath

        # engine
        engine = rd.engine

        # simplify
        use_simplify = rd.use_simplify

        # format render settings
        percentage = rd.resolution_percentage
        file_format = rd.image_settings.file_format
        ffmpeg_constant_rate = rd.ffmpeg.constant_rate_factor
        ffmpeg_codec = rd.ffmpeg.codec
        ffmpeg_format = rd.ffmpeg.format
        ffmpeg_audio_codec = rd.ffmpeg.audio_codec

        # stamp metadata settings
        metadata_input = rd.metadata_input = "SCENE"
        use_stamp_date = rd.use_stamp_date = False
        use_stamp_time = rd.use_stamp_time = False
        use_stamp_render_time = rd.use_stamp_render_time = False
        use_stamp_frame = rd.use_stamp_frame = True
        use_stamp_frame_range = rd.use_stamp_frame_range = False
        use_stamp_memory = rd.use_stamp_memory = False
        use_stamp_hostname = rd.use_stamp_hostname = False
        use_stamp_camera = rd.use_stamp_camera = False
        use_stamp_lens = rd.use_stamp_lens = True
        use_stamp_scene = rd.use_stamp_scene = False
        use_stamp_marker = rd.use_stamp_marker = False
        use_stamp_marker = rd.use_stamp_marker = False
        use_stamp_note = rd.use_stamp_note = True
        # rd.stamp_note_text = "Animator: <Name>"
        use_stamp = rd.use_stamp = True
        stamp_font_size = rd.stamp_font_size = 12
        stamp_foreground = rd.stamp_foreground = (0.8, 0.8, 0.8, 1)
        stamp_background = rd.stamp_background = (0, 0, 0, 0.25)
        use_stamp_labels = rd.use_stamp_labels = True

        try:
            # filepath
            rd.filepath = self._gen_playlast_path(context).as_posix()

            # engine
            rd.engine = addon_prefs.playblast_engine

            # simplify
            rd.use_simplify = False

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
            # rd.stamp_note_text = "Animator: <Name>"
            rd.use_stamp = True
            rd.stamp_font_size = 12
            rd.stamp_foreground = (0.8, 0.8, 0.8, 1)
            rd.stamp_background = (0, 0, 0, 0.25)
            rd.use_stamp_labels = True

            yield

        finally:
            # filepath
            rd.filepath = filepath

            # engine
            rd.engine = engine

            # simplify
            rd.use_simplify = use_simplify

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
            # rd.stamp_note_text = "Animator: <Name>"
            rd.use_stamp = use_stamp
            rd.stamp_font_size = stamp_font_size
            rd.stamp_foreground = stamp_foreground
            rd.stamp_background = stamp_background
            rd.use_stamp_labels = use_stamp_labels


class KITSU_OT_sqe_debug_duplicates(bpy.types.Operator):
    """"""

    bl_idname = "kitsu.sqe_debug_duplicates"
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


class KITSU_OT_sqe_debug_not_linked(bpy.types.Operator):
    """"""

    bl_idname = "kitsu.sqe_debug_not_linked"
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


class KITSU_OT_sqe_debug_multi_project(bpy.types.Operator):
    """"""

    bl_idname = "kitsu.sqe_debug_multi_project"
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
    KITSU_OT_session_start,
    KITSU_OT_session_end,
    KITSU_OT_productions_load,
    KITSU_OT_sequences_load,
    KITSU_OT_shots_load,
    KITSU_OT_asset_types_load,
    KITSU_OT_assets_load,
    KITSU_OT_sqe_push_new_sequence,
    KITSU_OT_sqe_push_new_shot,
    KITSU_OT_sqe_push_shot_meta,
    KITSU_OT_sqe_uninit_strip,
    KITSU_OT_sqe_unlink_shot,
    KITSU_OT_sqe_init_strip,
    KITSU_OT_sqe_link_shot,
    KITSU_OT_sqe_link_sequence,
    KITSU_OT_sqe_push_thumbnail,
    KITSU_OT_create_playblast,
    KITSU_OT_sqe_push_del_shot,
    KITSU_OT_sqe_pull_shot_meta,
    KITSU_OT_sqe_multi_edit_strip,
    KITSU_OT_sqe_debug_duplicates,
    KITSU_OT_sqe_debug_not_linked,
    KITSU_OT_sqe_debug_multi_project,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
