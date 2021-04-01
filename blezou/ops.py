from dataclasses import asdict
from pathlib import Path
import copy
import contextlib
from typing import Set, Dict, Union, List, Tuple, Any, Optional, cast
import bpy
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
)
from .util import zsession_auth, prefs_get, zsession_get
from .core import ui_redraw
from .logger import ZLoggerFactory
from .gazu import gazu

logger = ZLoggerFactory.getLogger(__name__)


class BZ_OT_SessionStart(bpy.types.Operator):
    """
    Starts the ZSession, which  is stored in Blezou addon preferences.
    Authenticates user with backend until session ends.
    Host, email and password are retrieved from Blezou addon preferences.
    """

    bl_idname = "blezou.session_start"
    bl_label = "Start Gazou Session"
    bl_options = {"INTERNAL"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return True
        # TODO: zsession.valid_config() seems to have update issues
        zsession = zsession_get(context)
        return zsession.valid_config()

    def execute(self, context: bpy.types.Context) -> Set[str]:
        zsession = zsession_get(context)

        zsession.set_config(self.get_config(context))
        zsession.start()
        return {"FINISHED"}

    def get_config(self, context: bpy.types.Context) -> Dict[str, str]:
        prefs = prefs_get(context)
        return {
            "email": prefs.email,
            "host": prefs.host,
            "passwd": prefs.passwd,
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
        return {"FINISHED"}


class BZ_OT_ProductionsLoad(bpy.types.Operator):
    """
    Gets all productions that are available in backend and let's user select. Invokes a search Popup (enum_prop) on click.
    """

    bl_idname = "blezou.productions_load"
    bl_label = "Productions Load"
    bl_options = {"INTERNAL"}
    bl_property = "enum_prop"

    def _get_productions(
        self, context: bpy.types.Context
    ) -> List[Tuple[str, str, str]]:
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
        prefs = prefs_get(context)

        # store vars to check if project / seq / shot changed
        prev_project_active = prefs["project_active"].to_dict()

        # update prefs
        prefs["project_active"] = asdict(ZProject.by_id(self.enum_prop))

        # clear active shot when sequence changes
        if prev_project_active:
            if prefs["project_active"].to_dict()["id"] != prev_project_active["id"]:
                prefs["sequence_active"] = {}
                prefs["shot_active"] = {}

        ui_redraw()
        return {"FINISHED"}

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event) -> Set[str]:
        context.window_manager.invoke_search_popup(self)
        return {"FINISHED"}


class BZ_OT_SequencesLoad(bpy.types.Operator):
    """
    Gets all sequences that are available in backend for active production and let's user select. Invokes a search Popup (enum_prop) on click.
    """

    bl_idname = "blezou.sequences_load"
    bl_label = "Sequences Load"
    bl_options = {"INTERNAL"}
    bl_property = "enum_prop"

    # TODO: reduce api request to one, we request in _get_sequences and also in execute to set sequence_active

    def _get_sequences(self, context: bpy.types.Context) -> List[Tuple[str, str, str]]:
        prefs = prefs_get(context)
        active_project = ZProject(**prefs["project_active"].to_dict())

        enum_list = [
            (s.id, s.name, s.description if s.description else "")
            for s in active_project.get_sequences_all()
        ]
        return enum_list

    enum_prop: bpy.props.EnumProperty(items=_get_sequences)  # type: ignore

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        prefs = prefs_get(context)
        active_project = prefs["project_active"]

        if zsession_auth(context):
            if active_project:
                return True
        return False

    def execute(self, context: bpy.types.Context) -> Set[str]:
        prefs = prefs_get(context)

        # store vars to check if project / seq / shot changed
        prev_sequence_active = prefs["sequence_active"].to_dict()

        # update preferences
        prefs["sequence_active"] = asdict(ZSequence.by_id(self.enum_prop))

        # clear active shot when sequence changes
        if prev_sequence_active:
            if prefs["sequence_active"].to_dict()["id"] != prev_sequence_active["id"]:
                prefs["shot_active"] = {}

        ui_redraw()
        return {"FINISHED"}

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event) -> Set[str]:
        context.window_manager.invoke_search_popup(self)
        return {"FINISHED"}


