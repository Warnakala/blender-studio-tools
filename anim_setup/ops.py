import re
from pathlib import Path
from typing import Dict, List, Set, Optional

import bpy

from .log import LoggerFactory
from .kitsu import KitsuConnector, Shot, Project, Sequence
from . import opsdata, prefs, asglobals

logger = LoggerFactory.getLogger()


def ui_redraw() -> None:
    """
    Forces blender to redraw the UI.
    """
    for screen in bpy.data.screens:
        for area in screen.areas:
            area.tag_redraw()


class AS_OT_create_actions(bpy.types.Operator):
    """
    Creates default action for active collection
    """

    bl_idname = "as.create_action"
    bl_label = "Create action"

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        act_coll = context.view_layer.active_layer_collection.collection
        return bool(bpy.data.filepath and act_coll)

    def execute(self, context: bpy.types.Context) -> Set[str]:
        assigned: List[bpy.types.Action] = []
        created: List[bpy.types.Action] = []
        failed: List[bpy.types.Collection] = []
        collections = opsdata.get_valid_collections(context)

        if not collections:
            self.report({"WARNING"}, "No valid collections available")
            return {"CANCELLED"}

        for coll in collections:
            rig = opsdata.find_rig(coll)

            if not rig:
                logger.warning(f"{coll.name} contains no rig.")
                failed.append(coll)
                continue

            # create new action
            action_name = self._gen_action_name(rig)
            if action_name not in list(bpy.data.actions):
                action = bpy.data.actions.new(action_name)
                logger.info("Created action: %s", action.name)
                created.append(action)
            else:
                action = bpy.data.actions[action_name]
                logger.info("Action %s already exists. Will take that.", action.name)

            # assign action
            rig.animation_data.action = action
            logger.info("%s assigned action %s", rig.name, action.name)

            # add fake user
            action.use_fake_user = True
            assigned.append(action)

        self.report(
            {"INFO"},
            "Actions: Created %s | Assigned %s | Failed %s"
            % (len(created), len(assigned), len(failed)),
        )
        return {"FINISHED"}

    def _gen_action_name(self, armature: bpy.types.Armature):
        action_prefix = "ANI"
        asset_name = opsdata.find_asset_name(armature.name).lower()
        version = "v001"
        shot_name = opsdata.get_shot_name_from_file()

        action_name = f"{action_prefix}-{asset_name}.{shot_name}.{version}"

        if self._is_multi_asset(asset_name):
            action_name = f"{action_prefix}-{asset_name}_A.{shot_name}.{version}"

        return action_name

    def _is_multi_asset(self, asset_name: str) -> bool:
        multi_assets = ["sprite", "snail"]
        if asset_name.lower() in multi_assets:
            return True
        return False


class AS_OT_setup_workspaces(bpy.types.Operator):
    """
    Sets up the workspaces for the animation task
    """

    bl_idname = "as.setup_workspaces"
    bl_label = "Setup Workspace"

    def execute(self, context: bpy.types.Context) -> Set[str]:

        # remove non anim workspaces
        for ws in bpy.data.workspaces:
            if ws.name != "Animation":
                bpy.ops.workspace.delete({"workspace": ws})

            self.report({"INFO"}, "Deleted non Animation workspaces")

        return {"FINISHED"}


