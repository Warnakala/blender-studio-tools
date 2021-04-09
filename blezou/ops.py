from dataclasses import asdict
from pathlib import Path
import copy
import re
import contextlib
from typing import Set, Dict, Union, List, Tuple, Any, Optional, cast
import bpy
import importlib
from .types import (
    ZProductions,
    ZProject,
    ZSequence,
    ZShot,
    ZAssetType,
    ZAsset,
    ZTask,
    ZTaskType,
    ZTaskStatus,
    ZCache,
)
from .util import *
from .core import ui_redraw
from . import props
from . import prefs
from .logger import ZLoggerFactory
from .gazu import gazu
from . import opsdata

logger = ZLoggerFactory.getLogger(name=__name__)


class BZ_OT_SessionStart(bpy.types.Operator):
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
        zsession = zsession_get(context)

        zsession.set_config(self.get_config(context))
        zsession.start()

        # init cache variables
        prefs.init_cache_variables(context=context)
        props.init_cache_variables(context=context)

        return {"FINISHED"}

    def get_config(self, context: bpy.types.Context) -> Dict[str, str]:
        addon_prefs = addon_prefs_get(context)
        return {
            "email": addon_prefs.email,
            "host": addon_prefs.host,
            "passwd": addon_prefs.passwd,
        }


