from dataclasses import asdict
from pathlib import Path
import contextlib
from typing import Set, Dict, Union, List, Tuple, Any
import bpy
from .types import ZProductions, ZProject, ZSequence, ZShot, ZAssetType, ZAsset
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


class BZ_OT_SQE_ScanTrackProps(bpy.types.Operator):
    """
    Composes a dictionary data structure to be pushed to backend and saves it in preferences of blezou addon.
    """

    bl_idname = "blezou.sqe_scan_track_properties"
    bl_label = "SQE Scan Track Properties"
    bl_options = {"INTERNAL"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return True

    def execute(self, context: bpy.types.Context) -> Set[str]:
        prefs = prefs_get(context)

        # clear old prefs
        prefs["sqe_track_props"] = {}
        seq_dict: Dict[str, Dict[str, Any]] = {}

        seq_editor = context.scene.sequence_editor

        for strip in seq_editor.sequences_all:
            strip_seq = strip.blezou.sequence
            strip_shot = strip.blezou.shot

            if strip_seq and strip_shot:
                # create seq if not exists
                if strip_seq not in seq_dict:
                    seq_dict[strip_seq] = {"shots": {}}

                shot_dict = {
                    "sequence_name": strip_seq,
                    "frame_in": strip.frame_final_start,
                    "frame_out": strip.frame_final_end,
                }

                # update seq dict with shot
                seq_dict[strip_seq]["shots"][strip_shot] = shot_dict

                # TODO: order dictionary

        prefs["sqe_track_props"] = seq_dict
        logger.info("Result of scan: \n %s" % seq_dict)

        # ui_redraw()
        return {"FINISHED"}


class BZ_OT_SQE_SyncTrackProps(bpy.types.Operator):
    """
    Pushes data structure which is saved in blezou addon prefs to backend. Performs updates if necessary.
    """

    bl_idname = "blezou.sqe_sync_track_properties"
    bl_label = "SQE Sync Track Properties"
    bl_options = {"INTERNAL"}

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
        active_project = ZProject(**prefs["project_active"].to_dict())
        track_props = prefs["sqe_track_props"]

        if not track_props:
            logger.info("No data to push to: %s" % prefs.host)
            return {"FINISHED"}

        logger.info("Pushing data to: %s" % prefs.host)
        # TODO: add popup confirmation dialog before syncin

        for seq_name in track_props:
            # check if seq already exists
            existing_seq = active_project.get_sequence_by_name(
                seq_name
            )  # returns None if not existent
            if existing_seq:
                zsequence = existing_seq
                logger.info("Sequence already exists: %s. Skip." % seq_name)
            else:
                # push new seq
                zsequence = active_project.create_sequence(seq_name)
                logger.info("Pushed new sequence: %s" % seq_name)

            for shot_name in track_props[seq_name]["shots"]:
                frame_in = track_props[seq_name]["shots"][shot_name]["frame_in"]
                frame_out = track_props[seq_name]["shots"][shot_name]["frame_out"]

                # update shot if already exists
                existing_shot = active_project.get_shot_by_name(
                    zsequence, shot_name
                )  # returns None if not existent
                if existing_shot:
                    existing_shot.data["frame_in"] = frame_in
                    existing_shot.data["frame_out"] = frame_out
                    active_project.update_shot(existing_shot)
                    logger.info("Pushed update to shot: %s" % shot_name)
                else:
                    # push shot
                    active_project.create_shot(
                        shot_name,
                        zsequence,
                        frame_in=frame_in,
                        frame_out=frame_out,
                        data={},
                    )
                    logger.info("Pushed new shot: %s" % shot_name)

        return {"FINISHED"}


class BZ_OT_SQE_MakeStripThumbnail(bpy.types.Operator):
    """
    Pushes data structure which is saved in blezou addon prefs to backend. Performs updates if necessary.
    """

    bl_idname = "blezou.sqe_make_strip_thumbnail"
    bl_label = "SQE Create Strip Thumbnail"
    bl_options = {"INTERNAL"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return bool(context.selected_sequences)

    def execute(self, context: bpy.types.Context) -> Set[str]:

        nr_of_strips = len(context.selected_sequences)
        do_multishot = nr_of_strips > 1
        # The multishot and singleshot branches do pretty much the same thing,
        # but report differently to the user.

        with self.override_render_settings(context):
            with self.temporary_current_frame(context) as original_curframe:
                # if user has multiple strips selected, make thumbnail for each of them, use middle frame
                if do_multishot:
                    self.report(
                        {"INFO"},
                        "Rendering thumbnails for %i selected shots." % nr_of_strips,
                    )
                    for strip in context.selected_sequences:
                        self.set_middle_frame(context, strip)
                        self.make_thumbnail(context, strip)

                else:
                    # if user has one strip selected, make thumbnail
                    strip = context.scene.sequence_editor.active_strip
                    # if active strip is not contained in the current frame, use middle frame of active strip
                    if not self.strip_contains(strip, original_curframe):
                        self.report(
                            {"WARNING"},
                            "Rendering middle frame as thumbnail for active shot.",
                        )
                        self.set_middle_frame(context, strip)
                    else:
                        self.report(
                            {"INFO"},
                            "Rendering current frame as thumbnail for active shot.",
                        )
                    self.make_thumbnail(context, strip)

        return {"FINISHED"}

    def save_render(self, datablock: bpy.types.Image, file_name: str) -> None:
        """Save the current render image to disk"""

        prefs = prefs_get(bpy.context)
        folder_name = prefs.folder_thumbnail

        # Ensure folder exists
        folder_path = Path(folder_name)
        folder_path.mkdir(parents=True, exist_ok=True)

        path = folder_path.joinpath(file_name)
        datablock.save_render(str(path))

    def make_thumbnail(
        self, context: bpy.types.Context, strip: bpy.types.Sequence
    ) -> None:
        bpy.ops.render.render()
        file_name = f"{str(context.scene.frame_current)}.jpg"  # TODO filename should be ID of shot
        self.save_render(bpy.data.images["Render Result"], file_name)

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

    @staticmethod
    def strip_contains(strip: bpy.types.Sequence, framenr: int) -> bool:
        """Returns True if the strip covers the given frame number"""
        return int(strip.frame_final_start) <= framenr <= int(strip.frame_final_end)


# ---------REGISTER ----------

classes = [
    BZ_OT_SessionStart,
    BZ_OT_SessionEnd,
    BZ_OT_ProductionsLoad,
    BZ_OT_SequencesLoad,
    BZ_OT_ShotsLoad,
    BZ_OT_AssetTypesLoad,
    BZ_OT_AssetsLoad,
    BZ_OT_SQE_ScanTrackProps,
    BZ_OT_SQE_SyncTrackProps,
    BZ_OT_SQE_MakeStripThumbnail,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)