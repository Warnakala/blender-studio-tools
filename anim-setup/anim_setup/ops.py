import re
from pathlib import Path
import types
from typing import Container, Dict, List, Set, Optional

import bpy

from .log import LoggerFactory
from .kitsu import KitsuConnector, Shot, Project, Sequence
from . import opsdata, prefs, asglobals

logger = LoggerFactory.getLogger()


def ui_redraw() -> None:
    """Forces blender to redraw the UI."""
    for screen in bpy.data.screens:
        for area in screen.areas:
            area.tag_redraw()


class AS_OT_create_actions(bpy.types.Operator):
    bl_idname = "as.create_action"
    bl_label = "Create action"
    bl_description = (
        "Creates action for all found assets that have no assigned yet. "
        "Names them following the blender-studio convention"
    )

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        act_coll = context.view_layer.active_layer_collection.collection
        return bool(bpy.data.filepath and act_coll)

    def execute(self, context: bpy.types.Context) -> Set[str]:
        assigned: List[bpy.types.Action] = []
        created: List[bpy.types.Action] = []
        failed: List[bpy.types.Collection] = []
        collections = opsdata.get_valid_collections(context)
        exists: List[bpy.types.Collection] = []

        if not collections:
            self.report({"WARNING"}, "No valid collections available")
            return {"CANCELLED"}

        for coll in collections:
            print("\n")
            rig = opsdata.find_rig(coll)

            if not rig:
                logger.warning(f"{coll.name} contains no rig.")
                failed.append(coll)
                continue

            # Create animation data if not existent.
            if not rig.animation_data:
                rig.animation_data_create()
                logger.info("%s created animation data", rig.name)

            # If action already exists check for fake user and then continue.
            if rig.animation_data.action:
                logger.info("%s already has an action assigned", rig.name)

                if not rig.animation_data.action.use_fake_user:
                    rig.animation_data.action.use_fake_user = True
                    logger.info("%s assigned existing action fake user", rig.name)
                exists.append(coll)
                continue

            # Create new action.
            action_name_new = opsdata.gen_action_name(coll)
            try:
                action = bpy.data.actions[action_name_new]
            except KeyError:
                action = bpy.data.actions.new(action_name_new)
                logger.info("Created action: %s", action.name)
                created.append(action)
            else:
                logger.info("Action %s already exists. Will take that.", action.name)

            # Assign action.
            rig.animation_data.action = action
            logger.info("%s assigned action %s", rig.name, action.name)

            # Add fake user.
            action.use_fake_user = True
            assigned.append(action)

        self.report(
            {"INFO"},
            "Actions: Created %s | Assigned %s | Exists %s | Failed %s"
            % (len(created), len(assigned), len(exists), len(failed)),
        )
        return {"FINISHED"}


class AS_OT_setup_workspaces(bpy.types.Operator):
    bl_idname = "as.setup_workspaces"
    bl_label = "Setup Workspace"
    bl_description = "Sets up the workspaces for the animation task"

    def execute(self, context: bpy.types.Context) -> Set[str]:

        # Remove non anim workspaces.
        for ws in bpy.data.workspaces:
            if ws.name != "Animation":
                bpy.ops.workspace.delete({"workspace": ws})

            self.report({"INFO"}, "Deleted non Animation workspaces")

        return {"FINISHED"}


