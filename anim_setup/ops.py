import re
from pathlib import Path
from typing import Dict, List, Set, Optional

import bpy

from .log import LoggerFactory
from . import opsdata, prefs

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

        latest_file = self._get_latest_edit(context)
        if not latest_file:
            self.report(
                {"ERROR"}, f"Found no edit file in: {editorial_path.as_posix()}"
            )

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
            filepath=latest_file.as_posix(),
            relative_path=False,
            frame_start=101,
            channel=1,
            fit_method="FIT",
        )

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


# ---------REGISTER ----------

classes = [
    AS_OT_create_actions,
    AS_OT_setup_workspaces,
    AS_OT_load_latest_edit,
    AS_OT_import_camera,
    AS_OT_import_camera_action,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