class BZ_OT_ShotsLoad(bpy.types.Operator):
    """
    Gets all sequences that are available in backend for active production and let's user select. Invokes a search Popup (enum_prop) on click.
    """

    bl_idname = "blezou.shots_load"
    bl_label = "Shots Load"
    bl_options = {"INTERNAL"}
    bl_property = "enum_prop"

    # TODO: reduce api request to one, we request in _get_shots and also in execute to set active shot

    def _get_shots(self, context: bpy.types.Context) -> List[Tuple[str, str, str]]:
        prefs = prefs_get(context)
        active_sequence = ZSequence(
            **prefs["sequence_active"].to_dict()
        )  # is of type IDProperty

        enum_list = [
            (s.id, s.name, s.description if s.description else "")
            for s in active_sequence.get_all_shots()
        ]
        return enum_list

    enum_prop: bpy.props.EnumProperty(items=_get_shots)  # type: ignore

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        # only if session is auth active_project and active sequence selected
        prefs = prefs_get(context)
        active_project = prefs["project_active"]
        active_sequence = prefs["sequence_active"]

        if zsession_auth(context) and active_project and active_sequence:
            return True
        return False

    def execute(self, context: bpy.types.Context) -> Set[str]:
        # update preferences
        prefs = prefs_get(context)
        prefs["shot_active"] = asdict(ZShot.by_id(self.enum_prop))
        ui_redraw()
        return {"FINISHED"}

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event) -> Set[str]:
        context.window_manager.invoke_search_popup(self)
        return {"FINISHED"}


class BZ_OT_AssetTypesLoad(bpy.types.Operator):
    """
    Gets all sequences that are available in backend for active production and let's user select. Invokes a search Popup (enum_prop) on click.
    """

    bl_idname = "blezou.asset_types_load"
    bl_label = "Assettyes Load"
    bl_options = {"INTERNAL"}
    bl_property = "enum_prop"

    # TODO: reduce api request to one, we request in _get_sequences and also in execute to set sequence_active

    def _get_assetypes(self, context: bpy.types.Context) -> List[Tuple[str, str, str]]:
        prefs = prefs_get(context)
        active_project = ZProject(**prefs["project_active"].to_dict())

        enum_list = [
            (at.id, at.name, "") for at in active_project.get_all_asset_types()
        ]
        return enum_list

    enum_prop: bpy.props.EnumProperty(items=_get_assetypes)  # type: ignore

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        prefs = prefs_get(context)
        active_project = prefs["project_active"]

        if zsession_auth(context) and active_project:
            return True
        return False

    def execute(self, context: bpy.types.Context) -> Set[str]:
        prefs = prefs_get(context)

        # store vars to check if project / seq / shot changed
        prev_a_type_active = prefs["asset_type_active"].to_dict()

        # update preferences
        prefs["asset_type_active"] = asdict(ZAssetType.by_id(self.enum_prop))

        # clear active shot when sequence changes
        if prev_a_type_active:
            if prefs["asset_type_active"].to_dict()["id"] != prev_a_type_active["id"]:
                prefs["asset_active"] = {}

        ui_redraw()
        return {"FINISHED"}

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event) -> Set[str]:
        context.window_manager.invoke_search_popup(self)
        return {"FINISHED"}


class BZ_OT_AssetsLoad(bpy.types.Operator):
    """
    Gets all sequences that are available in backend for active production and let's user select. Invokes a search Popup (enum_prop) on click.
    """

    bl_idname = "blezou.assets_load"
    bl_label = "Assets Load"
    bl_options = {"INTERNAL"}
    bl_property = "enum_prop"

    # TODO: reduce api request to one, we request in _get_sequences and also in execute to set sequence_active

    def _get_assets(self, context: bpy.types.Context) -> List[Tuple[str, str, str]]:
        prefs = prefs_get(context)
        active_project = ZProject(**prefs["project_active"].to_dict())
        active_asset_type = ZAssetType(**prefs["asset_type_active"].to_dict())

        enum_list = [
            (a.id, a.name, a.description if a.description else "")
            for a in active_project.get_all_assets_for_type(active_asset_type)
        ]
        return enum_list

    enum_prop: bpy.props.EnumProperty(items=_get_assets)  # type: ignore

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        prefs = prefs_get(context)
        active_project = prefs["project_active"]
        active_asset_type = prefs["asset_type_active"]

        if zsession_auth(context) and active_project and active_asset_type:
            return True
        return False

    def execute(self, context: bpy.types.Context) -> Set[str]:
        # update preferences
        prefs = prefs_get(context)
        prefs["asset_active"] = asdict(ZAsset.by_id(self.enum_prop))
        ui_redraw()
        return {"FINISHED"}

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event) -> Set[str]:
        context.window_manager.invoke_search_popup(self)
        return {"FINISHED"}


