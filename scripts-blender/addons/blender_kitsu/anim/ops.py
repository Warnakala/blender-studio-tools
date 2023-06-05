# ***** BEGIN GPL LICENSE BLOCK *****
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
# ***** END GPL LICENCE BLOCK *****
#
# (c) 2021, Blender Foundation - Paul Golter

from typing import List, Set, Tuple

import bpy

from blender_kitsu import (
    cache,
    util,
)
from blender_kitsu.logger import LoggerFactory

from blender_kitsu.anim import opsdata

logger = LoggerFactory.getLogger()


class KITSU_OT_anim_quick_duplicate(bpy.types.Operator):
    bl_idname = "kitsu.anim_quick_duplicate"
    bl_label = "Quick Duplicate"
    bl_description = (
        "Duplicate the active collection and add it to the "
        "output collection of the current scene"
    )

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        act_coll = context.view_layer.active_layer_collection.collection

        return bool(
            cache.shot_active_get()
            and context.view_layer.active_layer_collection.collection
            and not opsdata.is_item_local(act_coll)
        )

    def execute(self, context: bpy.types.Context) -> Set[str]:
        act_coll = context.view_layer.active_layer_collection.collection
        shot_active = cache.shot_active_get()
        amount = context.window_manager.kitsu.quick_duplicate_amount

        if not act_coll:
            self.report({"ERROR"}, f"No collection selected")
            return {"CANCELLED"}

        # Check if output colletion exists in scene.
        try:
            output_coll = bpy.data.collections[
                opsdata.get_output_coll_name(shot_active)
            ]

        except KeyError:
            self.report(
                {"ERROR"},
                f"Missing output collection: {opsdata.get_output_coll_name(shot_active)}",
            )
            return {"CANCELLED"}

        # Get ref coll.
        ref_coll = opsdata.get_ref_coll(act_coll)

        for i in range(amount):
            # Create library override.
            coll = ref_coll.override_hierarchy_create(
                context.scene, context.view_layer, reference=act_coll
            )

            # Set color tag to be the same.
            coll.color_tag = act_coll.color_tag

            # Link coll in output collection.
            if coll not in list(output_coll.children):
                output_coll.children.link(coll)

        # Report.
        self.report(
            {"INFO"},
            f"Created {amount} Duplicates of: {act_coll.name} and added to {output_coll.name}",
        )

        util.ui_redraw()
        return {"FINISHED"}


