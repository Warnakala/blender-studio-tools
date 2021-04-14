from typing import Optional

import bpy

from . import cache
from . import checkstrip
from . import props
from . import prefs
from .ops import (
    BLEZOU_OT_assets_load,
    BLEZOU_OT_asset_types_load,
    BLEZOU_OT_productions_load,
    BLEZOU_OT_sequences_load,
    BLEZOU_OT_session_end,
    BLEZOU_OT_session_start,
    BLEZOU_OT_shots_load,
    BLEZOU_OT_sqe_debug_duplicates,
    BLEZOU_OT_sqe_debug_multi_project,
    BLEZOU_OT_sqe_debug_not_linked,
    BLEZOU_OT_sqe_init_strip,
    BLEZOU_OT_sqe_link_sequence,
    BLEZOU_OT_sqe_link_shot,
    BLEZOU_OT_sqe_multi_edit_strip,
    BLEZOU_OT_sqe_pull_shot_meta,
    BLEZOU_OT_sqe_push_del_shot,
    BLEZOU_OT_sqe_push_new_sequence,
    BLEZOU_OT_sqe_push_new_shot,
    BLEZOU_OT_sqe_push_shot_meta,
    BLEZOU_OT_sqe_push_thumbnail,
    BLEZOU_OT_sqe_uninit_strip,
    BLEZOU_OT_sqe_unlink_shot,
)


def get_selshots_noun(nr_of_shots: int, prefix: str = "Active") -> str:
    if not nr_of_shots:
        noun = "All"
    elif nr_of_shots == 1:
        noun = f"{prefix} Shot"
    else:
        noun = "%i Shots" % nr_of_shots
    return noun


class BLEZOU_PT_vi3d_auth(bpy.types.Panel):
    """
    Panel in 3dview that displays email, password and login operator.
    """

    bl_category = "Blezou"
    bl_label = "Login"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_order = 10

    def draw(self, context: bpy.types.Context) -> None:
        addon_prefs = prefs.addon_prefs_get(context)
        zsession = prefs.zsession_get(context)

        layout = self.layout

        row = layout.row(align=True)
        if not zsession.is_auth():
            row.label(text=f"Email: {addon_prefs.email}")
            row = layout.row(align=True)
            row.operator(BLEZOU_OT_session_start.bl_idname, text="Login", icon="PLAY")
        else:
            row.label(text=f"Logged in: {zsession.email}")
            row = layout.row(align=True)
            row.operator(
                BLEZOU_OT_session_end.bl_idname, text="Logout", icon="PANEL_CLOSE"
            )


class BLEZOU_PT_vi3d_context(bpy.types.Panel):
    """
    Panel in 3dview that enables browsing through backend data structure.
    Thought of as a menu to setup a context by selecting active production
    active sequence, shot etc.
    """

    bl_category = "Blezou"
    bl_label = "Context"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {"DEFAULT_CLOSED"}
    bl_order = 20

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return prefs.zsession_auth(context)

    def draw(self, context: bpy.types.Context) -> None:
        addon_prefs = prefs.addon_prefs_get(context)
        layout = self.layout
        category = addon_prefs.category  # can be either 'SHOTS' or 'ASSETS'
        zproject_active = cache.zproject_active_get()
        item_group_data = {
            "name": "Sequence",
            "zobject": cache.zsequence_active_get(),
            "operator": BLEZOU_OT_sequences_load.bl_idname,
        }
        item_data = {
            "name": "Shot",
            "zobject": cache.zshot_active_get(),
            "operator": BLEZOU_OT_shots_load.bl_idname,
        }
        # Production
        layout.row().label(text=f"Production: {zproject_active.name}")

        # Category
        box = layout.box()
        row = box.row(align=True)
        row.prop(addon_prefs, "category", expand=True)

        if not prefs.zsession_auth(context) or not zproject_active:
            row.enabled = False

        # Sequence / AssetType
        if category == "ASSETS":
            item_group_data["name"] = "AssetType"
            item_group_data["zobject"] = cache.zasset_type_active_get()
            item_group_data["operator"] = BLEZOU_OT_asset_types_load.bl_idname

        row = box.row(align=True)
        item_group_text = f"Select {item_group_data['name']}"

        if not zproject_active:
            row.enabled = False

        elif item_group_data["zobject"]:
            item_group_text = item_group_data["zobject"].name
        row.operator(
            item_group_data["operator"], text=item_group_text, icon="DOWNARROW_HLT"
        )

        # Shot / Asset
        if category == "ASSETS":
            item_data["name"] = "Asset"
            item_data["zobject"] = cache.zasset_active_get()
            item_data["operator"] = BLEZOU_OT_assets_load.bl_idname

        row = box.row(align=True)
        item_text = f"Select {item_data['name']}"

        if not zproject_active and item_group_data["zobject"]:
            row.enabled = False

        elif item_data["zobject"]:
            item_text = item_data["zobject"].name

        row.operator(item_data["operator"], text=item_text, icon="DOWNARROW_HLT")