class Pull:
    """Class that contains staticmethods to pull data from gazou data base into Blender"""

    @staticmethod
    def shot_meta(strip: bpy.types.Sequence, zshot: ZShot) -> None:
        seq_name = zshot.sequence_name
        if seq_name:  # TODO: is sometimtes None
            strip.blezou.sequence = seq_name
        strip.blezou.shot = zshot.name
        strip.blezou.description = zshot.description if zshot.description else ""
        strip.blezou.id = zshot.id
        strip.blezou.initialized = True
        strip.blezou.linked = True
        # strip.frame_final_start = zshot.data["frame_in"]
        # strip.frame_final_end = zshot.data["frame_out"]
        logger.info("Pulled meta from shot: %s to strip: %s" % (zshot.name, strip.name))


class Push:
    """Class that contains staticmethods to push data from blender to gazou data base"""

    @staticmethod
    def shot_meta(strip: bpy.types.Sequence, zshot: ZShot) -> None:
        zshot.name = strip.blezou.shot
        zshot.description = strip.blezou.description
        zshot.data["frame_in"] = strip.frame_final_start
        zshot.data["frame_out"] = strip.frame_final_end
        # update in gazou
        zshot.update()
        logger.info("Pushed meta to shot: %s from strip: %s" % (zshot.name, strip.name))

    @staticmethod
    def new_shot(
        strip: bpy.types.Sequence,
        zsequence: ZSequence,
        zproject: ZProject,
    ) -> ZShot:
        zshot = zproject.create_shot(
            strip.blezou.shot,
            zsequence,
            frame_in=strip.frame_final_start,
            frame_out=strip.frame_final_end,
        )
        if strip.blezou.description:
            zshot.description = strip.blezou.description
            zshot.update()
        logger.info(
            "Pushed create shot: %s for project: %s" % (zshot.name, zproject.name)
        )
        return zshot

    @staticmethod
    def new_sequence(strip: bpy.types.Sequence, zproject: ZProject) -> ZSequence:
        zsequence = zproject.create_sequence(
            strip.blezou.sequence,
        )
        logger.info(
            "Pushed create sequence: %s for project: %s"
            % (zsequence.name, zproject.name)
        )
        return zsequence


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
                "Strip: %s. Is linked to ID: %s." % (strip.name, strip.blezou.id)
            )
            return True

    @staticmethod
    def has_meta(strip: bpy.types.Sequence) -> bool:
        """Returns True if strip.blezou.shot and strip.blezou.sequence is Truethy else False"""
        seq = strip.blezou.sequence
        shot = strip.blezou.shot
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
        """Returns ZShot instance if shot with strip.blezou.id exists else None"""
        try:
            zshot = ZShot.by_id(strip.blezou.id)
        except gazu.exception.RouteNotFoundException:
            logger.error(
                "Strip: %s. Shot ID: %s not found in gazou anymore. Was maybe deleted?"
                % (strip.name, strip.blezou.id)
            )
            return None
        if zshot:
            logger.info(
                "Strip: %s. Shot %s exists in gazou, ID: %s)."
                % (strip.name, zshot.name, zshot.id)
            )
            return zshot
        else:
            logger.info(
                "Strip: %s. Shot %s does not exist in gazou. ID: %s not found."
                % (strip.name, zshot.name, strip.blezou.id)
            )
            return None

    @staticmethod
    def seq_exists_by_name(
        strip: bpy.types.Sequence, zproject: ZProject
    ) -> Optional[ZSequence]:
        """Returns ZSequence instance if strip.blezou.sequence exists in gazou, else None"""
        zseq = zproject.get_sequence_by_name(strip.blezou.sequence)
        if zseq:
            logger.info(
                "Strip: %s. Sequence %s exists in gazou, ID: %s)."
                % (strip.name, zseq.name, zseq.id)
            )
            return zseq
        else:
            logger.info(
                "Strip: %s. Sequence %s does not exist in gazou."
                % (strip.name, strip.blezou.sequence)
            )
            return None

    @staticmethod
    def shot_exists_by_name(
        strip: bpy.types.Sequence, zproject: ZProject, zsequence: ZSequence
    ) -> Optional[ZShot]:
        """Returns ZShot instance if strip.blezou.shot exists in gazou, else None."""
        zshot = zproject.get_shot_by_name(zsequence, strip.blezou.shot)
        if zshot:
            logger.info(
                "Strip: %s. Shot already existent in gazou, ID: %s)."
                % (strip.name, zshot.id)
            )
            return zshot
        else:
            logger.info(
                "Strip: %s. Shot %s does not exist in gazou."
                % (strip.name, strip.blezou.shot)
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
    bl_label = "Push Shot meta"
    bl_options = {"INTERNAL"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return bool(zsession_auth(context) and context.selected_sequences)

    def execute(self, context: bpy.types.Context) -> Set[str]:
        succeeded = []
        failed = []
        logger.info("-START- Blezou Pushing Metadata")
        # begin progress update
        selected_sequences = context.selected_sequences
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
    bl_label = "Push New Shot"
    bl_options = {"INTERNAL"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        # needs to be logged in, active project
        prefs = prefs_get(context)
        active_project = prefs["project_active"]
        return bool(
            zsession_auth(context)
            and active_project.to_dict()
            and context.selected_sequences
        )

    def execute(self, context: bpy.types.Context) -> Set[str]:
        prefs = prefs_get(context)
        zproject = ZProject(**prefs["project_active"].to_dict())
        succeeded = []
        failed = []
        logger.info("-START- Blezou pushing new Shots to: %s" % zproject.name)

        # begin progress update
        selected_sequences = context.selected_sequences
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
            zseq = CheckStrip.seq_exists_by_name(strip, zproject)
            # TODO: does not log?
            if not zseq:
                zseq = Push.new_sequence(strip, zproject)

            # check if shot already on gazou > create it
            zshot = CheckStrip.shot_exists_by_name(strip, zproject, zseq)
            # TODO: does not log?
            if zshot:
                failed.append(strip)
                continue

            # push update to shot
            zshot = Push.new_shot(strip, zseq, zproject)
            Pull.shot_meta(strip, zshot)
            succeeded.append(strip)

        # end progress update
        context.window_manager.progress_update(len(selected_sequences))
        context.window_manager.progress_end()

        self.report(
            {"INFO"},
            f"Created {len(succeeded)} new Shots | Failed: {len(failed)}",
        )
        logger.info("-END- Blezou pushing new Shots to: %s" % zproject.name)
        return {"FINISHED"}


class BZ_OT_SQE_InitShot(bpy.types.Operator):
    """
    Operator that initializes a regular sequence strip to a 'blezou' shot.
    Only sets strip.blezou.initialized = True. But this is required for further
    operations and to  differentiate between regular sequence strip and blezou shot strip.
    """

    bl_idname = "blezou.sqe_new_shot"
    bl_label = "New Shot"
    bl_description = "Adds required shot metadata to selecetd strips"

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return bool(context.selected_sequences)

    def execute(self, context: bpy.types.Context) -> Set[str]:
        succeeded = []
        failed = []
        logger.info("-START- Initializing Shots")

        for strip in context.selected_sequences:
            if strip.blezou.initialized:
                logger.info("%s already initialized." % strip.name)
                failed.append(strip)
                continue

            strip.blezou.initialized = True
            succeeded.append(strip)
            logger.info("Initialized strip: %s as Shot." % strip.name)

        self.report(
            {"INFO"},
            f"Initialized {len(succeeded)} Shots | Failed: {len(failed)}.",
        )
        logger.info("-END- Initializing Shots")
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
        "Adds required shot metadata to selecetd strip based on data from gazou."
    )
    bl_property = "enum_prop"

    def _get_shots(self, context: bpy.types.Context) -> List[Tuple[str, str, str]]:
        prefs = prefs_get(context)
        zproject = ZProject(**prefs["project_active"].to_dict())

        enum_list = []
        all_sequences = zproject.get_sequences_all()
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
        prefs = prefs_get(context)
        active_project = prefs["project_active"]
        return bool(
            zsession_auth(context) and active_project and context.selected_sequences
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
        context.window_manager.invoke_props_dialog(self, width=400)
        return {"FINISHED"}


class BZ_OT_SQE_PullShotMeta(bpy.types.Operator):
    """
    Operator that pulls metadata of all selected sequencce strips from gazou
    after performing various checks. Metadata will be saved in strip.blezou.
    """

    bl_idname = "blezou.sqe_pull_shot_meta"
    bl_label = "Pull Shot Meta"
    bl_options = {"INTERNAL"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return bool(zsession_auth(context) and context.selected_sequences)

    def execute(self, context: bpy.types.Context) -> Set[str]:
        succeeded = []
        failed = []
        logger.info("-START- Pulling Shot Metadata")

        # begin progress update
        selected_sequences = context.selected_sequences
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
            f"Pulled Metadata for {len(succeeded)} Shots | Failed: {len(failed)}.",
        )
        logger.info("-END- Pulling Shot Metadata")
        ui_redraw()
        return {"FINISHED"}


class BZ_OT_SQE_DelShot(bpy.types.Operator):
    """
    Operator that deletes all  metadata of all selected sequencce strips
    after performing various checks. It does NOT change anything in gazou.
    """

    bl_idname = "blezou.sqe_del_shot"
    bl_label = "Del Shot"
    bl_description = "Removes shot metadata from selecetd strips. Only affects SQE."

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return bool(context.selected_sequences)

    def execute(self, context: bpy.types.Context) -> Set[str]:
        failed: List[bpy.types.Sequence] = []
        succeeded: List[bpy.types.Sequence] = []
        logger.info("-START- Deleting Shot Metadata")

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
            f"Removed metadata of {len(succeeded)} Shots | Failed: {len(failed)}.",
        )
        logger.info("-END- Deleting Shot Metadata")
        return {"FINISHED"}


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
        return bool(zsession_auth(context) and context.selected_sequences)

    def execute(self, context: bpy.types.Context) -> Set[str]:
        nr_of_strips: int = len(context.selected_sequences)
        do_multishot: bool = nr_of_strips > 1
        failed = []
        upload_queue: List[Path] = []  # will be used as successed list
        logger.info("-START- Pushing Shot Thumbnails")
        with self.override_render_settings(context):
            with self.temporary_current_frame(context) as original_curframe:

                # ----RENDER AND SAVE THUMBNAILS ------

                # begin first progress update
                selected_sequences = context.selected_sequences
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
            f"Created thumbnails for {len(upload_queue)} Shots | Failed: {len(failed)}",
        )
        logger.info("-END- Pushing Shot Thumbnails")
        return {"FINISHED"}

    def make_thumbnail(
        self, context: bpy.types.Context, strip: bpy.types.Sequence
    ) -> Path:
        bpy.ops.render.render()
        file_name = f"{strip.blezou.id}_{str(context.scene.frame_current)}.jpg"
        path = self._save_render(bpy.data.images["Render Result"], file_name)
        logger.info(f"Saved thumbnail of shot {strip.blezou.shot} to {path.as_posix()}")
        return path

    def _save_render(self, datablock: bpy.types.Image, file_name: str) -> Path:
        """Save the current render image to disk"""

        prefs = prefs_get(bpy.context)
        folder_name = prefs.folder_thumbnail

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
                "Failed to upload thumbnails. Task Status: 'wip' is missing."
            )
        if not ztask_type:
            raise RuntimeError(
                "Failed to upload thumbnails. Task Type: 'Animation' is missing."
            )

        # find / get latest task
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

    def _get_duplicates(self, context: bpy.types.Context) -> List[Tuple[str, str, str]]:
        """get all strips that are initialized but not linked yet"""
        enum_list = []
        data_dict = {}
        strips = [
            context.scene.sequence_editor.sequences_all[item.identifier]
            for item in context.scene.bl_rna.properties["strip_cache"].enum_items
        ]

        # create data dict that holds all shots ids and the corresponding strips that are linked to it
        for i in range(len(strips)):

            if strips[i].blezou.linked:
                # get shot_id, shot_name, create entry in data_dict if id not existent
                shot_id = strips[i].blezou.id
                shot_name = strips[i].blezou.shot
                if shot_id not in data_dict:
                    data_dict[shot_id] = {"name": shot_name, "strips": []}

                # append i to strips list
                if strips[i] not in set(data_dict[shot_id]["strips"]):
                    data_dict[shot_id]["strips"].append(strips[i])

                # comparet to all other strip
                for j in range(i + 1, len(strips)):
                    if shot_id == strips[j].blezou.id:
                        data_dict[shot_id]["strips"].append(strips[j])

        # convert in data strucutre for enum property
        for shot_id, data in data_dict.items():
            if len(data["strips"]) > 1:
                enum_list.append(("", data["name"], shot_id))
                for strip in data["strips"]:
                    enum_list.append((strip.name, strip.name, ""))

        return enum_list

    duplicates: bpy.props.EnumProperty(items=_get_duplicates, name="Duplicates")

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return bool(context.selected_sequences)

    def execute(self, context: bpy.types.Context) -> Set[str]:
        strip_name = self.duplicates
        if strip_name:
            # deselect all if something is selected
            if context.selected_sequences:
                bpy.ops.sequencer.select_all()
            strip = context.scene.sequence_editor.sequences_all[strip_name]
            strip.select = True
        return {"FINISHED"}

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event) -> Set[str]:
        if context.selected_sequences:
            items = [(s.name, s.name, s.name) for s in context.selected_sequences]
            bpy.types.Scene.strip_cache = bpy.props.EnumProperty(
                items=items, name="blezou_strips_cache"
            )
        else:
            items = [
                (s.name, s.name, s.name)
                for s in context.scene.sequence_editor.sequences_all
            ]
            bpy.types.Scene.strip_cache = bpy.props.EnumProperty(
                items=items, name="blezou_strips_cache"
            )
        context.window_manager.invoke_props_popup(self, event)
        return {"FINISHED"}


