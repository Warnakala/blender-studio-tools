from pathlib import Path
from typing import Dict, List, Set, Optional

import bpy

from .log import LoggerFactory


logger = LoggerFactory.getLogger()


def ui_redraw() -> None:
    """
    Forces blender to redraw the UI.
    """
    for screen in bpy.data.screens:
        for area in screen.areas:
            area.tag_redraw()


class AS_OT_create_action(bpy.types.Operator):
    """
    Creates default action for active collection
    """

    bl_idname = "as.create_action"
    bl_label = "Create action"
    bl_options = {"INTERNAL"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        act_coll = context.view_layer.active_layer_collection.collection
        return bool(bpy.data.filepath and act_coll)

    def execute(self, context: bpy.types.Context) -> Set[str]:
        act_coll = context.view_layer.active_layer_collection.collection

        if not act_coll:
            self.report({"WARNING"}, "Active collection needed")
            return {"CANCELLED"}

        rig = self._find_rig(act_coll)

        if not rig:
            self.report({"WARNING"}, f"{act_coll.name} contains no rig.")
            return {"CANCELLED"}

        # create new action
        action_name = self._gen_action_name(rig)
        if action_name not in list(bpy.data.actions):
            action = bpy.data.actions.new(action_name)
            logger.info("Created action: %s", action.name)
        else:
            action = bpy.data.actions[action_name]

        # assign action
        rig.animation_data.action = action
        logger.info("%s assigned action %s", rig.name, action.name)

        # add fake user
        action.use_fake_user = True

        return {"FINISHED"}

    def _find_rig(self, coll: bpy.types.Collection) -> Optional[bpy.types.Armature]:

        coll_suffix = self._find_asset_name(coll.name)

        for obj in coll.all_objects:
            # default rig name: 'RIG-rex' / 'RIG-Rex'
            if obj.type != "ARMATURE":
                continue

            if not obj.name.startswith("RIG"):
                continue

            if obj.name.lower() == f"rig-{coll_suffix.lower()}":
                logger.info("Found rig: %s", obj.name)
                return obj

        return None

    def _gen_action_name(self, armature: bpy.types.Armature):
        action_prefix = "ANI"
        asset_name = self._find_asset_name(armature.name).lower()
        version = "v001"
        shot_name = self._get_shot_name_from_file()

        action_name = f"{action_prefix}-{asset_name}.{shot_name}.{version}"

        if self._is_multi_asset(asset_name):
            action_name = f"{action_prefix}-{asset_name}_A.{shot_name}.{version}"

        return action_name

    def _find_asset_name(self, name: str) -> str:
        return name.split("-")[-1]  # CH-rex -> 'rex'

    def _get_shot_name_from_file(self) -> Optional[str]:
        if not bpy.data.filepath:
            return None

        # default 110_0030_A.anim.blend
        return Path(bpy.data.filepath).name.split(".")[0]

    def _is_multi_asset(self, asset_name: str) -> bool:
        multi_assets = ["sprite", "snail"]
        if asset_name.lower() in multi_assets:
            return True
        return False


# ---------REGISTER ----------

classes = [AS_OT_create_action]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
