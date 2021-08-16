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

from typing import Dict, Optional, Set, Any
from pathlib import Path

import bpy

from blender_kitsu import bkglobals, cache, util, prefs
from blender_kitsu.logger import LoggerFactory
from blender_kitsu.types import TaskType, AssetType

logger = LoggerFactory.getLogger(name=__name__)


class KITSU_OT_con_productions_load(bpy.types.Operator):
    """
    Gets all productions that are available in server and let's user select. Invokes a search Popup (enum_prop) on click.
    """

    bl_idname = "kitsu.con_productions_load"
    bl_label = "Productions Load"
    bl_property = "enum_prop"
    bl_description = "Sets active project"

    enum_prop: bpy.props.EnumProperty(items=cache.get_projects_enum_list)  # type: ignore

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return prefs.session_auth(context)

    def execute(self, context: bpy.types.Context) -> Set[str]:
        # Store vars to check if project / seq / shot changed.
        project_prev_id = cache.project_active_get().id

        # Update kitsu metadata.
        cache.project_active_set_by_id(context, self.enum_prop)

        # Clear active shot when sequence changes.
        if self.enum_prop != project_prev_id:
            cache.sequence_active_reset(context)
            cache.asset_type_active_reset(context)
            cache.shot_active_reset(context)
            cache.asset_active_reset(context)

        util.ui_redraw()
        return {"FINISHED"}

    def invoke(self, context, event):
        context.window_manager.invoke_search_popup(self)
        return {"FINISHED"}


class KITSU_OT_con_sequences_load(bpy.types.Operator):
    """
    Gets all sequences that are available in server for active production and let's user select. Invokes a search Popup (enum_prop) on click.
    """

    bl_idname = "kitsu.con_sequences_load"
    bl_label = "Sequences Load"
    bl_property = "enum_prop"
    bl_description = "Sets active sequence for this scene"

    enum_prop: bpy.props.EnumProperty(items=cache.get_sequences_enum_list)  # type: ignore

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return bool(prefs.session_auth(context) and cache.project_active_get())

    def execute(self, context: bpy.types.Context) -> Set[str]:

        # Store vars to check if project / seq / shot changed.
        zseq_prev_id = cache.sequence_active_get().id

        # Update kitsu metadata.
        cache.sequence_active_set_by_id(context, self.enum_prop)

        # Clear active shot when sequence changes.
        if self.enum_prop != zseq_prev_id:
            cache.shot_active_reset(context)

        util.ui_redraw()
        return {"FINISHED"}

    def invoke(self, context, event):
        context.window_manager.invoke_search_popup(self)
        return {"FINISHED"}


class KITSU_OT_con_shots_load(bpy.types.Operator):
    """
    Gets all shots that are available in server for active production and let's user select. Invokes a search Popup (enum_prop) on click.
    """

    bl_idname = "kitsu.con_shots_load"
    bl_label = "Shots Load"
    bl_property = "enum_prop"
    bl_description = "Sets active shot for this scene"

    enum_prop: bpy.props.EnumProperty(items=cache.get_shots_enum_for_active_seq)  # type: ignore

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        # Only if session is auth active_project and active sequence selected.
        return bool(
            prefs.session_auth(context)
            and cache.sequence_active_get()
            and cache.project_active_get()
        )

    def execute(self, context: bpy.types.Context) -> Set[str]:
        # Update kitsu metadata.
        if self.enum_prop:
            cache.shot_active_set_by_id(context, self.enum_prop)
        util.ui_redraw()
        return {"FINISHED"}

    def invoke(self, context, event):
        context.window_manager.invoke_search_popup(self)
        return {"FINISHED"}