class BZ_OT_SQE_DebugNotLinked(bpy.types.Operator):
    """"""

    bl_idname = "blezou.sqe_debug_not_linked"
    bl_label = "Debug Not Linked"
    bl_options = {"REGISTER", "UNDO"}
    bl_property = "not_linked"

    def _get_not_linked(self, context: bpy.types.Context) -> List[Tuple[str, str, str]]:
        """get all strips that are initialized but not linked yet"""
        enum_list = []
        strips = [
            context.scene.sequence_editor.sequences_all[item.identifier]
            for item in context.scene.bl_rna.properties["strip_cache"].enum_items
        ]
        for strip in strips:
            if strip.blezou.initialized and not strip.blezou.linked:
                enum_list.append((strip.name, strip.name, ""))
        return enum_list

    not_linked: bpy.props.EnumProperty(items=_get_not_linked, name="Not Linked")

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return bool(context.selected_sequences)

    def execute(self, context: bpy.types.Context) -> Set[str]:
        strip_name = self.not_linked
        if strip_name:
            # deselect all if something is selected
            if context.selected_sequences:
                bpy.ops.sequencer.select_all()
            strip = context.scene.sequence_editor.sequences_all[strip_name]
            strip.select = True
        return {"FINISHED"}

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event) -> Set[str]:
        # register a enumproperty on types.scene that holds items which represent names of sequence strips
        # if selection exists use it
        if context.selected_sequences:
            items = [(s.name, s.name, "") for s in context.selected_sequences]

        # if not use all strips in sequence editor
        else:
            items = [
                (s.name, s.name, "")
                for s in context.scene.sequence_editor.sequences_all
            ]
        bpy.types.Scene.strip_cache = bpy.props.EnumProperty(
            items=items, name="blezou_strips_cache"
        )
        context.window_manager.invoke_props_popup(self, event)
        return {"FINISHED"}


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
    BZ_OT_SQE_DelShot,
    BZ_OT_SQE_InitShot,
    BZ_OT_SQE_LinkShot,
    BZ_OT_SQE_PushThumbnail,
    BZ_OT_SQE_PullShotMeta,
    BZ_OT_SQE_DebugDuplicates,
    BZ_OT_SQE_DebugNotLinked,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)