class BLEZOU_PT_sqe_auth(bpy.types.Panel):
    """
    Panel in sequence editor that displays email, password and login operator.
    """

    bl_category = "Blezou"
    bl_label = "Login"
    bl_space_type = "SEQUENCE_EDITOR"
    bl_region_type = "UI"
    bl_order = 10

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return bool(not prefs.zsession_auth(context))

    def draw(self, context: bpy.types.Context) -> None:
        addon_prefs = prefs.addon_prefs_get(context)
        zsession = prefs.zsession_get(context)

        layout = self.layout

        row = layout.row(align=True)
        if not zsession.is_auth():
            row.label(text=f"Email: {addon_prefs.email}")
            row = layout.row(align=True)
            row.operator(BLEZOU_OT_session_start.bl_idname, text="Login", icon="PLAY")
        else:
            row.label(text=f"Logged in: {zsession.email}")
            row = layout.row(align=True)
            row.operator(
                BLEZOU_OT_session_end.bl_idname, text="Logout", icon="PANEL_CLOSE"
            )


class BLEZOU_MT_sqe_advanced_delete(bpy.types.Menu):
    bl_label = "Advanced Delete"

    def draw(self, context: bpy.types.Context) -> None:

        selshots = context.selected_sequences
        strips_to_unlink = [s for s in selshots if s.blezou.linked]

        layout = self.layout
        layout.operator(
            BLEZOU_OT_sqe_push_del_shot.bl_idname,
            text=f"Unlink and Delete {len(strips_to_unlink)} Shots",
            icon="CANCEL",
        )


