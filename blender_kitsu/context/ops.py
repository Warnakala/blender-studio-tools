from typing import Set, Any

import bpy

from blender_kitsu import cache, util, prefs
from blender_kitsu.logger import LoggerFactory


logger = LoggerFactory.getLogger(name=__name__)


class KITSU_OT_con_productions_load(bpy.types.Operator):
    """
    Gets all productions that are available in server and let's user select. Invokes a search Popup (enum_prop) on click.
    """

    bl_idname = "kitsu.con_productions_load"
    bl_label = "Productions Load"
    bl_options = {"INTERNAL"}
    bl_property = "enum_prop"

    enum_prop: bpy.props.EnumProperty(items=cache.get_projects_enum_list)  # type: ignore

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return prefs.session_auth(context)

    def execute(self, context: bpy.types.Context) -> Set[str]:
        # store vars to check if project / seq / shot changed
        project_prev_id = cache.project_active_get().id

        # update kitsu metadata
        cache.project_active_set_by_id(context, self.enum_prop)

        # clear active shot when sequence changes
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
    bl_options = {"INTERNAL"}
    bl_property = "enum_prop"

    enum_prop: bpy.props.EnumProperty(items=cache.get_sequences_enum_list)  # type: ignore

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return bool(prefs.session_auth(context) and cache.project_active_get())

    def execute(self, context: bpy.types.Context) -> Set[str]:

        # store vars to check if project / seq / shot changed
        zseq_prev_id = cache.sequence_active_get().id

        # update kitsu metadata
        cache.sequence_active_set_by_id(context, self.enum_prop)

        # clear active shot when sequence changes
        if self.enum_prop != zseq_prev_id:
            cache.shot_active_reset(context)

        util.ui_redraw()
        return {"FINISHED"}

    def invoke(self, context, event):
        context.window_manager.invoke_search_popup(self)
        return {"FINISHED"}


class KITSU_OT_con_shots_load(bpy.types.Operator):
    """
    Gets all sequences that are available in server for active production and let's user select. Invokes a search Popup (enum_prop) on click.
    """

    bl_idname = "kitsu.con_shots_load"
    bl_label = "Shots Load"
    bl_options = {"INTERNAL"}
    bl_property = "enum_prop"

    enum_prop: bpy.props.EnumProperty(items=cache.get_shots_enum_for_active_seq)  # type: ignore

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        # only if session is auth active_project and active sequence selected
        return bool(
            prefs.session_auth(context)
            and cache.sequence_active_get()
            and cache.project_active_get()
        )

    def execute(self, context: bpy.types.Context) -> Set[str]:
        # update kitsu metadata
        if self.enum_prop:
            cache.shot_active_set_by_id(context, self.enum_prop)
        util.ui_redraw()
        return {"FINISHED"}

    def invoke(self, context, event):
        context.window_manager.invoke_search_popup(self)
        return {"FINISHED"}


class KITSU_OT_con_asset_types_load(bpy.types.Operator):
    """
    Gets all sequences that are available in server for active production and let's user select. Invokes a search Popup (enum_prop) on click.
    """

    bl_idname = "kitsu.con_asset_types_load"
    bl_label = "Asset Types Load"
    bl_options = {"INTERNAL"}
    bl_property = "enum_prop"

    enum_prop: bpy.props.EnumProperty(items=cache.get_assetypes_enum_list)  # type: ignore

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return bool(prefs.session_auth(context) and cache.project_active_get())

    def execute(self, context: bpy.types.Context) -> Set[str]:
        # store vars to check if project / seq / shot changed
        asset_type_prev_id = cache.asset_type_active_get().id

        # update kitsu metadata
        cache.asset_type_active_set_by_id(context, self.enum_prop)

        # clear active shot when sequence changes
        if self.enum_prop != asset_type_prev_id:
            cache.asset_active_reset(context)

        util.ui_redraw()
        return {"FINISHED"}

    def invoke(self, context, event):
        context.window_manager.invoke_search_popup(self)
        return {"FINISHED"}


class KITSU_OT_con_assets_load(bpy.types.Operator):
    """
    Gets all sequences that are available in server for active production and let's user select. Invokes a search Popup (enum_prop) on click.
    """

    bl_idname = "kitsu.con_assets_load"
    bl_label = "Assets Load"
    bl_options = {"INTERNAL"}
    bl_property = "enum_prop"

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

        # update kitsu metadata
        cache.asset_active_set_by_id(context, self.enum_prop)
        util.ui_redraw()
        return {"FINISHED"}

    def invoke(self, context, event):
        context.window_manager.invoke_search_popup(self)
        return {"FINISHED"}


class KITSU_OT_con_task_types_load(bpy.types.Operator):
    """
    Gets all sequences that are available in server for active production and let's user select. Invokes a search Popup (enum_prop) on click.
    """

    bl_idname = "kitsu.con_task_types_load"
    bl_label = "Task Types Load"
    bl_options = {"INTERNAL"}
    bl_property = "enum_prop"

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
        # store vars to check if project / seq / shot changed
        asset_task_type_id = cache.task_type_active_get().id

        # update kitsu metadata
        cache.task_type_active_set_by_id(context, self.enum_prop)

        util.ui_redraw()
        return {"FINISHED"}

    def invoke(self, context, event):
        context.window_manager.invoke_search_popup(self)
        return {"FINISHED"}


# ---------REGISTER ----------

classes = [
    KITSU_OT_con_productions_load,
    KITSU_OT_con_sequences_load,
    KITSU_OT_con_shots_load,
    KITSU_OT_con_asset_types_load,
    KITSU_OT_con_assets_load,
    KITSU_OT_con_task_types_load,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