class KITSU_OT_anim_check_action_names(bpy.types.Operator):
    bl_idname = "kitsu.anim_check_action_names"
    bl_label = "Check Action Names "
    bl_options = {"REGISTER", "UNDO"}
    bl_description = (
        "Inspect all action names of .blend file and check "
        "if they follow the Blender Studio naming convention"
    )
    wrong: List[Tuple[bpy.types.Action, str]] = []
    # List of tuples that contains the action on index 0 with the wrong name
    # and the name it should have on index 1.

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return bool(cache.shot_active_get())

    def execute(self, context: bpy.types.Context) -> Set[str]:
        active_shot = cache.shot_active_get()
        addon_prefs = bpy.context.preferences.addons["blender_kitsu"].preferences

        existing_action_names = [a.name for a in bpy.data.actions]
        failed = []
        succeeded = []

        for obj in [obj for obj in bpy.data.objects if obj.type == "ARMATURE"]:
            # Cerate Action if None Exists
            if obj.animation_data is None or obj.animation_data.action is None:
                base_name = obj.name.split(addon_prefs.shot_builder_armature_prefix)[-1]
                new_action = bpy.data.actions.new(
                    f"{addon_prefs.shot_builder_action_prefix}{base_name}.{active_shot.name}.v001"
                )
                new_action.use_fake_user = True
                obj.animation_data_create()
                obj.animation_data.action = new_action
                obj.animation_data.action.name = f"{addon_prefs.shot_builder_action_prefix}{base_name}.{active_shot.name}.v001"

        # Rename actions.
        for action, name in self.wrong:
            if name in existing_action_names:
                logger.warning(
                    "Failed to rename action %s to %s. Action with that name already exists",
                    action.name,
                    name,
                )
                failed.append(action)
                continue

            old_name = action.name
            action.name = name
            existing_action_names.append(action.name)
            succeeded.append(action)
            logger.info("Renamed action %s to %s", old_name, action.name)

        # Report.
        report_str = f"Renamed actions: {len(succeeded)}"
        report_state = "INFO"
        if failed:
            report_state = "WARNING"
            report_str += f" | Failed: {len(failed)}"

        self.report(
            {report_state},
            report_str,
        )

        # Clear action names cache.
        opsdata.action_names_cache.clear()

        return {"FINISHED"}

    def invoke(self, context, event):
        shot_active = cache.shot_active_get()
        self.wrong.clear()
        no_action = []
        correct = []

        # Clear action names cache.
        opsdata.action_names_cache.clear()
        opsdata.action_names_cache.extend([a.name for a in bpy.data.actions])

        # Find all asset collections in .blend.
        asset_colls = opsdata.find_asset_collections()

        if not asset_colls:
            self.report(
                {"WARNING"},
                f"Failed to find any asset collections",
            )
            return {"CANCELLED"}

        # Find rig of each asset collection.
        asset_rigs: List[Tuple[bpy.types.Collection, bpy.types.Armature]] = []
        for coll in asset_colls:
            rig = opsdata.find_rig(coll, log=False)
            if rig:
                asset_rigs.append((coll, rig))

        if not asset_rigs:
            self.report(
                {"WARNING"},
                f"Failed to find any valid rigs",
            )
            return {"CANCELLED"}

        # For each rig check the current action name if it matches the convention.
        for coll, rig in asset_rigs:
            if not rig.animation_data or not rig.animation_data.action:
                logger.info("%s has no animation data", rig.name)
                no_action.append(rig)
                continue

            action_name_should = opsdata.gen_action_name(rig, coll, shot_active)
            action_name_is = rig.animation_data.action.name

            # If action name does not follow convention append it to wrong list.
            if action_name_is != action_name_should:
                logger.warning(
                    "Action %s should be named %s", action_name_is, action_name_should
                )
                self.wrong.append((rig.animation_data.action, action_name_should))

                # Extend action_names_cache list so any follow up items in loop can
                # access that information and adjust postfix accordingly.
                opsdata.action_names_cache.append(action_name_should)
                continue

            # Action name of rig is correct.
            correct.append(rig)

        if not self.wrong:
            self.report({"INFO"}, "All actions names are correct")
            return {"FINISHED"}

        self.report(
            {"INFO"},
            f"Checked Rigs: {len(asset_rigs)} | Wrong Actions {len(correct)} | Correct Actions: {len(correct)} | No Actions: {len(no_action)}",
        )
        return context.window_manager.invoke_props_dialog(self, width=500)

    def draw(self, context):
        layout = self.layout

        for action, name in self.wrong:
            row = layout.row()
            row.label(text=action.name)
            row.label(text="", icon="FORWARD")
            row.label(text=name)


class KITSU_OT_anim_enforce_naming_convention(bpy.types.Operator):
    bl_idname = "kitsu.anim_enforce_naming_convention"
    bl_label = "Set Name Conventions"
    bl_options = {"REGISTER", "UNDO"}
    bl_description = "Fix Naming of Scene, Output Collection, Actions, and optionally Find and remove a given string"

    remove_str: bpy.props.StringProperty(
        name="Find and Replace",
        default="",
    )
    rename_scene: bpy.props.BoolProperty(name="Rename Scene", default=True)
    rename_output_col: bpy.props.BoolProperty(
        name="Rename Output Collection", default=True
    )
    find_replace: bpy.props.BoolProperty(
        name="Find and Remove",
        default=False,
        description="Remove this string from Collection, Object and Object Data names. Used to remove suffixes from file names such as '.001'",
    )

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=500)

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "rename_scene")
        layout.prop(self, "rename_actions")
        layout.prop(self, "rename_output_col")
        layout.prop(self, "find_replace")
        if self.find_replace:
            layout.prop(self, "remove_str")

    def rename_datablock(self, data_block, replace: str):
        # Return Early if data_block is linked but not overriden
        if data_block is None or data_block.library is not None:
            return
        if replace in data_block.name:
            data_block.name = data_block.name.replace(replace, "")
            return data_block.name

    def execute(self, context: bpy.types.Context):
        shot_base_name = bpy.path.basename(bpy.data.filepath).replace(".anim.blend", "")
        scene_col = context.scene.collection
        anim_suffix = "anim.output"

        if self.find_replace:
            for col in scene_col.children_recursive:
                self.rename_datablock(col, self.remove_str)
                for obj in col.objects:
                    self.rename_datablock(obj, self.remove_str)
                    self.rename_datablock(obj.data, self.remove_str)

        if self.rename_output_col:
            output_cols = [
                col
                for col in context.scene.collection.children_recursive
                if anim_suffix in col.name
            ]
            if len(output_cols) != 1:
                self.report(
                    {"INFO"},
                    f"Animation Output Collection could not be found",
                )

                return {"CANCELLED"}
            output_col = output_cols[0]
            output_col.name = f"{shot_base_name}.{anim_suffix}"

        # Rename Scene
        if self.rename_scene:
            context.scene.name = f"{shot_base_name}.anim"

        self.report(
            {"INFO"},
            f"Naming Conventions Enforced",
        )
        return {"FINISHED"}