class AS_OT_load_latest_edit(bpy.types.Operator):
    """
    Loads latest edit from dropbox folder
    """

    bl_idname = "as.load_latest_edit"
    bl_label = "Load edit"

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        addon_prefs = prefs.addon_prefs_get(context)
        editorial_path = Path(addon_prefs.editorial_path)

        # needs to be run in sequence editor area
        area_override = None
        for area in bpy.context.screen.areas:
            if area.type == "SEQUENCE_EDITOR":
                area_override = area

        return bool(area_override and editorial_path)

    def execute(self, context: bpy.types.Context) -> Set[str]:

        addon_prefs = prefs.addon_prefs_get(context)
        editorial_path = Path(addon_prefs.editorial_path)
        strip_channel = 1
        latest_file = self._get_latest_edit(context)
        if not latest_file:
            self.report(
                {"ERROR"}, f"Found no edit file in: {editorial_path.as_posix()}"
            )
        strip_filepath = latest_file.as_posix()
        strip_frame_start = 101

        # needs to be run in sequence editor area
        area_override = None
        for area in bpy.context.screen.areas:
            if area.type == "SEQUENCE_EDITOR":
                area_override = area

        if not area_override:
            self.report({"ERROR"}, "No sequence editor are found")
            return {"CANCELLED"}

        override = bpy.context.copy()
        override["area"] = area_override

        bpy.ops.sequencer.movie_strip_add(
            override,
            filepath=strip_filepath,
            relative_path=False,
            frame_start=strip_frame_start,
            channel=strip_channel,
            fit_method="FIT",
        )

        # get sequence name
        seqname = opsdata.get_sequence_from_file()
        if not seqname:
            self.report({"ERROR"}, "Failed to retrieve seqname from current file.")
            return {"CANCELLED"}

        # get shotname
        shotname = opsdata.get_shot_name_from_file()
        if not shotname:
            self.report({"ERROR"}, "Failed to retrieve shotname from current file.")
            return {"CANCELLED"}

        # setup connector and get data from kitsu
        connector = KitsuConnector(addon_prefs)
        project = Project.by_id(connector, addon_prefs.kitsu.project_id)
        sequence = project.get_sequence_by_name(connector, seqname)

        if not sequence:
            self.report({"ERROR"}, f"Failed to find {seqname} on kitsu.")
            return {"CANCELLED"}

        shot = project.get_shot_by_name(connector, sequence, shotname)

        if not shot:
            self.report({"ERROR"}, f"Failed to find shot {shotname} on kitsu.")
            return {"CANCELLED"}

        # update shift frame range prop
        frame_in = shot.data["frame_in"]
        frame_out = shot.data["frame_out"]

        if not frame_in:
            self.report(
                {"ERROR"}, f"On kitsu 'frame_in' is not defined for shot {shotname}."
            )
            return {"CANCELLED"}

        # set sequence strip start kitsu data
        for strip in context.scene.sequence_editor.sequences_all:
            strip.frame_start = -frame_in + (strip_frame_start * 2)

        self.report({"INFO"}, f"Loaded latest edit: {latest_file.name}")

        return {"FINISHED"}

    def _get_latest_edit(self, context: bpy.types.Context):
        addon_prefs = prefs.addon_prefs_get(context)

        editorial_path = Path(addon_prefs.editorial_path)

        files_list = [
            f
            for f in editorial_path.iterdir()
            if f.is_file() and self._is_valid_edit_name(f.name)
        ]
        files_list = sorted(files_list, reverse=True)

        return files_list[0]

    def _is_valid_edit_name(self, filename: str) -> bool:
        pattern = r"sf-edit-v\d\d\d.mp4"

        match = re.search(pattern, filename)
        if match:
            return True
        return False


class AS_OT_import_camera(bpy.types.Operator):
    """
    Imports camera rig and makes library override
    """

    bl_idname = "as.import_camera"
    bl_label = "Import Camera"

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        addon_prefs = prefs.addon_prefs_get(context)
        return bool(addon_prefs.is_project_root_valid and bpy.data.filepath)

    def execute(self, context: bpy.types.Context) -> Set[str]:

        addon_prefs = prefs.addon_prefs_get(context)

        # import camera rig and make override
        camera_rig_path = addon_prefs.camera_rig_path
        if not camera_rig_path:
            self.report({"ERROR"}, "Failed to import camera rig")
            return {"CANCELLED"}

        cam_lib_coll = opsdata.import_data_from_lib(
            "collections",
            "CA-camera_rig",
            camera_rig_path,
        )
        opsdata.instance_coll_to_scene_and_override(context, cam_lib_coll)
        cam_coll = bpy.data.collections[cam_lib_coll.name, None]

        self.report({"INFO"}, f"Imported camera: {cam_coll.name}")
        return {"FINISHED"}