class BLEZOU_PT_sqe_shot_tools(bpy.types.Panel):
    """
    Panel in sequence editor that shows .blezou properties of active strip. (shot, sequence)
    """

    # TODO: Because each draw function was previously a seperate Panel there might be a lot of
    # code duplication now, needs to be refactored at some point

    bl_category = "Blezou"
    bl_label = "Shot Tools"
    bl_space_type = "SEQUENCE_EDITOR"
    bl_region_type = "UI"
    bl_order = 20

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return bool(prefs.zsession_auth(context) or context.selected_sequences)

    def draw(self, context: bpy.types.Context) -> None:

        if self.poll_setup(context):
            self.draw_setup(context)

        if self.poll_metadata(context):
            self.draw_metadata(context)

        if self.poll_multi_edit(context):
            self.draw_multi_edit(context)

        if self.poll_push(context):
            self.draw_push(context)

        if self.poll_pull(context):
            self.draw_pull(context)

        if self.poll_debug(context):
            self.draw_debug(context)

    @classmethod
    def poll_setup(cls, context: bpy.types.Context) -> bool:
        return bool(context.selected_sequences)

    def draw_setup(self, context: bpy.types.Context) -> None:
        """
        Panel in SQE that shows operators to setup shots. That includes initialization,
        uninitizialization, linking and unlinking.
        """

        strip = context.scene.sequence_editor.active_strip
        selshots = context.selected_sequences
        nr_of_shots = len(selshots)
        noun = get_selshots_noun(nr_of_shots)
        zproject_active = cache.zproject_active_get()

        strips_to_init = []
        strips_to_uninit = []
        strips_to_unlink = []

        for s in selshots:
            if s.type not in checkstrip.VALID_STRIP_TYPES:
                continue
            if not s.blezou.initialized:
                strips_to_init.append(s)
            elif s.blezou.linked:
                strips_to_unlink.append(s)
            elif s.blezou.initialized:
                strips_to_uninit.append(s)

        # create box
        layout = self.layout
        box = layout.box()
        box.label(text="Setup Shots", icon="TOOL_SETTINGS")

        # Production
        if prefs.zsession_auth(context):
            box.row().label(text=f"Production: {zproject_active.name}")

        # Single Selection
        if nr_of_shots == 1:
            row = box.row(align=True)

            # initialize
            if strip.type not in checkstrip.VALID_STRIP_TYPES:
                row.label(
                    text=f"Only sequence strips of types: {checkstrip.VALID_STRIP_TYPES }"
                )
                return

            if not strip.blezou.initialized:
                # init active
                row.operator(
                    BLEZOU_OT_sqe_init_strip.bl_idname, text=f"Init {noun}", icon="ADD"
                )
                # link active
                row.operator(
                    BLEZOU_OT_sqe_link_shot.bl_idname,
                    text=f"Link {noun}",
                    icon="LINKED",
                )

            # unlink
            elif strip.blezou.linked:

                row = box.row(align=True)
                row.operator(
                    BLEZOU_OT_sqe_unlink_shot.bl_idname,
                    text=f"Unlink {noun}",
                    icon="UNLINKED",
                )
                row.menu("BLEZOU_MT_sqe_advanced_delete", icon="DOWNARROW_HLT", text="")

            # uninitialize
            else:
                row = box.row(align=True)
                # unlink active
                row.operator(
                    BLEZOU_OT_sqe_uninit_strip.bl_idname,
                    text=f"Uninitialize {noun}",
                    icon="REMOVE",
                )

        # Multiple Selection
        elif nr_of_shots > 1:
            row = box.row(align=True)

            # init
            if strips_to_init:
                row.operator(
                    BLEZOU_OT_sqe_init_strip.bl_idname,
                    text=f"Init {len(strips_to_init)} Shots",
                    icon="ADD",
                )
            # make row
            if strips_to_uninit or strips_to_unlink:
                row = box.row(align=True)

            # uninitialize
            if strips_to_uninit:
                row.operator(
                    BLEZOU_OT_sqe_uninit_strip.bl_idname,
                    text=f"Uninitialize {len(strips_to_uninit)} Shots",
                    icon="REMOVE",
                )

            # unlink all
            if strips_to_unlink:
                row.operator(
                    BLEZOU_OT_sqe_unlink_shot.bl_idname,
                    text=f"Unlink {len(strips_to_unlink)} Shots",
                    icon="UNLINKED",
                )
                row.menu("BLEZOU_MT_sqe_advanced_delete", icon="DOWNARROW_HLT", text="")

    @classmethod
    def poll_metadata(cls, context: bpy.types.Context) -> bool:
        nr_of_shots = len(context.selected_sequences)
        strip = context.scene.sequence_editor.active_strip
        if nr_of_shots == 1:
            return strip.blezou.initialized
        return False

    def draw_metadata(self, context: bpy.types.Context) -> None:
        """
        Panel in sequence editor that shows .blezou properties of active strip. (shot, sequence)
        """

        strip = context.scene.sequence_editor.active_strip

        # create box
        layout = self.layout
        box = layout.box()
        box.label(text="Metadata", icon="ALIGN_LEFT")

        col = box.column(align=True)

        # sequence
        sub_row = col.row(align=True)
        sub_row.prop(strip.blezou, "sequence_name_display")
        sub_row.operator(
            BLEZOU_OT_sqe_link_sequence.bl_idname, text="", icon="DOWNARROW_HLT"
        )
        sub_row.operator(BLEZOU_OT_sqe_push_new_sequence.bl_idname, text="", icon="ADD")

        # shot
        col.prop(strip.blezou, "shot_name")

        # description
        col.prop(strip.blezou, "shot_description_display", text="Description")
        col.enabled = False if not strip.blezou.initialized else True

    @classmethod
    def poll_multi_edit(cls, context: bpy.types.Context) -> bool:
        sel_shots = context.selected_sequences
        nr_of_shots = len(sel_shots)
        unvalid = [s for s in sel_shots if s.blezou.linked or not s.blezou.initialized]
        return bool(not unvalid and nr_of_shots > 1)

    def draw_multi_edit(self, context: bpy.types.Context) -> None:
        """
        Panel in sequence editor that can edit properties of multiple strips at one.
        Mostly used to quickly initialize lots of shots with an increasing counter.
        """

        addon_prefs = prefs.addon_prefs_get(context)
        nr_of_shots = len(context.selected_sequences)
        noun = get_selshots_noun(nr_of_shots)

        # create box
        layout = self.layout
        box = layout.box()
        box.label(text="Multi Edit", icon="PROPERTIES")

        # Sequence
        # TODO: use link sequence operator instead or sequence_enum ?
        col = box.column()
        sub_row = col.row(align=True)
        # sub_row.prop(context.window_manager, "sequence_name_display")
        sub_row.prop(context.window_manager, "sequence_enum", text="Sequence")
        sub_row.operator(BLEZOU_OT_sqe_push_new_sequence.bl_idname, text="", icon="ADD")

        # Counter
        row = box.row()
        row.prop(
            context.window_manager, "shot_counter_start", text="Shot Counter Start"
        )
        row.prop(context.window_manager, "show_advanced", text="")

        if context.window_manager.show_advanced:

            # Counter
            box.row().prop(
                addon_prefs, "shot_counter_digits", text="Shot Counter Digits"
            )
            box.row().prop(
                addon_prefs, "shot_counter_increment", text="Shot Counter Increment"
            )

            # variables
            row = box.row(align=True)
            row.prop(
                context.window_manager,
                "var_use_custom_seq",
                text="Custom Sequence Variable",
            )
            if context.window_manager.var_use_custom_seq:
                row.prop(context.window_manager, "var_sequence_custom", text="")

            # project
            row = box.row(align=True)
            row.prop(
                context.window_manager,
                "var_use_custom_project",
                text="Custom Project Variable",
            )
            if context.window_manager.var_use_custom_project:
                row.prop(context.window_manager, "var_project_custom", text="")

            # Shot pattern
            box.row().prop(addon_prefs, "shot_pattern", text="Shot Pattern")

        # preview
        row = box.row()
        row.prop(context.window_manager, "shot_preview", text="Preview")

        row = box.row(align=True)
        row.operator(
            BLEZOU_OT_sqe_multi_edit_strip.bl_idname,
            text=f"Edit {noun}",
            icon="TRIA_RIGHT",
        )

    @classmethod
    def poll_push(cls, context: bpy.types.Context) -> bool:
        # if only one strip is selected and it is not init then hide panel
        if not prefs.zsession_auth(context):
            return False

        selshots = context.selected_sequences
        if not selshots:
            selshots = context.scene.sequence_editor.sequences_all

        strips_to_meta = []
        strips_to_tb = []
        strips_to_submit = []

        for s in selshots:
            if s.blezou.linked:
                strips_to_tb.append(s)
                strips_to_meta.append(s)

            elif s.blezou.initialized:
                strips_to_submit.append(s)

        return bool(strips_to_meta or strips_to_tb or strips_to_submit)

    def draw_push(self, context: bpy.types.Context) -> None:
        """
        Panel that shows operator to sync sequence editor metadata with backend.
        """
        nr_of_shots = len(context.selected_sequences)
        layout = self.layout
        strip = context.scene.sequence_editor.active_strip

        selshots = context.selected_sequences
        if not selshots:
            selshots = context.scene.sequence_editor.sequences_all

        strips_to_meta = []
        strips_to_tb = []
        strips_to_submit = []
        strips_to_delete = []

        for s in selshots:
            if s.blezou.linked:
                strips_to_tb.append(s)
                strips_to_meta.append(s)
                strips_to_delete.append(s)

            elif s.blezou.initialized:
                if s.blezou.shot_name and s.blezou.sequence_name:
                    strips_to_submit.append(s)

        # create box
        layout = self.layout
        box = layout.box()
        box.label(text="Push", icon="EXPORT")
        # special case if one shot is selected and it is init but not linked
        # shows the operator but it is not enabled until user types in required metadata
        if nr_of_shots == 1 and not strip.blezou.linked:
            # new operator
            row = box.row()
            col = row.column(align=True)
            col.operator(
                BLEZOU_OT_sqe_push_new_shot.bl_idname,
                text="Submit New Shot",
                icon="ADD",
            )
            return

        # either way no selection one selection but linked or multiple

        # metadata operator
        row = box.row()
        if strips_to_meta:
            col = row.column(align=True)
            noun = get_selshots_noun(
                len(strips_to_meta), prefix=f"{len(strips_to_meta)}"
            )
            col.operator(
                BLEZOU_OT_sqe_push_shot_meta.bl_idname,
                text=f"Metadata {noun}",
                icon="ALIGN_LEFT",
            )

        # thumbnail operator
        if strips_to_tb:
            noun = get_selshots_noun(len(strips_to_tb), prefix=f"{len(strips_to_meta)}")
            col.operator(
                BLEZOU_OT_sqe_push_thumbnail.bl_idname,
                text=f"Thumbnail {noun}",
                icon="IMAGE_DATA",
            )

        # submit operator
        if nr_of_shots > 0:
            if strips_to_submit:
                noun = get_selshots_noun(
                    len(strips_to_submit), prefix=f"{len(strips_to_submit)}"
                )
                row = box.row()
                col = row.column(align=True)
                col.operator(
                    BLEZOU_OT_sqe_push_new_shot.bl_idname,
                    text=f"Submit {noun}",
                    icon="ADD",
                )

    @classmethod
    def poll_pull(cls, context: bpy.types.Context) -> bool:
        # if only one strip is selected and it is not init then hide panel
        if not prefs.zsession_auth(context):
            return False

        selshots = context.selected_sequences
        if not selshots:
            selshots = context.scene.sequence_editor.sequences_all

        strips_to_meta = []

        for s in selshots:
            if s.blezou.linked:
                strips_to_meta.append(s)

        return bool(strips_to_meta)

    def draw_pull(self, context: bpy.types.Context) -> None:
        """
        Panel that shows operator to sync sequence editor metadata with backend.
        """

        selshots = context.selected_sequences
        if not selshots:
            selshots = context.scene.sequence_editor.sequences_all

        strips_to_meta = []

        for s in selshots:
            if s.blezou.linked:
                strips_to_meta.append(s)

        # create box
        layout = self.layout
        box = layout.box()
        box.label(text="Pull", icon="IMPORT")

        layout = self.layout
        if strips_to_meta:
            noun = get_selshots_noun(
                len(strips_to_meta), prefix=f"{len(strips_to_meta)}"
            )
            row = box.row()
            row.operator(
                BLEZOU_OT_sqe_pull_shot_meta.bl_idname,
                text=f"Metadata {noun}",
                icon="ALIGN_LEFT",
            )

    @classmethod
    def poll_debug(cls, context: bpy.types.Context) -> bool:
        return prefs.addon_prefs_get(context).enable_debug

    def draw_debug(self, context: bpy.types.Context) -> None:
        nr_of_shots = len(context.selected_sequences)
        noun = get_selshots_noun(nr_of_shots)

        # create box
        layout = self.layout
        box = layout.box()
        box.label(text="Debug", icon="MODIFIER_ON")

        row = box.row()
        row.operator(
            BLEZOU_OT_sqe_debug_duplicates.bl_idname,
            text=f"Duplicates {noun}",
            icon="MODIFIER_ON",
        )
        row = box.row()
        row.operator(
            BLEZOU_OT_sqe_debug_not_linked.bl_idname,
            text=f"Not Linked {noun}",
            icon="MODIFIER_ON",
        )
        row = box.row()
        row.operator(
            BLEZOU_OT_sqe_debug_multi_project.bl_idname,
            text=f"Multi Projects {noun}",
            icon="MODIFIER_ON",
        )


# ---------REGISTER ----------

classes = [
    BLEZOU_PT_vi3d_auth,
    BLEZOU_PT_sqe_auth,
    BLEZOU_PT_vi3d_context,
    BLEZOU_MT_sqe_advanced_delete,
    BLEZOU_PT_sqe_shot_tools,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