class KITSU_OT_unlink_collection_with_string(bpy.types.Operator):
    bl_idname = "kitsu.unlink_collection_with_string"
    bl_label = "Find and Unlink Collections"
    bl_options = {"REGISTER", "UNDO"}
    bl_description = (
        "Unlink any Collection with a given name. By default name is 'OVERRIDE_HIDDEN'"
    )

    remove_collection_string: bpy.props.StringProperty(
        name="Find in Name",
        default='OVERRIDE_HIDDEN',
        description="Search for this string withing current scene's collections. Collection will be unlinked if it matches given string'",
    )

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=500)

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "remove_collection_string")

    def execute(self, context):
        scene_cols = context.scene.collection.children
        cols = [col for col in scene_cols if self.remove_collection_string in col.name]
        cleaned = False
        for col in cols:
            cleaned = True
            scene_cols.unlink(col)
            self.report(
                {"INFO"},
                f"Removed Collection '{col.name}'",
            )
        if not cleaned:
            self.report(
                {"INFO"},
                f"No Collections found containing name '{self.remove_collection_string}'",
            )
        return {"FINISHED"}


class KITSU_OT_anim_update_output_coll(bpy.types.Operator):
    bl_idname = "kitsu.anim_update_output_coll"
    bl_label = "Update Output Collection"
    bl_options = {"REGISTER", "UNDO"}
    bl_description = (
        "Scans scene for any collections that are not yet in the output collection"
    )

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        active_shot = cache.shot_active_get()
        output_coll_name = opsdata.get_output_coll_name(active_shot)
        try:
            output_coll = bpy.data.collections[output_coll_name]
        except KeyError:
            output_coll = None

        return bool(active_shot and output_coll)

    def execute(self, context: bpy.types.Context) -> Set[str]:
        active_shot = cache.shot_active_get()
        output_coll_name = opsdata.get_output_coll_name(active_shot)
        output_coll = bpy.data.collections[output_coll_name]

        # Clear Out Output Collection before Starting
        for collection in output_coll.children:
            output_coll.children.unlink(collection)
        bpy.context.view_layer.update()

        asset_colls = opsdata.find_asset_collections_in_scene(context.scene)
        missing: List[bpy.types.Collection] = []
        output_coll_childs = list(opsdata.traverse_collection_tree(output_coll))

        # Check if all found asset colls are in output coll.
        for coll in asset_colls:
            if coll in output_coll_childs:
                continue
            missing.append(coll)

        # Only take parent colls.
        childs = []
        for i in range(len(missing)):
            coll = missing[i]
            coll_childs = list(opsdata.traverse_collection_tree(coll))
            for j in range(i + 1, len(missing)):
                coll_comp = missing[j]
                if coll_comp in coll_childs:
                    childs.append(coll_comp)

        parents = [coll for coll in missing if coll not in childs]
        for coll in parents:
            output_coll.children.link(coll)
            logger.info("%s linked in %s", coll.name, output_coll.name)

        # Ensure Camera Rig is Linked
        for coll in [col for col in bpy.data.collections]:
            if coll.override_library:
                if (
                    coll.override_library.hierarchy_root.name == "CA-camera_rig"
                ):  # TODO Fix this hack to be generic
                    output_coll.children.link(coll)

        self.report(
            {"INFO"},
            f"Found Asset Collections: {len(asset_colls)} | Added to output collection: {len(parents)}",
        )
        return {"FINISHED"}


# ---------REGISTER ----------.

classes = [
    KITSU_OT_anim_quick_duplicate,
    KITSU_OT_anim_check_action_names,
    KITSU_OT_anim_update_output_coll,
    KITSU_OT_anim_enforce_naming_convention,
    KITSU_OT_unlink_collection_with_string,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