class AS_OT_import_camera_action(bpy.types.Operator):
    """
    Imports cam action of previs file that matches current shot and assignes it
    """

    bl_idname = "as.import_camera_action"
    bl_label = "Import Camera Action"

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        addon_prefs = prefs.addon_prefs_get(context)
        return bool(addon_prefs.is_project_root_valid and bpy.data.filepath)

    def execute(self, context: bpy.types.Context) -> Set[str]:

        try:
            cam_coll = bpy.data.collections["CA-camera_rig", None]
        except KeyError:
            self.report({"ERROR"}, f"Camera collection CA-camera_rig is not imported")
            return {"CANCELELD"}

        # import camera action from previz file

        # get shotname and previs filepath
        shotname = opsdata.get_shot_name_from_file()
        if not shotname:
            self.report({"ERROR"}, "Failed to retrieve shotname from current file.")
            return {"CANCELLED"}

        previs_path = opsdata.get_previs_file(context)
        if not previs_path:
            self.report({"ERROR"}, "Failed to find previz file")
            return {"CANCELLED"}

        # check if cam action name exists in previs library
        cam_action_name = opsdata.get_cam_action_name_from_lib(shotname, previs_path)
        if not cam_action_name:
            self.report(
                {"ERROR"},
                f"Camera action: {cam_action_name} not found in lib: {previs_path.name}",
            )
            return {"CANCELLED"}

        # import cam action data block
        cam_action = opsdata.import_data_from_lib(
            "actions", cam_action_name, previs_path, link=False
        )

        # find rig to assing action to
        rig = opsdata.find_rig(cam_coll)
        if not rig:
            self.report({"WARNING"}, f"{cam_coll.name} contains no rig.")
            return {"CANCELLED"}

        # assign action
        rig.animation_data.action = cam_action
        logger.info("%s assigned action %s", rig.name, cam_action.name)

        # add fake user
        cam_action.use_fake_user = True

        # ensure version suffix to action data bloc
        opsdata.ensure_name_version_suffix(cam_action)

        self.report({"INFO"}, f"{rig.name} imported camera action: {cam_action.name}")
        return {"FINISHED"}


class AS_OT_shift_cam_anim(bpy.types.Operator):
    """
    Shifts the animation as well as anim modifier values of the camera by number of frames
    """

    bl_idname = "as.shift_cam_anim"
    bl_label = "Shift Camera Anim"

    def execute(self, context: bpy.types.Context) -> Set[str]:
        nr_of_frames = context.scene.anim_setup.shift_frames

        # get cam coll
        try:
            rig = bpy.data.objects["RIG-camera", None]
        except KeyError:
            self.report({"ERROR"}, f"Failed to find camera object 'RIG-camera'")
            return {"CANCELELD"}

        for fcurve in rig.animation_data.action.fcurves:

            # shift all keyframes
            for point in fcurve.keyframe_points:
                # print(f"{fcurve.data_path}|{fcurve.array_index}: {point.co.x}|{point.co.y}")
                point.co.x += nr_of_frames
                # don't forget the keyframe's handles:
                point.handle_left.x += nr_of_frames
                point.handle_right.x += nr_of_frames

            logger.info(
                "%s: %s shifted all keyframes by %i frames",
                fcurve.id_data.name,
                fcurve.data_path,
                nr_of_frames,
            )

            # shift all noise modififers values
            for m in fcurve.modifiers:
                if not m.type == "NOISE":
                    continue

                m.offset += nr_of_frames

                if m.use_restricted_range:
                    frame_start = m.frame_start
                    frame_end = m.frame_end
                    m.frame_start = frame_start + (nr_of_frames)
                    m.frame_end = frame_end + (nr_of_frames)

                logger.info(
                    "%s shifted %s modifier values by %i frames",
                    m.id_data.name,
                    m.type.lower(),
                    nr_of_frames,
                )

        self.report({"INFO"}, f"{rig.name} shifted animation by {nr_of_frames}")
        return {"FINISHED"}


class AS_OT_get_frame_shift(bpy.types.Operator):
    """
    Gets the amount of frames that camera has to be shifted, by requesting the frame range
    of the current shot in kitsu
    """

    bl_idname = "as.get_frame_shift"
    bl_label = "Get Frame Shift"

    def execute(self, context: bpy.types.Context) -> Set[str]:
        addon_prefs = prefs.addon_prefs_get(context)
        nr_of_frames = context.scene.anim_setup.shift_frames

        self.report({"WARNING"}, "Not implemente yet")
        return {"FINISHED"}


# ---------REGISTER ----------

classes = [
    AS_OT_create_actions,
    AS_OT_setup_workspaces,
    AS_OT_load_latest_edit,
    AS_OT_import_camera,
    AS_OT_import_camera_action,
    AS_OT_shift_cam_anim,
    AS_OT_get_frame_shift,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