class KITSU_OT_con_asset_types_load(bpy.types.Operator):
    """
    Gets all asset_types that are available in server and let's user select. Invokes a search Popup (enum_prop) on click.
    """

    bl_idname = "kitsu.con_asset_types_load"
    bl_label = "Asset Types Load"
    bl_property = "enum_prop"
    bl_description = "Sets active asset type for this scene"

    enum_prop: bpy.props.EnumProperty(items=cache.get_assetypes_enum_list)  # type: ignore

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return bool(prefs.session_auth(context) and cache.project_active_get())

    def execute(self, context: bpy.types.Context) -> Set[str]:
        # Store vars to check if project / seq / shot changed.
        asset_type_prev_id = cache.asset_type_active_get().id

        # Update kitsu metadata.
        cache.asset_type_active_set_by_id(context, self.enum_prop)

        # Clear active shot when sequence changes.
        if self.enum_prop != asset_type_prev_id:
            cache.asset_active_reset(context)

        util.ui_redraw()
        return {"FINISHED"}

    def invoke(self, context, event):
        context.window_manager.invoke_search_popup(self)
        return {"FINISHED"}


class KITSU_OT_con_assets_load(bpy.types.Operator):
    """
    Gets all assets that are available on server for active production and let's user select. Invokes a search Popup (enum_prop) on click.
    """

    bl_idname = "kitsu.con_assets_load"
    bl_label = "Assets Load"
    bl_property = "enum_prop"
    bl_description = "Sets active asset for this scene"

    enum_prop: bpy.props.EnumProperty(items=cache.get_assets_enum_for_active_asset_type)  # type: ignore

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return bool(
            prefs.session_auth(context)
            and cache.project_active_get()
            and cache.asset_type_active_get()
        )

    def execute(self, context: bpy.types.Context) -> Set[str]:
        if not self.enum_prop:
            return {"CANCELLED"}

        # Update kitsu metadata.
        cache.asset_active_set_by_id(context, self.enum_prop)
        util.ui_redraw()
        return {"FINISHED"}

    def invoke(self, context, event):
        context.window_manager.invoke_search_popup(self)
        return {"FINISHED"}


class KITSU_OT_con_task_types_load(bpy.types.Operator):
    """
    Gets all task types that are available on server for active asset/shot and let's user select. Invokes a search Popup (enum_prop) on click.
    """

    bl_idname = "kitsu.con_task_types_load"
    bl_label = "Task Types Load"
    bl_property = "enum_prop"
    bl_description = "Sets active task type for this scene"

    enum_prop: bpy.props.EnumProperty(items=cache.get_task_types_enum_for_current_context)  # type: ignore

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        addon_prefs = prefs.addon_prefs_get(context)
        precon = bool(prefs.session_auth(context) and cache.project_active_get())

        if context.scene.kitsu.category == "SHOTS":
            return bool(
                precon and cache.sequence_active_get() and cache.shot_active_get()
            )

        if context.scene.kitsu.category == "ASSETS":
            return bool(
                precon and cache.asset_type_active_get() and cache.asset_active_get()
            )

        return False

    def execute(self, context: bpy.types.Context) -> Set[str]:
        # Store vars to check if project / seq / shot changed.
        asset_task_type_id = cache.task_type_active_get().id

        # Update kitsu metadata.
        cache.task_type_active_set_by_id(context, self.enum_prop)

        util.ui_redraw()
        return {"FINISHED"}

    def invoke(self, context, event):
        context.window_manager.invoke_search_popup(self)
        return {"FINISHED"}