class BZ_OT_SessionEnd(bpy.types.Operator):
    """
    Ends the ZSession which is stored in Blezou addon preferences.
    """

    bl_idname = "blezou.session_end"
    bl_label = "End Gazou Session"
    bl_options = {"INTERNAL"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return zsession_auth(context)

    def execute(self, context: bpy.types.Context) -> Set[str]:
        zsession = zsession_get(context)
        zsession.end()
        # clear cache variables
        props.clear_cache_variables()
        prefs.clear_cache_variables()
        return {"FINISHED"}


class BZ_OT_ProductionsLoad(bpy.types.Operator):
    """
    Gets all productions that are available in server and let's user select. Invokes a search Popup (enum_prop) on click.
    """

    bl_idname = "blezou.productions_load"
    bl_label = "Productions Load"
    bl_options = {"INTERNAL"}
    bl_property = "enum_prop"

    def _get_productions(
        self, context: bpy.types.Context
    ) -> List[Tuple[str, str, str]]:

        if not zsession_auth(context):
            return []

        zproductions = ZProductions()
        enum_list = [
            (p.id, p.name, p.description if p.description else "")
            for p in zproductions.projects
        ]
        return enum_list

    enum_prop: bpy.props.EnumProperty(items=_get_productions)  # type: ignore

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return zsession_auth(context)

    def execute(self, context: bpy.types.Context) -> Set[str]:
        # store vars to check if project / seq / shot changed
        project_prev_id = zproject_active_get().id

        # update blezou metadata
        zproject_active_set_by_id(context, self.enum_prop)

        # clear active shot when sequence changes
        if self.enum_prop != project_prev_id:
            zsequence_active_reset(context)
            zasset_type_active_reset(context)
            zshot_active_reset(context)
            zasset_active_reset(context)

        ui_redraw()
        return {"FINISHED"}

    def invoke(self, context, event):
        context.window_manager.invoke_search_popup(self)
        return {"FINISHED"}


class BZ_OT_SequencesLoad(bpy.types.Operator):
    """
    Gets all sequences that are available in server for active production and let's user select. Invokes a search Popup (enum_prop) on click.
    """

    bl_idname = "blezou.sequences_load"
    bl_label = "Sequences Load"
    bl_options = {"INTERNAL"}
    bl_property = "enum_prop"

    # TODO: reduce api request to one, we request in _get_sequences and also in execute to set sequence_active

    def _get_sequences(self, context: bpy.types.Context) -> List[Tuple[str, str, str]]:
        zproject_active = zproject_active_get()

        enum_list = [
            (s.id, s.name, s.description if s.description else "")
            for s in zproject_active.get_sequences_all()
        ]
        return enum_list

    enum_prop: bpy.props.EnumProperty(items=_get_sequences)  # type: ignore

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return bool(zsession_auth(context) and zproject_active_get())

    def execute(self, context: bpy.types.Context) -> Set[str]:

        # store vars to check if project / seq / shot changed
        zseq_prev_id = zsequence_active_get().id

        # update blezou metadata
        zsequence_active_set_by_id(context, self.enum_prop)

        # clear active shot when sequence changes
        if self.enum_prop != zseq_prev_id:
            zshot_active_reset(context)

        ui_redraw()
        return {"FINISHED"}

    def invoke(self, context, event):
        context.window_manager.invoke_search_popup(self)
        return {"FINISHED"}


class BZ_OT_ShotsLoad(bpy.types.Operator):
    """
    Gets all sequences that are available in server for active production and let's user select. Invokes a search Popup (enum_prop) on click.
    """

    bl_idname = "blezou.shots_load"
    bl_label = "Shots Load"
    bl_options = {"INTERNAL"}
    bl_property = "enum_prop"

    # TODO: reduce api request to one, we request in _get_shots and also in execute to set active shot

    def _get_shots(self, context: bpy.types.Context) -> List[Tuple[str, str, str]]:
        zseq_active = zsequence_active_get()

        enum_list = [
            (s.id, s.name, s.description if s.description else "")
            for s in zseq_active.get_all_shots()
        ]
        return enum_list

    enum_prop: bpy.props.EnumProperty(items=_get_shots)  # type: ignore

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        # only if session is auth active_project and active sequence selected
        return bool(
            zsession_auth(context) and zsequence_active_get() and zproject_active_get()
        )

    def execute(self, context: bpy.types.Context) -> Set[str]:
        # update blezou metadata
        if self.enum_prop:
            zshot_active_set_by_id(context, self.enum_prop)
        ui_redraw()
        return {"FINISHED"}

    def invoke(self, context, event):
        context.window_manager.invoke_search_popup(self)
        return {"FINISHED"}


class BZ_OT_AssetTypesLoad(bpy.types.Operator):
    """
    Gets all sequences that are available in server for active production and let's user select. Invokes a search Popup (enum_prop) on click.
    """

    bl_idname = "blezou.asset_types_load"
    bl_label = "Assettyes Load"
    bl_options = {"INTERNAL"}
    bl_property = "enum_prop"

    # TODO: reduce api request to one, we request in _get_sequences and also in execute to set sequence_active

    def _get_assetypes(self, context: bpy.types.Context) -> List[Tuple[str, str, str]]:
        zproject_active = zproject_active_get()
        enum_list = [
            (at.id, at.name, "") for at in zproject_active.get_all_asset_types()
        ]
        return enum_list

    enum_prop: bpy.props.EnumProperty(items=_get_assetypes)  # type: ignore

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return bool(zsession_auth(context) and zproject_active_get())

    def execute(self, context: bpy.types.Context) -> Set[str]:
        # store vars to check if project / seq / shot changed
        asset_type_prev_id = zasset_type_active_get().id

        # update blezou metadata
        zasset_type_active_set_by_id(context, self.enum_prop)

        # clear active shot when sequence changes
        if self.enum_prop != asset_type_prev_id:
            zasset_active_reset(context)

        ui_redraw()
        return {"FINISHED"}

    def invoke(self, context, event):
        context.window_manager.invoke_search_popup(self)
        return {"FINISHED"}


class BZ_OT_AssetsLoad(bpy.types.Operator):
    """
    Gets all sequences that are available in server for active production and let's user select. Invokes a search Popup (enum_prop) on click.
    """

    bl_idname = "blezou.assets_load"
    bl_label = "Assets Load"
    bl_options = {"INTERNAL"}
    bl_property = "enum_prop"

    # TODO: reduce api request to one, we request in _get_sequences and also in execute to set sequence_active

    def _get_assets(self, context: bpy.types.Context) -> List[Tuple[str, str, str]]:
        zproject_active = zproject_active_get()
        zasset_type_active = zasset_type_active_get()

        enum_list = [
            (a.id, a.name, a.description if a.description else "")
            for a in zproject_active.get_all_assets_for_type(zasset_type_active)
        ]
        return enum_list

    enum_prop: bpy.props.EnumProperty(items=_get_assets)  # type: ignore

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return bool(
            zsession_auth(context)
            and zproject_active_get()
            and zasset_type_active_get()
        )

    def execute(self, context: bpy.types.Context) -> Set[str]:
        if not self.enum_prop:
            return {"CANCELED"}

        # update blezou metadata
        zasset_active_set_by_id(context, self.enum_prop)
        ui_redraw()
        return {"FINISHED"}

    def invoke(self, context, event):
        context.window_manager.invoke_search_popup(self)
        return {"FINISHED"}


class Pull:
    """Class that contains staticmethods to pull data from gazou data base into Blender"""

    @staticmethod
    def shot_meta(strip: bpy.types.Sequence, zshot: ZShot) -> None:
        # clear cache before pulling
        ZCache.clear_all()

        # update sequence props
        zseq = ZSequence.by_id(zshot.parent_id)
        strip.blezou.sequence_id = zseq.id
        strip.blezou.sequence_name = zseq.name

        # update shot props
        strip.blezou.shot_id = zshot.id
        strip.blezou.shot_name = zshot.name
        strip.blezou.shot_description = zshot.description if zshot.description else ""

        # update project props
        zproject = ZProject.by_id(zshot.project_id)
        strip.blezou.project_id = zproject.id
        strip.blezou.project_name = zproject.name

        # update meta props
        strip.blezou.initialized = True
        strip.blezou.linked = True
        logger.info("Pulled meta from shot: %s to strip: %s" % (zshot.name, strip.name))


class Push:
    """Class that contains staticmethods to push data from blender to gazou data base"""

    @staticmethod
    def shot_meta(strip: bpy.types.Sequence, zshot: ZShot) -> None:

        # update shot info
        zshot.name = strip.blezou.shot_name
        zshot.description = strip.blezou.shot_description
        frame_range = Push._remap_frame_range(
            strip.frame_final_start, strip.frame_final_end
        )
        zshot.data["frame_in"] = frame_range[0]
        zshot.data["frame_out"] = frame_range[1]

        # update sequence info if changed
        if not zshot.sequence_name == strip.blezou.sequence_name:
            zseq = ZSequence.by_id(strip.blezou.sequence_id)
            zshot.sequence_id = zseq.id
            zshot.parent_id = zseq.id
            zshot.sequence_name = zseq.name

        # update in gazou
        zshot.update()
        logger.info("Pushed meta to shot: %s from strip: %s" % (zshot.name, strip.name))

    @staticmethod
    def new_shot(
        strip: bpy.types.Sequence,
        zsequence: ZSequence,
        zproject: ZProject,
    ) -> ZShot:

        frame_range = Push._remap_frame_range(
            strip.frame_final_start, strip.frame_final_end
        )
        zshot = zproject.create_shot(
            strip.blezou.shot_name,
            zsequence,
            frame_in=frame_range[0],
            frame_out=frame_range[1],
        )
        # update description, no option to pass that on create
        if strip.blezou.shot_description:
            zshot.description = strip.blezou.shot_description
            zshot.update()

        # set project name locally, will be available on next pull
        zshot.project_name = zproject.name
        logger.info(
            "Pushed create shot: %s for project: %s" % (zshot.name, zproject.name)
        )
        return zshot

    @staticmethod
    def new_sequence(strip: bpy.types.Sequence, zproject: ZProject) -> ZSequence:
        zsequence = zproject.create_sequence(
            strip.blezou.sequence_name,
        )
        logger.info(
            "Pushed create sequence: %s for project: %s"
            % (zsequence.name, zproject.name)
        )
        return zsequence

    @staticmethod
    def delete_shot(strip: bpy.types.Sequence, zshot: ZShot) -> str:
        result = zshot.remove()
        logger.info(
            "Pushed delete shot: %s for project: %s"
            % (zshot.name, zshot.project_name if zshot.project_name else "Unknown")
        )
        strip.blezou.clear()
        return result

    @staticmethod
    def _remap_frame_range(frame_in, frame_out):
        start_frame = 101
        nb_of_frames = frame_out - frame_in
        return (start_frame, start_frame + nb_of_frames)


class CheckStrip:
    """Class that contains various static methods to perform checks on sequence strips"""

    @staticmethod
    def initialized(strip: bpy.types.Sequence) -> bool:
        """Returns True if strip.blezou.initialized is True else False"""
        if not strip.blezou.initialized:
            logger.info("Strip: %s. Not initialized." % strip.name)
            return False
        else:
            logger.info("Strip: %s. Is initialized." % strip.name)
            return True

    @staticmethod
    def linked(strip: bpy.types.Sequence) -> bool:
        """Returns True if strip.blezou.linked is True else False"""
        if not strip.blezou.linked:
            logger.info("Strip: %s. Not linked yet." % strip.name)
            return False
        else:
            logger.info(
                "Strip: %s. Is linked to ID: %s." % (strip.name, strip.blezou.shot_id)
            )
            return True

    @staticmethod
    def has_meta(strip: bpy.types.Sequence) -> bool:
        """Returns True if strip.blezou.shot_name and strip.blezou.sequence_name is Truethy else False"""
        seq = strip.blezou.sequence_name
        shot = strip.blezou.shot_name
        if not bool(seq and shot):
            logger.info("Strip: %s. Missing metadata." % strip.name)
            return False
        else:
            logger.info(
                "Strip: %s. Has metadata (Sequence: %s, Shot: %s)."
                % (strip.name, seq, shot)
            )
            return True

    @staticmethod
    def shot_exists_by_id(strip: bpy.types.Sequence) -> Optional[ZShot]:
        """Returns ZShot instance if shot with strip.blezou.shot_id exists else None"""

        ZCache.clear_all()

        try:
            zshot = ZShot.by_id(strip.blezou.shot_id)
        except gazu.exception.RouteNotFoundException:
            logger.error(
                "Strip: %s Shot ID: %s not found on server anymore. Was maybe deleted?"
                % (strip.name, strip.blezou.shot_id)
            )
            return None
        if zshot:
            logger.info(
                "Strip: %s Shot %s exists on server (ID: %s)."
                % (strip.name, zshot.name, zshot.id)
            )
            return zshot
        else:
            logger.info(
                "Strip: %s Shot %s does not exist on server (ID: %s)"
                % (strip.name, zshot.name, strip.blezou.shot_id)
            )
            return None

    @staticmethod
    def seq_exists_by_name(
        strip: bpy.types.Sequence, zproject: ZProject
    ) -> Optional[ZSequence]:
        """Returns ZSequence instance if strip.blezou.sequence_name exists in gazou, else None"""

        ZCache.clear_all()

        zseq = zproject.get_sequence_by_name(strip.blezou.sequence_name)
        if zseq:
            logger.info(
                "Strip: %s Sequence %s exists in on server (ID: %s)."
                % (strip.name, zseq.name, zseq.id)
            )
            return zseq
        else:
            logger.info(
                "Strip: %s Sequence %s does not exist on server."
                % (strip.name, strip.blezou.sequence_name)
            )
            return None

    @staticmethod
    def shot_exists_by_name(
        strip: bpy.types.Sequence, zproject: ZProject, zsequence: ZSequence
    ) -> Optional[ZShot]:
        """Returns ZShot instance if strip.blezou.shot_name exists in gazou, else None."""

        ZCache.clear_all()

        zshot = zproject.get_shot_by_name(zsequence, strip.blezou.shot_name)
        if zshot:
            logger.info(
                "Strip: %s Shot already existent on server (ID: %s)."
                % (strip.name, zshot.id)
            )
            return zshot
        else:
            logger.info(
                "Strip: %s Shot %s does not exist on server."
                % (strip.name, strip.blezou.shot_name)
            )
            return None

    @staticmethod
    def contains(strip: bpy.types.Sequence, framenr: int) -> bool:
        """Returns True if the strip covers the given frame number"""
        return int(strip.frame_final_start) <= framenr <= int(strip.frame_final_end)


class BZ_OT_SQE_PushShotMeta(bpy.types.Operator):
    """
    Operator that pushes metadata of all selected sequencce strips to gazou
    after performing various checks. Metadata is saved in strip.blezou.
    """

    bl_idname = "blezou.sqe_push_shot_meta"
    bl_label = "Push Shot Metadata"
    bl_options = {"INTERNAL"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return bool(zsession_auth(context))

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

            # only if strip is linked to gazou
            if not CheckStrip.linked(strip):
                failed.append(strip)
                continue

            # check if shot is still available by id
            zshot = CheckStrip.shot_exists_by_id(strip)
            if not zshot:
                failed.append(strip)
                continue

            # push update to shot
            Push.shot_meta(strip, zshot)
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


class BZ_OT_SQE_PushNewShot(bpy.types.Operator):
    """
    Operator that creates a new shot based on all selected sequencce strips to gazou
    after performing various checks. Does not create shot if already exists on gazou.
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
                zsession_auth(context)
                and zproject_active_get()
                and strip.blezou.sequence_name
                and strip.blezou.shot_name
            )

        return bool(zsession_auth(context) and zproject_active_get())

    def execute(self, context: bpy.types.Context) -> Set[str]:

        if not self.confirm:
            self.report({"WARNING"}, "Submit new aborted.")
            return {"CANCELLED"}

        zproject_active = zproject_active_get()
        succeeded = []
        failed = []
        logger.info("-START- Blezou submitting new shots to: %s" % zproject_active.name)

        # begin progress update
        selected_sequences = context.selected_sequences
        if not selected_sequences:
            selected_sequences = context.scene.sequence_editor.sequences_all

        context.window_manager.progress_begin(0, len(selected_sequences))

        for idx, strip in enumerate(selected_sequences):
            context.window_manager.progress_update(idx)

            # check if user initialized shot
            if not CheckStrip.initialized(strip):
                failed.append(strip)
                continue

            # check if strip is already linked to gazou
            if CheckStrip.linked(strip):
                failed.append(strip)
                continue

            # check if user provided enough info
            if not CheckStrip.has_meta(strip):
                failed.append(strip)
                continue

            # check if seq already on gazou > create it
            zseq = CheckStrip.seq_exists_by_name(strip, zproject_active)
            if not zseq:
                zseq = Push.new_sequence(strip, zproject_active)

            # check if shot already on gazou > create it
            zshot = CheckStrip.shot_exists_by_name(strip, zproject_active, zseq)
            if zshot:
                failed.append(strip)
                continue

            # push update to shot
            zshot = Push.new_shot(strip, zseq, zproject_active)
            Pull.shot_meta(strip, zshot)
            succeeded.append(strip)

        # end progress update
        context.window_manager.progress_update(len(selected_sequences))
        context.window_manager.progress_end()

        self.report(
            {"INFO"},
            f"Submitted {len(succeeded)} new shots | Failed: {len(failed)}",
        )
        logger.info("-END- Blezou submitting new shots to: %s" % zproject_active.name)
        ui_redraw()
        return {"FINISHED"}

    def invoke(self, context, event):
        self.confirm = False
        return context.window_manager.invoke_props_dialog(self, width=500)

    def draw(self, context):
        zproject_active = zproject_active_get()
        selected_sequences = context.selected_sequences

        if not selected_sequences:
            selected_sequences = context.scene.sequence_editor.sequences_all

        if len(selected_sequences) > 1:
            noun = "%i Shots" % len(selected_sequences)
        else:
            noun = "this Shot"

        if not zproject_active:
            prod_load_text = "Select Production"
        else:
            prod_load_text = zproject_active.name

        # UI
        layout = self.layout

        # Production
        row = layout.row()
        row.enabled = False
        row.operator(
            BZ_OT_ProductionsLoad.bl_idname, text=prod_load_text, icon="DOWNARROW_HLT"
        )

        # confirm dialog
        col = layout.column()
        col.prop(
            self,
            "confirm",
            text="Submit %s to server. Will skip shots if they already exist."
            % (noun.lower()),
        )


class BZ_OT_SQE_InitShot(bpy.types.Operator):
    """
    Operator that initializes a regular sequence strip to a 'blezou' shot.
    Only sets strip.blezou.initialized = True. But this is required for further
    operations and to  differentiate between regular sequence strip and blezou shot strip.
    """

    bl_idname = "blezou.sqe_init_shot"
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
            if strip.blezou.initialized:
                logger.info("%s already initialized." % strip.name)
                failed.append(strip)
                continue

            strip.blezou.initialized = True
            succeeded.append(strip)
            logger.info("Initialized strip: %s as shot." % strip.name)

        self.report(
            {"INFO"},
            f"Initialized {len(succeeded)} shots | Failed: {len(failed)}.",
        )
        logger.info("-END- Initializing shots")
        ui_redraw()
        return {"FINISHED"}


class BZ_OT_SQE_InitShotBulk(bpy.types.Operator):
    """
    Operator that initializes a regular sequence strip to a 'blezou' shot.
    Only sets strip.blezou.initialized = True. But this is required for further
    operations and to  differentiate between regular sequence strip and blezou shot strip.
    """

    bl_idname = "blezou.sqe_init_shot_bulkd"
    bl_label = "Bulk Initialize Shots"
    bl_description = "Adds required shot metadata to selecetd strips"

    # Property Functions
    def _get_active_project(self) -> str:
        return zproject_active_get().name

    def _get_sequences(self, context: bpy.types.Context) -> List[Tuple[str, str, str]]:
        zproject_active = zproject_active_get()
        if not zproject_active:
            return []

        enum_list = [
            (s.name, s.name, s.description if s.description else "")
            for s in zproject_active.get_sequences_all()
        ]
        return enum_list

    def _gen_shot_preview(self):
        examples: List[str] = []

        var_project = (
            self.var_project_custom
            if self.var_use_custom_project
            else self.var_project_active
        )
        var_sequence = (
            self.var_sequence_custom if self.var_use_custom_seq else self.sequence_enum
        )
        shot_pattern = addon_prefs_get(bpy.context).shot_pattern
        var_lookup_table = {"Sequence": var_sequence, "Project": var_project}

        for count in range(3):
            counter_number = self.counter_start + (self.counter_increment * count)
            counter = str(counter_number).rjust(self.counter_digits, "0")
            var_lookup_table["Counter"] = counter
            examples.append(opsdata._resolve_pattern(shot_pattern, var_lookup_table))

        return ", ".join(examples) + "..."

    # Property Definitions
    var_use_custom_seq: bpy.props.BoolProperty(
        name="Use Custom",
        description="Enables to type in custom sequence name for <Sequence> wildcard.",
    )  # type: ignore
    var_use_custom_project: bpy.props.BoolProperty(
        name="Use Custom",
        description="Enables to type in custom project name for <Project> wildcard",
    )  # type: ignore
    var_sequence_custom: bpy.props.StringProperty(  # type: ignore
        name="Sequence",
        description="Value that will be used to insert in <Sequence> wildcard if custom sequence is enabled.",
        default="",
    )
    var_project_custom: bpy.props.StringProperty(  # type: ignore
        name="Project",
        description="Value that will be used to insert in <Project> wildcard if custom project is enabled.",
        default="",
    )
    var_project_active: bpy.props.StringProperty(
        name="Active Project",
        description="Value that will be used to insert in <Project> wildcard",
        get=_get_active_project,
    )
    use_sequence_new: bpy.props.BoolProperty(
        name="New",
        description="Instead of dropdown menu to select existing sequences, check this to type in new sequence name.",
    )
    sequence_enum: bpy.props.EnumProperty(
        items=_get_sequences,
        description="Name of Sequence the generated Shots will be assinged to.",
    )
    sequence_new: bpy.props.StringProperty(  # type: ignore
        name="Sequence",
        description="Name of the new Sequence that the shots will belong to.",
        default="",
    )
    counter_digits: bpy.props.IntProperty(  # type: ignore
        name="Counter Digits",
        description="How many digits the counter should contain.",
        default=4,
        min=0,
    )
    counter_start: bpy.props.IntProperty(  # type: ignore
        name="Counter Start",
        description="Value that defines where the shot counter starts.",
        step=10,
        min=0,
    )
    counter_increment: bpy.props.IntProperty(  # type: ignore
        name="Counter Incr",
        description="By which Increment counter should be increased.",
        default=10,
        step=5,
        min=0,
    )

    shot_preview: bpy.props.StringProperty(  # type: ignore
        name="Shot Pattern",
        description="Preview result of current settings on how a shot will be named.",
        get=_gen_shot_preview,
    )

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        nr_of_shots = len(context.selected_sequences)
        return bool(nr_of_shots > 1 or nr_of_shots == 0)

    def execute(self, context: bpy.types.Context) -> Set[str]:
        succeeded = []
        failed = []
        logger.info("-START- Bulk Initializing Shots")

        # sort sequence after frame in
        selected_sequences = context.selected_sequences
        if not selected_sequences:
            selected_sequences = context.scene.sequence_editor.sequences_all

        selected_sequences = sorted(
            selected_sequences, key=lambda x: x.frame_final_start
        )

        for idx, strip in enumerate(selected_sequences):
            if strip.blezou.initialized:
                logger.info("%s already initialized." % strip.name)
                failed.append(strip)
                continue

            # gen data for resolver
            var_project = (
                self.var_project_custom
                if self.var_use_custom_project
                else self.var_project_active
            )
            var_sequence = (
                self.var_sequence_custom
                if self.var_use_custom_seq
                else self.sequence_enum
            )
            counter_number = self.counter_start + (self.counter_increment * idx)
            counter = str(counter_number).rjust(self.counter_digits, "0")
            var_lookup_table = {
                "Sequence": var_sequence,
                "Project": var_project,
                "Counter": counter,
            }
            shot_pattern = addon_prefs_get(context).shot_pattern
            sequence = (
                self.sequence_new if self.use_sequence_new else self.sequence_enum
            )
            shot = opsdata._resolve_pattern(shot_pattern, var_lookup_table)

            strip.blezou.initialized = True
            strip.blezou.sequence_name = sequence
            strip.blezou.shot_name = shot
            succeeded.append(strip)
            logger.info("Initialized strip: %s as shot: %s" % (strip.name, shot))

        self.report(
            {"INFO"},
            f"Initialized {len(succeeded)} shots | Failed: {len(failed)}.",
        )
        logger.info("-END- Bulk Initializing Shots")
        ui_redraw()
        return {"FINISHED"}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=500)

    def draw(self, context):
        selected_sequences = context.selected_sequences
        if not selected_sequences:
            selected_sequences = context.scene.sequence_editor.sequences_all
        # noun = "%i shots" % len(selected_sequences)

        # UI
        layout = self.layout
        row = layout.row()
        row.label(text=f"{len(selected_sequences)} Shots")

        # Sequence
        row = layout.row()
        row.label(text="Sequence")
        row = layout.row()
        box = row.box()
        row = box.row(align=True)
        row.prop(self, "use_sequence_new", text="New")
        if self.use_sequence_new:
            row.prop(self, "sequence_new", text="Sequence")
        else:
            row.prop(self, "sequence_enum", text="Sequence")

        # Counter
        row = layout.row()
        row.label(text="Counter Settings")
        row = layout.row()
        box = row.box()
        box.row().prop(self, "counter_digits", text="Digits")
        box.row().prop(self, "counter_increment", text="Increment")
        box.row().prop(self, "counter_start", text="Start")

        # varaibles
        row = layout.row()
        row.label(text="Variables")
        row = layout.row()
        box = row.box()

        # sequence
        row = box.row(align=True)
        row.prop(self, "var_use_custom_seq", text="Custom")
        if self.var_use_custom_seq:
            row.prop(self, "var_sequence_custom", text="Sequence")
        else:
            row.prop(self, "sequence_enum", text="Sequence")

        # project
        row = box.row(align=True)
        row.prop(self, "var_use_custom_project", text="Custom")
        if self.var_use_custom_project:
            row.prop(self, "var_project_custom", text="Project")
        else:
            row.prop(self, "var_project_active", text="Project")

        # pattern
        row = layout.row()
        row.label(text="Shot Pattern")
        row = layout.row()
        box = row.box()
        box.row().prop(addon_prefs_get(context), "shot_pattern", text="Shot Pattern")
        box.row().prop(self, "shot_preview", text="Preview")


class BZ_OT_SQE_LinkSequence(bpy.types.Operator):
    """
    Gets all sequences that are available in server for active production and let's user select. Invokes a search Popup (enum_prop) on click.
    """

    bl_idname = "blezou.sqe_link_sequence"
    bl_label = "Link Sequence"
    bl_options = {"INTERNAL"}
    bl_property = "enum_prop"

    def _get_sequences(self, context: bpy.types.Context) -> List[Tuple[str, str, str]]:
        zproject_active = zproject_active_get()

        if not zproject_active:
            return []

        enum_list = [
            (s.id, s.name, s.description if s.description else "")
            for s in zproject_active.get_sequences_all()
        ]
        return enum_list

    enum_prop: bpy.props.EnumProperty(items=_get_sequences)  # type: ignore

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        strip = context.scene.sequence_editor.active_strip
        return bool(
            zsession_auth(context)
            and zproject_active_get()
            and strip
            and context.selected_sequences
        )

    def execute(self, context: bpy.types.Context) -> Set[str]:
        strip = context.scene.sequence_editor.active_strip
        sequence_id = self.enum_prop
        if not sequence_id:
            return {"CANCELED"}

        # set sequence properties
        zseq = ZSequence.by_id(sequence_id)
        strip.blezou.sequence_name = zseq.name
        strip.blezou.sequence_id = zseq.id

        ui_redraw()
        return {"FINISHED"}

    def invoke(self, context, event):
        context.window_manager.invoke_search_popup(self)
        return {"FINISHED"}


class BZ_OT_SQE_LinkShot(bpy.types.Operator):
    """
    Operator that invokes ui which shows user all available shots in gazou.
    It is used to 'link' a seqeunce strip to an alredy existent shot in gazou.
    Fills out all metadata after selecting shot.
    """

    bl_idname = "blezou.sqe_link_shot"
    bl_label = "Link Shot"
    bl_description = (
        "Adds required shot metadata to selecetd strip based on data from server."
    )
    bl_property = "enum_prop"

    def _get_shots(self, context: bpy.types.Context) -> List[Tuple[str, str, str]]:
        zproject_active = zproject_active_get()

        if not zproject_active:
            return []

        enum_list = []
        all_sequences = zproject_active.get_sequences_all()
        for seq in all_sequences:
            all_shots = seq.get_all_shots()
            if len(all_shots) > 0:
                enum_list.append(
                    ("", seq.name, seq.description if seq.description else "")
                )
                for shot in all_shots:
                    enum_list.append(
                        (
                            shot.id,
                            shot.name,
                            shot.description if shot.description else "",
                        )
                    )
        return enum_list

    enum_prop: bpy.props.EnumProperty(items=_get_shots, name="Shot")  # type: ignore

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return bool(
            zsession_auth(context)
            and zproject_active_get()
            and context.scene.sequence_editor.active_strip
            and context.selected_sequences
        )

    def execute(self, context: bpy.types.Context) -> Set[str]:
        strip = context.scene.sequence_editor.active_strip

        if self.enum_prop:  # returns 0 for organisational item
            zshot = ZShot.by_id(self.enum_prop)
            Pull.shot_meta(strip, zshot)
            logger.info(
                "Linked strip: %s to shot: %s with ID: %s"
                % (strip.name, zshot.name, zshot.id)
            )

        ui_redraw()
        return {"FINISHED"}

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event) -> Set[str]:
        return context.window_manager.invoke_props_dialog(  # type: ignore
            self, width=500
        )


class BZ_OT_SQE_PullShotMeta(bpy.types.Operator):
    """
    Operator that pulls metadata of all selected sequencce strips from gazou
    after performing various checks. Metadata will be saved in strip.blezou.
    """

    bl_idname = "blezou.sqe_pull_shot_meta"
    bl_label = "Pull Shot Metadata"
    bl_options = {"INTERNAL"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return bool(zsession_auth(context))

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

            # only if strip is linked to gazou
            if not CheckStrip.linked(strip):
                failed.append(strip)
                continue

            # check if shot is still available by id
            zshot = CheckStrip.shot_exists_by_id(strip)
            if not zshot:
                failed.append(strip)
                continue

            # push update to shot
            Pull.shot_meta(strip, zshot)
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


class BZ_OT_SQE_DelShotMeta(bpy.types.Operator):
    """
    Operator that deletes all  metadata of all selected sequencce strips
    after performing various checks. It does NOT change anything in gazou.
    """

    bl_idname = "blezou.sqe_del_shot_meta"
    bl_label = "Delete Shot Metadata"
    bl_description = "Cleares shot metadata of selecetd strips. Only affects Sequence Editor. Link to server will be lost. "
    confirm: bpy.props.BoolProperty(name="Confirm")

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return bool(context.selected_sequences)

    def execute(self, context: bpy.types.Context) -> Set[str]:
        if not self.confirm:
            self.report({"WARNING"}, "Clearing metadata aborted.")
            return {"CANCELLED"}

        failed: List[bpy.types.Sequence] = []
        succeeded: List[bpy.types.Sequence] = []
        logger.info("-START- Deleting shot metadata")

        for strip in context.selected_sequences:
            if not CheckStrip.initialized(strip):
                failed.append(strip)
                continue

            # clear blezou properties
            strip.blezou.clear()
            succeeded.append(strip)
            logger.info("Cleared metadata and uninitialized strip: %s" % strip.name)

        self.report(
            {"INFO"},
            f"Cleared metadata of {len(succeeded)} shots | Failed: {len(failed)}.",
        )
        logger.info("-END- Deleting shot metadata")
        ui_redraw()
        return {"FINISHED"}

    def invoke(self, context, event):
        self.confirm = False
        return context.window_manager.invoke_props_dialog(self, width=500)

    def draw(self, context):
        layout = self.layout
        col = layout.column()

        selshots = context.selected_sequences
        if len(selshots) > 1:
            noun = "%i shots" % len(selshots)
        else:
            noun = "this shot"

        col.prop(
            self,
            "confirm",
            text="Cleares metadata of %s. Only affects Sequence Editor. Link to server will be lost."
            % noun,
        )


class BZ_OT_SQE_PushDeleteShot(bpy.types.Operator):
    """
    Operator that deletes all  metadata of all selected sequencce strips
    after performing various checks. It does NOT change anything in gazou.
    """

    bl_idname = "blezou.sqe_push_del_shot"
    bl_label = "Delete Shot"
    bl_description = "Deletes shot on server and clears metadata of selected strips."

    confirm: bpy.props.BoolProperty(name="Confirm")

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return bool(zsession_auth(context) and context.selected_sequences)

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

            # check if strip is already linked to gazou
            if not CheckStrip.linked(strip):
                failed.append(strip)
                continue

            # check if shot still exists on gazou
            zshot = CheckStrip.shot_exists_by_id(strip)
            if not zshot:
                failed.append(strip)
                continue

            # delete shot
            Push.delete_shot(strip, zshot)
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
        if len(selshots) > 1:
            noun = "%i shots" % len(selshots)
        else:
            noun = "this shot"

        col.prop(
            self,
            "confirm",
            text="Delete %s on server." % noun,
        )


class BZ_OT_SQE_PushThumbnail(bpy.types.Operator):
    """
    Operator that takes thumbnail of all selected sequencce strips and saves them
    in tmp directory. Loops through all thumbnails and uploads them to gazou.
    uses Animation task type to create task and set main thumbnail in wip state.
    """

    bl_idname = "blezou.sqe_push_thumbnail"
    bl_label = "Push Thumbnail"
    bl_options = {"INTERNAL"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return bool(zsession_auth(context))

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

                    # only if strip is linked to gazou
                    if not CheckStrip.linked(strip):
                        failed.append(strip)
                        continue

                    # check if shot is still available by id
                    zshot = CheckStrip.shot_exists_by_id(strip)
                    if not zshot:
                        failed.append(strip)
                        continue

                    # if only one strip is selected,
                    if not do_multishot:
                        # if active strip is not contained in the current frame, use middle frame of active strip
                        # otherwise don't change frame and use current one
                        if not CheckStrip.contains(strip, original_curframe):
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

        addon_prefs = addon_prefs_get(bpy.context)
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
            # turns out a entitiy in gazou can have 0 tasks even tough task types exist
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


class BZ_OT_SQE_DebugDuplicates(bpy.types.Operator):
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
            return {"CANCELED"}

        # deselect all if something is selected
        if context.selected_sequences:
            bpy.ops.sequencer.select_all()

        strip = context.scene.sequence_editor.sequences_all[strip_name]
        strip.select = True
        bpy.ops.sequencer.select()
        return {"FINISHED"}

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event) -> Set[str]:
        opsdata._SQE_DUPLCIATES[:] = opsdata._sqe_update_duplicates(context)
        return context.window_manager.invoke_props_popup(self, event)  # type: ignore


class BZ_OT_SQE_DebugNotLinked(bpy.types.Operator):
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
        opsdata._SQE_NOT_LINKED[:] = opsdata._sqe_update_not_linked(context)
        return context.window_manager.invoke_props_popup(self, event)  # type: ignore


class BZ_OT_SQE_DebugMultiProjects(bpy.types.Operator):
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
        opsdata._SQE_MULTI_PROJECT[:] = opsdata._sqe_update_multi_project(context)
        return context.window_manager.invoke_props_popup(self, event)  # type: ignore


# ---------REGISTER ----------

classes = [
    BZ_OT_SessionStart,
    BZ_OT_SessionEnd,
    BZ_OT_ProductionsLoad,
    BZ_OT_SequencesLoad,
    BZ_OT_ShotsLoad,
    BZ_OT_AssetTypesLoad,
    BZ_OT_AssetsLoad,
    BZ_OT_SQE_PushNewShot,
    BZ_OT_SQE_PushShotMeta,
    BZ_OT_SQE_DelShotMeta,
    BZ_OT_SQE_InitShot,
    BZ_OT_SQE_InitShotBulk,
    BZ_OT_SQE_LinkShot,
    BZ_OT_SQE_LinkSequence,
    BZ_OT_SQE_PushThumbnail,
    BZ_OT_SQE_PushDeleteShot,
    BZ_OT_SQE_PullShotMeta,
    BZ_OT_SQE_DebugDuplicates,
    BZ_OT_SQE_DebugNotLinked,
    BZ_OT_SQE_DebugMultiProjects,
]


def register():
    importlib.reload(opsdata)
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
