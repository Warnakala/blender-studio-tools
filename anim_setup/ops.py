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

            # create animation data if not existent
            if not rig.animation_data:
                rig.animation_data_create()
                logger.info("%s created animation data", rig.name)

            # if action already exists check for fake user and then continue
            if rig.animation_data.action:
                logger.info("%s already has an action assigned", rig.name)

                if not rig.animation_data.action.use_fake_user:
                    rig.animation_data.action.use_fake_user = True
                    logger.info("%s assigned existing action fake user", rig.name)
                exists.append(coll)
                continue

            # create new action
            action_name_new = opsdata.gen_action_name(coll)
            try:
                action = bpy.data.actions[action_name_new]
            except KeyError:
                action = bpy.data.actions.new(action_name_new)
                logger.info("Created action: %s", action.name)
                created.append(action)
            else:
                logger.info("Action %s already exists. Will take that.", action.name)

            # assign action
            rig.animation_data.action = action
            logger.info("%s assigned action %s", rig.name, action.name)

            # add fake user
            action.use_fake_user = True
            assigned.append(action)

        self.report(
            {"INFO"},
            "Actions: Created %s | Assigned %s | Exists %s | Failed %s"
            % (len(created), len(assigned), len(exists), len(failed)),
        )
        return {"FINISHED"}


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
        frame_3d_in = shot.data["3d_in"]
        frame_3d_offset = frame_3d_in - 101

        if not frame_in:
            self.report(
                {"ERROR"}, f"On kitsu 'frame_in' is not defined for shot {shotname}."
            )
            return {"CANCELLED"}

        # set sequence strip start kitsu data
        for strip in context.scene.sequence_editor.sequences_all:
            strip.frame_start = -frame_in + (strip_frame_start * 2) + frame_3d_offset

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
        cam_action_name_new = opsdata.get_cam_action_name_from_lib(
            shotname, previs_path
        )
        if not cam_action_name_new:
            self.report(
                {"ERROR"},
                f"Camera action: {cam_action_name_new} not found in lib: {previs_path.name}",
            )
            return {"CANCELLED"}

        # import cam action data block
        cam_action = opsdata.import_data_from_lib(
            "actions", cam_action_name_new, previs_path, link=False
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


class AS_OT_import_asset_actions(bpy.types.Operator):
    """
    Imports asset action of previs file that matches current shot and assigne it
    """

    bl_idname = "as.import_asset_actions"
    bl_label = "Import Asset Actions"

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        addon_prefs = prefs.addon_prefs_get(context)
        return bool(addon_prefs.is_project_root_valid and bpy.data.filepath)

    def execute(self, context: bpy.types.Context) -> Set[str]:

        succeeded = []
        failed = []
        actions_imported = []
        renamed_actions = []

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
        action_candidates: Dict[str, List[str]] = {}
        asset_colls = []

        with bpy.data.libraries.load(
            previs_path.as_posix(), relative=True, link=False
        ) as (
            data_from,
            data_to,
        ):

            for asset in asglobals.ACTION_ASSETS:

                # check if asset is in current scene
                try:
                    coll = bpy.data.collections[asset]
                except KeyError:
                    # can continue here if not in scene we
                    # cant load action anyway
                    continue
                else:
                    logger.info("Found asset in scene: %s", coll.name)
                    asset_colls.append(coll)

                # find if actions exists for that asset in previs file
                asset_name = opsdata.find_asset_name(asset)
                for action in data_from.actions:
                    if action.startswith(f"ANI-{asset_name}."):

                        # create key if not existent yet
                        if asset not in action_candidates:
                            action_candidates[asset] = []

                        # append action to that asset
                        action_candidates[asset].append(action)

        # load and assign actions for asset colls
        for coll in asset_colls:

            # find rig
            rig = opsdata.find_rig(coll)
            if not rig:
                logger.warning("%s contains no rig.", coll.name)
                continue

            # check if action was found in previs file for that asset
            if not coll.name in action_candidates:
                logger.warning("%s no action found in previs file", coll.name)
                continue
            else:
                logger.info(
                    "%s found actions in previs file: %s",
                    asset,
                    str(action_candidates[coll.name]),
                )

            # check if multiple actions are in the prvis file for that asset
            if len(action_candidates[coll.name]) > 1:
                logger.warning(
                    "%s Multiple actions found in previs file: %s",
                    coll.name,
                    str(action_candidates[coll.name]),
                )
                continue

            # import action from previs file
            actions = action_candidates[coll.name]

            """
            try:
                bpy.data.actions[actions[0]]
            except KeyError:
                pass
            else:
                logger.warning("%s failed to import action")
            """
            action = opsdata.import_data_from_lib(
                "actions", actions[0], previs_path, link=False
            )
            if not action:
                continue

            actions_imported.append(action)

            # create animation data if not existent
            if not rig.animation_data:
                rig.animation_data_create()
                logger.info("%s created animation data", rig.name)

            # assign action
            rig.animation_data.action = action
            logger.info("%s assigned action %s", rig.name, action.name)

            # add fake user
            action.use_fake_user = True

            # rename actions
            action_name_new = opsdata.gen_action_name(coll)
            try:
                action_existing = bpy.data.actions[action_name_new]
            except KeyError:
                # action does not exists can rename
                old_name = action.name
                action.name = action_name_new
                logger.info("Renamed action: %s to %s", old_name, action.name)
                renamed_actions.append(action)
            else:
                # action name already exists in this scene
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
    """
    Imports asset action of previs file that matches current shot and assigne it
    """

    bl_idname = "as.import_multi_assets"
    bl_label = "Import Multi Assets"

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        addon_prefs = prefs.addon_prefs_get(context)
        return bool(addon_prefs.is_project_root_valid and bpy.data.filepath)

    def execute(self, context: bpy.types.Context) -> Set[str]:
        actions_imported = []
        new_colls = []

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

            # find all sprites actions
            for asset in asglobals.MULTI_ASSETS:
                # check if asset is in current scene
                try:
                    coll = bpy.data.collections[asset]
                except KeyError:
                    # can continue here if not in scene we
                    # cant load action anyway
                    continue
                else:
                    logger.info("Found asset in scene: %s", coll.name)
                    asset_colls.append(coll)

                # find if actions exists for that asset in previs file
                asset_name = opsdata.find_asset_name(asset)
                for action in data_from_actions:
                    if action.startswith(f"ANI-{asset_name}"):

                        # create key if not existent yet
                        if asset not in action_candidates:
                            action_candidates[asset] = []

                        # append action to that asset
                        action_candidates[asset].append(action)

        # load and assign actions for asset colls
        color_tag: str = ""
        for coll in asset_colls:

            # check if action was found in previs file for that asset
            if not coll.name in action_candidates:
                logger.warning("%s no action found in previs file", coll.name)
                continue
            else:
                logger.info(
                    "%s found actions in previs file: %s",
                    asset,
                    str(action_candidates[coll.name]),
                )

            # create duplicate for each action
            for idx, action_candidate in enumerate(action_candidates[coll.name]):

                # first index use existing collection that was already created by shot builder
                if idx == 0:
                    new_coll = bpy.data.collections[asset, None]
                    logger.info("First index will use existing coll: %s", new_coll.name)
                    color_tag = new_coll.color_tag  # take color from first collection
                else:
                    ref_coll = opsdata.get_ref_coll(coll)
                    new_coll = ref_coll.override_hierarchy_create(
                        context.scene, context.view_layer, reference=coll
                    )
                    new_coll.color_tag = color_tag
                    logger.info("Created new override collection: %s", new_coll.name)
                    new_colls.append(new_coll)

                # find rig of new coll
                rig = opsdata.find_rig(new_coll)
                if not rig:
                    logger.warning("%s contains no rig.", coll.name)
                    continue

                # import action
                action = opsdata.import_data_from_lib(
                    "actions", action_candidate, previs_path, link=False
                )
                if not action:
                    continue

                actions_imported.append(action)

                # create animation data if not existent
                if not rig.animation_data:
                    rig.animation_data_create()
                    logger.info("%s created animation data", rig.name)

                # assign action
                rig.animation_data.action = action
                logger.info("%s assigned action %s", rig.name, action.name)

                # add fake user
                # action.use_fake_user = True

        self.report(
            {"INFO"},
            f"Found Assets: {len(asset_colls)} | Imported Actions: {len(actions_imported)} | New collections: {len(new_colls)}",
        )
        return {"FINISHED"}


class AS_OT_shift_anim(bpy.types.Operator):
    """
    Shifts the animation as well as anim modifier values of the camera by number of frames
    """

    bl_idname = "as.shift_anim"
    bl_label = "Shift Anim"
    multi_assets: bpy.props.BoolProperty(name="Do Multi Assets")

    def execute(self, context: bpy.types.Context) -> Set[str]:
        nr_of_frames = context.scene.anim_setup.shift_frames
        rigs: List[bpy.types.Armature] = []

        if not self.multi_assets:
            # get cam coll
            try:
                rig = bpy.data.objects["RIG-camera", None]
            except KeyError:
                logger.warning("Failed to find camera object 'RIG-camera'")
            else:
                rigs.append(rig)

            # find assets
            for asset in asglobals.ACTION_ASSETS:

                # check if asset is in current scene
                try:
                    coll = bpy.data.collections[asset]
                except KeyError:
                    # can continue here if not in scene we
                    # cant load action anyway
                    continue
                else:
                    logger.info("Found asset in scene: %s", coll.name)
                    # find rig
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
                    # find rig
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

                # shift all keyframes
                for point in fcurve.keyframe_points:
                    # print(f"{fcurve.data_path}|{fcurve.array_index}: {point.co.x}|{point.co.y}")
                    point.co.x += nr_of_frames
                    # don't forget the keyframe's handles:
                    point.handle_left.x += nr_of_frames
                    point.handle_right.x += nr_of_frames

                """
                logger.info(
                    "%s: %s shifted all keyframes by %i frames",
                    fcurve.id_data.name,
                    fcurve.data_path,
                    nr_of_frames,
                )
                """

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
            logger.info(
                "%s: %s shifted all keyframes by %i frames",
                rig.name,
                rig.animation_data.action.name,
                nr_of_frames,
            )

        self.report(
            {"INFO"}, f"Shifted animation of {len(rigs)} actions by {nr_of_frames}"
        )
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


class AS_OT_apply_additional_settings(bpy.types.Operator):

    bl_idname = "as.apply_additional_settings"
    bl_label = "Apply Additional Settings"

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
    """
    Excludes Collections that are not needed for Animation
    """

    bl_idname = "as.exclude_colls"
    bl_label = "Exclude Collections"

    def execute(self, context: bpy.types.Context) -> Set[str]:
        view_layer_colls = opsdata.get_all_view_layer_colls(context)

        excluded = []
        for coll_name in asglobals.HIDE_COLLS:
            # find view layer collection, if same collection is linked in in 2 different colls in same scene, these
            # are 2 different view layer colls, we need to grab all
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
            {"INFO"}, f"Exluded Collections: {list([v.name for v in excluded])}"
        )
        return {"FINISHED"}


# ---------REGISTER ----------

classes = [
    AS_OT_create_actions,
    AS_OT_setup_workspaces,
    AS_OT_load_latest_edit,
    AS_OT_import_camera,
    AS_OT_import_camera_action,
    AS_OT_shift_anim,
    AS_OT_get_frame_shift,
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