class KITSU_OT_con_detect_context(bpy.types.Operator):
    bl_idname = "kitsu.con_detect_context"
    bl_label = "Detect Context"
    bl_description = "Auto detects context by looking at file path"

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return bool(
            prefs.session_auth(context)
            and cache.project_active_get()
            and bpy.data.filepath
        )

    def execute(self, context: bpy.types.Context) -> Set[str]:
        # Update kitsu metadata.
        filepath = Path(bpy.data.filepath)
        active_project = cache.project_active_get()
        category = filepath.parents[2].name
        item_group = filepath.parents[1].name
        item = filepath.parents[0].name
        item_task_type = filepath.stem.split(".")[-1]

        if category == bkglobals.SHOT_DIR_NAME:
            # TODO: check if frame range update gets triggered.

            # Set category.
            context.scene.kitsu.category = "SHOTS"

            # Detect ad load seqeunce.
            sequence = active_project.get_sequence_by_name(item_group)
            if not sequence:
                self.report(
                    {"ERROR"}, f"Failed to find sequence: '{item_group}' on server"
                )
                return {"CANCELLED"}

            bpy.ops.kitsu.con_sequences_load(enum_prop=sequence.id)

            # Detect and load shot.
            shot = active_project.get_shot_by_name(sequence, item)
            if not shot:
                self.report({"ERROR"}, f"Failed to find shot: '{item}' on server")
                return {"CANCELLED"}

            bpy.ops.kitsu.con_shots_load(enum_prop=shot.id)

            # Detect and load shot task type.
            kitsu_task_type_name = self._find_in_mapping(
                item_task_type, bkglobals.SHOT_TASK_MAPPING, "shot task type"
            )
            if not kitsu_task_type_name:
                return {"CANCELLED"}

            task_type = TaskType.by_name(kitsu_task_type_name)
            if not task_type:
                self.report(
                    {"ERROR"},
                    f"Failed to find task type: '{kitsu_task_type_name}' on server",
                )
                return {"CANCELLED"}

            bpy.ops.kitsu.con_task_types_load(enum_prop=task_type.id)

        elif category == bkglobals.ASSET_DIR_NAME:

            # Set category.
            context.scene.kitsu.category = "ASSETS"

            # Detect and load asset type.
            kitsu_asset_type_name = self._find_in_mapping(
                item_group, bkglobals.ASSET_TYPE_MAPPING, "asset type"
            )
            if not kitsu_asset_type_name:
                return {"CANCELLED"}

            asset_type = AssetType.by_name(kitsu_asset_type_name)
            if not asset_type:
                self.report(
                    {"ERROR"},
                    f"Failed to find asset type: '{kitsu_asset_type_name}' on server",
                )
                return {"CANCELLED"}

            bpy.ops.kitsu.con_asset_types_load(enum_prop=asset_type.id)

            # Detect and load asset.
            asset = active_project.get_asset_by_name(item)
            if not asset:
                self.report({"ERROR"}, f"Failed to find asset: '{item}' on server")
                return {"CANCELLED"}

            bpy.ops.kitsu.con_assets_load(enum_prop=asset.id)

            # Detect and load asset task_type.
            kitsu_task_type_name = self._find_in_mapping(
                item_task_type, bkglobals.ASSET_TASK_MAPPING, "task type"
            )
            if not kitsu_task_type_name:
                return {"CANCELLED"}

            task_type = TaskType.by_name(kitsu_task_type_name)
            if not task_type:
                self.report(
                    {"ERROR"},
                    f"Failed to find task type: '{kitsu_task_type_name}' on server",
                )
                return {"CANCELLED"}

            bpy.ops.kitsu.con_task_types_load(enum_prop=task_type.id)

        else:
            self.report(
                {"ERROR"},
                (
                    f"Expected '{bkglobals.SHOT_DIR_NAME}' or '{bkglobals.ASSET_DIR_NAME}' 3 folders up. "
                    f"Got: '{filepath.parents[2].as_posix()}' instead. "
                    "Blend file might not be saved in project structure"
                ),
            )
            return {"CANCELLED"}

        util.ui_redraw()
        return {"FINISHED"}

    def _find_in_mapping(
        self, key: str, mapping: Dict[str, str], entity_type: str
    ) -> Optional[str]:
        if not key in mapping:
            self.report(
                {"ERROR"},
                f"Failed to find {entity_type}: '{key}' in {entity_type} remapping",
            )
            return None
        return mapping[key]


# ---------REGISTER ----------.

classes = [
    KITSU_OT_con_productions_load,
    KITSU_OT_con_sequences_load,
    KITSU_OT_con_shots_load,
    KITSU_OT_con_asset_types_load,
    KITSU_OT_con_assets_load,
    KITSU_OT_con_task_types_load,
    KITSU_OT_con_detect_context,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