class AS_OT_load_latest_edit(bpy.types.Operator):
    bl_idname = "as.load_latest_edit"
    bl_label = "Load edit"
    bl_description = (
        "Loads latest edit from shot_preview_folder "
        "Shifts edit so current shot starts at 3d_in metadata shot key from Kitsu"
    )

    @classmethod
    def can_load_edit(cls, context: bpy.types.Context) -> bool:
        """Check if shared dir and VSE area are available"""
        addon_prefs = prefs.addon_prefs_get(context)
        edit_export_path = Path(addon_prefs.edit_export_path)

        # Needs to be run in sequence editor area
        # TODO: temporarily create a VSE area if not available.
        area_override = None
        for area in bpy.context.screen.areas:
            if area.type == "SEQUENCE_EDITOR":
                area_override = area

        return bool(area_override and edit_export_path)

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return cls.can_load_edit(context)

    @classmethod
    def description(cls, context, properties):
        if cls.can_load_edit(context):
            return "Load latest edit from shared folder"
        else:
            return "Shared folder not set, or VSE area not available in this workspace"

    def execute(self, context: bpy.types.Context) -> Set[str]:

        addon_prefs = prefs.addon_prefs_get(context)
        edit_export_path = Path(addon_prefs.edit_export_path)
        strip_channel = 1
        latest_file = self._get_latest_edit(context)
        if not latest_file:
            self.report(
                {"ERROR"}, f"Found no edit file in: {edit_export_path.as_posix()}"
            )
        strip_filepath = latest_file.as_posix()
        strip_frame_start = 101

        # Needs to be run in sequence editor area.
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

        # Get sequence name.
        seqname = opsdata.get_sequence_from_file()
        if not seqname:
            self.report({"ERROR"}, "Failed to retrieve seqname from current file.")
            return {"CANCELLED"}

        # Get shotname.
        shotname = opsdata.get_shot_name_from_file()
        if not shotname:
            self.report({"ERROR"}, "Failed to retrieve shotname from current file.")
            return {"CANCELLED"}

        # Setup connector and get data from kitsu.
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

        # Update shift frame range prop.
        frame_in = shot.data["frame_in"]
        frame_out = shot.data["frame_out"]
        frame_3d_in = shot.data["3d_in"]
        frame_3d_offset = frame_3d_in - 101

        if not frame_in:
            self.report(
                {"ERROR"}, f"On kitsu 'frame_in' is not defined for shot {shotname}."
            )
            return {"CANCELLED"}

        # Set sequence strip start kitsu data.
        for strip in context.scene.sequence_editor.sequences_all:
            strip.frame_start = -frame_in + (strip_frame_start * 2) + frame_3d_offset

        self.report({"INFO"}, f"Loaded latest edit: {latest_file.name}")

        return {"FINISHED"}

    def _get_latest_edit(self, context: bpy.types.Context):
        addon_prefs = prefs.addon_prefs_get(context)

        edit_export_path = Path(addon_prefs.edit_export_path)

        files_list = [
            f
            for f in edit_export_path.iterdir()
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
    bl_idname = "as.import_camera"
    bl_label = "Import Camera"
    bl_description = "Imports camera rig and makes library override"

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        addon_prefs = prefs.addon_prefs_get(context)
        return bool(addon_prefs.is_project_root_valid and bpy.data.filepath)

    def execute(self, context: bpy.types.Context) -> Set[str]:

        addon_prefs = prefs.addon_prefs_get(context)

        # Import camera rig and make override.
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
    bl_idname = "as.import_camera_action"
    bl_label = "Import Camera Action"
    bl_description = (
        "Imports camera action of previs file that matches current shot and assigns it"
    )

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

        # Import camera action from previz file.

        # Get shotname and previs filepath.
        shotname = opsdata.get_shot_name_from_file()
        if not shotname:
            self.report({"ERROR"}, "Failed to retrieve shotname from current file.")
            return {"CANCELLED"}

        previs_path = opsdata.get_previs_file(context)
        if not previs_path:
            self.report({"ERROR"}, "Failed to find previz file")
            return {"CANCELLED"}

        # Check if cam action name exists in previs library.
        cam_action_name_new = opsdata.get_cam_action_name_from_lib(
            shotname, previs_path
        )
        if not cam_action_name_new:
            self.report(
                {"ERROR"},
                f"Camera action: {cam_action_name_new} not found in lib: {previs_path.name}",
            )
            return {"CANCELLED"}

        # Import cam action data block.
        cam_action = opsdata.import_data_from_lib(
            "actions", cam_action_name_new, previs_path, link=False
        )

        # Find rig to assing action to.
        rig = opsdata.find_rig(cam_coll)
        if not rig:
            self.report({"WARNING"}, f"{cam_coll.name} contains no rig.")
            return {"CANCELLED"}

        # Assign action.
        rig.animation_data.action = cam_action
        logger.info("%s assigned action %s", rig.name, cam_action.name)

        # Add fake user.
        cam_action.use_fake_user = True

        # Ensure version suffix to action data bloc.
        opsdata.ensure_name_version_suffix(cam_action)

        self.report({"INFO"}, f"{rig.name} imported camera action: {cam_action.name}")
        return {"FINISHED"}


class AS_OT_import_asset_actions(bpy.types.Operator):
    """Imports asset action of previs file that matches current shot and assigns it"""

    bl_idname = "as.import_asset_actions"
    bl_label = "Import Asset Actions"
    bl_description = (
        "For each found asset tries to find action in previs file. "
        "Imports it to current file, renames it, adds fake user and assigns it"
    )

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        addon_prefs = prefs.addon_prefs_get(context)
        return bool(addon_prefs.is_project_root_valid and bpy.data.filepath)

    def execute(self, context: bpy.types.Context) -> Set[str]:

        succeeded = []
        failed = []
        actions_imported = []
        renamed_actions = []

        # Get shotname and previs filepath.
        shotname = opsdata.get_shot_name_from_file()
        if not shotname:
            self.report({"ERROR"}, "Failed to retrieve shotname from current file.")
            return {"CANCELLED"}

        previs_path = opsdata.get_previs_file(context)
        if not previs_path:
            self.report({"ERROR"}, "Failed to find previz file")
            return {"CANCELLED"}

        # Check if cam action name exists in previs library.
        action_candidates: Dict[str, List[str]] = {}
        asset_colls = []

        with bpy.data.libraries.load(
            previs_path.as_posix(), relative=True, link=False
        ) as (
            data_from,
            data_to,
        ):

            for asset in asglobals.ACTION_ASSETS:

                # Check if asset is in current scene.
                try:
                    coll = bpy.data.collections[asset]
                except KeyError:
                    # can continue here if not in scene we
                    # cant load action anyway
                    continue
                else:
                    logger.info("Found asset in scene: %s", coll.name)
                    asset_colls.append(coll)

                # Find if actions exists for that asset in previs file.
                asset_name = opsdata.find_asset_name(asset)
                for action in data_from.actions:
                    if action.startswith(f"ANI-{asset_name}."):

                        # Create key if not existent yet.
                        if asset not in action_candidates:
                            action_candidates[asset] = []

                        # Append action to that asset.
                        action_candidates[asset].append(action)

        # Load and assign actions for asset colls.
        for coll in asset_colls:

            # Find rig.
            rig = opsdata.find_rig(coll)
            if not rig:
                logger.warning("%s contains no rig.", coll.name)
                continue

            # Check if action was found in previs file for that asset.
            if not coll.name in action_candidates:
                logger.warning("%s no action found in previs file", coll.name)
                continue
            else:
                logger.info(
                    "%s found actions in previs file: %s",
                    asset,
                    str(action_candidates[coll.name]),
                )

            # Check if multiple actions are in the prvis file for that asset.
            if len(action_candidates[coll.name]) > 1:
                logger.warning(
                    "%s Multiple actions found in previs file: %s",
                    coll.name,
                    str(action_candidates[coll.name]),
                )
                continue

            # Import action from previs file.
            actions = action_candidates[coll.name]
            action = opsdata.import_data_from_lib(
                "actions", actions[0], previs_path, link=False
            )
            if not action:
                continue

            actions_imported.append(action)

            # Create animation data if not existent.
            if not rig.animation_data:
                rig.animation_data_create()
                logger.info("%s created animation data", rig.name)

            # Assign action.
            rig.animation_data.action = action
            logger.info("%s assigned action %s", rig.name, action.name)

            # Add fake user.
            action.use_fake_user = True

            # Rename actions.
            action_name_new = opsdata.gen_action_name(coll)
            try:
                action_existing = bpy.data.actions[action_name_new]
            except KeyError:
                # Action does not exists can rename.
                old_name = action.name
                action.name = action_name_new
                logger.info("Renamed action: %s to %s", old_name, action.name)
                renamed_actions.append(action)
            else:
                # Action name already exists in this scene.
                logger.info(
                    "Failed to rename action action %s to %s. Already exists",
                    action.name,
                    action_name_new,
                )
                continue

        self.report(
            {"INFO"},
            f"Found Assets: {len(asset_colls)} | Imported Actions: {len(actions_imported)} | Renamed Actions: {len(renamed_actions)}",
        )
        return {"FINISHED"}


class AS_OT_import_multi_assets(bpy.types.Operator):
    bl_idname = "as.import_multi_assets"
    bl_label = "Import Multi Assets"
    bl_description = (
        "For each found multi asset tries to find action in previs file. "
        "Imports it to current file, renames it, adds fake user and assigns it"
    )

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        addon_prefs = prefs.addon_prefs_get(context)
        return bool(addon_prefs.is_project_root_valid and bpy.data.filepath)

    def execute(self, context: bpy.types.Context) -> Set[str]:
        actions_imported = []
        new_colls = []

        # Get shotname and previs filepath.
        shotname = opsdata.get_shot_name_from_file()
        if not shotname:
            self.report({"ERROR"}, "Failed to retrieve shotname from current file.")
            return {"CANCELLED"}

        previs_path = opsdata.get_previs_file(context)
        if not previs_path:
            self.report({"ERROR"}, "Failed to find previz file")
            return {"CANCELLED"}

        # Check if cam action name exists in previs library.
        action_candidates: Dict[str, List[str]] = {}
        asset_colls: List[bpy.types.Collection] = []

        with bpy.data.libraries.load(
            previs_path.as_posix(), relative=True, link=False
        ) as (
            data_from,
            data_to,
        ):
            data_from_actions: List[str] = data_from.actions
            data_from_actions.sort()

            # Find all sprites actions.
            for asset in asglobals.MULTI_ASSETS:
                # Check if asset is in current scene.
                try:
                    coll = bpy.data.collections[asset]
                except KeyError:
                    # Can continue here if not in scene we
                    # cant load action anyway.
                    continue
                else:
                    logger.info("Found asset in scene: %s", coll.name)
                    asset_colls.append(coll)

                # Find if actions exists for that asset in previs file.
                asset_name = opsdata.find_asset_name(asset)
                for action in data_from_actions:
                    if action.startswith(f"ANI-{asset_name}"):

                        # Create key if not existent yet.
                        if asset not in action_candidates:
                            action_candidates[asset] = []

                        # Append action to that asset.
                        action_candidates[asset].append(action)

        # Load and assign actions for asset colls.
        color_tag: str = ""
        for coll in asset_colls:

            # Check if action was found in previs file for that asset.
            if not coll.name in action_candidates:
                logger.warning("%s no action found in previs file", coll.name)
                continue
            else:
                logger.info(
                    "%s found actions in previs file: %s",
                    asset,
                    str(action_candidates[coll.name]),
                )

            # Create duplicate for each action.
            for idx, action_candidate in enumerate(action_candidates[coll.name]):

                # First index use existing collection that was already created by shot builder.
                if idx == 0:
                    new_coll = bpy.data.collections[asset, None]
                    logger.info("First index will use existing coll: %s", new_coll.name)
                    color_tag = new_coll.color_tag  # Take color from first collection.
                else:
                    ref_coll = opsdata.get_ref_coll(coll)
                    new_coll = ref_coll.override_hierarchy_create(
                        context.scene, context.view_layer, reference=coll
                    )
                    new_coll.color_tag = color_tag
                    logger.info("Created new override collection: %s", new_coll.name)
                    new_colls.append(new_coll)

                # Find rig of new coll.
                rig = opsdata.find_rig(new_coll)
                if not rig:
                    logger.warning("%s contains no rig.", coll.name)
                    continue

                # Import action.
                action = opsdata.import_data_from_lib(
                    "actions", action_candidate, previs_path, link=False
                )
                if not action:
                    continue

                actions_imported.append(action)

                # Create animation data if not existent.
                if not rig.animation_data:
                    rig.animation_data_create()
                    logger.info("%s created animation data", rig.name)

                # Assign action.
                rig.animation_data.action = action
                logger.info("%s assigned action %s", rig.name, action.name)

        self.report(
            {"INFO"},
            f"Found Assets: {len(asset_colls)} | Imported Actions: {len(actions_imported)} | New collections: {len(new_colls)}",
        )
        return {"FINISHED"}


class AS_OT_shift_anim(bpy.types.Operator):
    bl_idname = "as.shift_anim"
    bl_label = "Shift Anim"
    bl_description = (
        "Shifts the animation of found assets by number of frames. "
        "It also shifts the camera animation as well as its modifier values"
    )

    multi_assets: bpy.props.BoolProperty(name="Do Multi Assets")

    def execute(self, context: bpy.types.Context) -> Set[str]:
        # Define the frame offset by:
        # Subtracting the layout cut in frame (to set the 0)
        # Adding 101 (the animation start for a shot)
        # For example, layout frame 520 becomes frames_offset -520 + 101 = -419.

        frames_offset = -context.scene.anim_setup.layout_cut_in + 101
        rigs: List[bpy.types.Armature] = []

        if not self.multi_assets:
            # Get cam coll.
            try:
                rig = bpy.data.objects["RIG-camera", None]
            except KeyError:
                logger.warning("Failed to find camera object 'RIG-camera'")
            else:
                rigs.append(rig)

            # Find assets.
            for asset in asglobals.ACTION_ASSETS:

                # Check if asset is in current scene.
                try:
                    coll = bpy.data.collections[asset]
                except KeyError:
                    # Can continue here if not in scene we
                    # cant load action anyway.
                    continue
                else:
                    logger.info("Found asset in scene: %s", coll.name)
                    # Find rig.
                    rig = opsdata.find_rig(coll)
                    if not rig:
                        logger.warning("%s contains no rig.", coll.name)
                        continue
                    rigs.append(rig)
        else:
            for asset in asglobals.MULTI_ASSETS:
                for coll in bpy.data.collections:

                    if not opsdata.is_item_lib_override(coll):
                        continue

                    if not coll.name.startswith(asset):
                        continue

                    logger.info("Found asset in scene: %s", coll.name)
                    # Find rig.
                    rig = opsdata.find_rig(coll)
                    if not rig:
                        logger.warning("%s contains no rig.", coll.name)
                        continue
                    rigs.append(rig)

        if not rigs:
            self.report(
                {"ERROR"}, "Failed to find any assets or cameras to shift animation."
            )
            return {"CANCELLED"}

        for rig in rigs:
            for fcurve in rig.animation_data.action.fcurves:

                # Shift all keyframes.
                for point in fcurve.keyframe_points:
                    # Print(f"{fcurve.data_path}|{fcurve.array_index}: {point.co.x}|{point.co.y}").
                    point.co.x += frames_offset
                    # Don't forget the keyframe's handles:.
                    point.handle_left.x += frames_offset
                    point.handle_right.x += frames_offset

                # Shift all noise modififers values.
                for m in fcurve.modifiers:
                    if not m.type == "NOISE":
                        continue

                    m.offset += frames_offset

                    if m.use_restricted_range:
                        frame_start = m.frame_start
                        frame_end = m.frame_end
                        m.frame_start = frame_start + (frames_offset)
                        m.frame_end = frame_end + (frames_offset)

                    logger.info(
                        "%s shifted %s modifier values by %i frames",
                        m.id_data.name,
                        m.type.lower(),
                        frames_offset,
                    )
            logger.info(
                "%s: %s shifted all keyframes by %i frames",
                rig.name,
                rig.animation_data.action.name,
                frames_offset,
            )

        self.report(
            {"INFO"}, f"Shifted animation of {len(rigs)} actions by {frames_offset}"
        )
        return {"FINISHED"}


class AS_OT_apply_additional_settings(bpy.types.Operator):

    bl_idname = "as.apply_additional_settings"
    bl_label = "Apply Additional Settings"
    bl_description = (
        "Apply some additional settings that are important " "for animation scenes"
    )

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        sqe_area = cls._get_sqe_area(context)
        return bool(sqe_area)

    def execute(self, context: bpy.types.Context) -> Set[str]:

        sqe_area = self._get_sqe_area(context)

        sqe_area.spaces.active.use_proxies = False
        sqe_area.spaces.active.proxy_render_size = "PROXY_100"

        self.report({"INFO"}, "Set: use_proxies | proxy_render_size")
        return {"FINISHED"}

    @classmethod
    def _get_sqe_area(cls, context: bpy.types.Context):
        for window in context.window_manager.windows:
            screen = window.screen

            for area in screen.areas:
                if area.type == "SEQUENCE_EDITOR":
                    return area

        return None


class AS_OT_exclude_colls(bpy.types.Operator):
    """Excludes Collections that are not needed for animation"""

    bl_idname = "as.exclude_colls"
    bl_label = "Exclude Collections"
    bl_description = (
        "Exclude some collections by name that are not needed in animation scenes"
    )

    def execute(self, context: bpy.types.Context) -> Set[str]:
        view_layer_colls = opsdata.get_all_view_layer_colls(context)

        excluded = []
        for coll_name in asglobals.HIDE_COLLS:
            # Find view layer collection, if same collection is linked in in 2 different colls in same scene, these
            # are 2 different view layer colls, we need to grab all.
            valid_view_layer_colls = [
                vc for vc in view_layer_colls if vc.name == coll_name
            ]

            if not valid_view_layer_colls:
                logger.info("No view layer collections named: %s", coll_name)
                continue

            for view_layer_coll in valid_view_layer_colls:
                view_layer_coll.exclude = True
                logger.info("Excluded view layer collection: %s", view_layer_coll.name)
                excluded.append(view_layer_coll)

        self.report(
            {"INFO"}, f"Excluded Collections: {list([v.name for v in excluded])}"
        )
        return {"FINISHED"}


# ---------REGISTER ----------.

classes = [
    AS_OT_create_actions,
    AS_OT_setup_workspaces,
    AS_OT_load_latest_edit,
    AS_OT_import_camera,
    AS_OT_import_camera_action,
    AS_OT_shift_anim,
    AS_OT_apply_additional_settings,
    AS_OT_import_asset_actions,
    AS_OT_exclude_colls,
    AS_OT_import_multi_assets,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
