import bpy
from typing import Optional
from .util import *
from . import props

from .ops import (
    BZ_OT_SessionStart,
    BZ_OT_SessionEnd,
    BZ_OT_ProductionsLoad,
    BZ_OT_SequencesLoad,
    BZ_OT_ShotsLoad,
    BZ_OT_AssetsLoad,
    BZ_OT_AssetTypesLoad,
    BZ_OT_SQE_PushThumbnail,
    BZ_OT_SQE_InitShot,
    BZ_OT_SQE_DelShotMeta,
    BZ_OT_SQE_LinkShot,
    BZ_OT_SQE_LinkSequence,
    BZ_OT_SQE_PushNewShot,
    BZ_OT_SQE_PushDeleteShot,
    BZ_OT_SQE_PushShotMeta,
    BZ_OT_SQE_PullShotMeta,
    BZ_OT_SQE_MultiEditStrip,
    BZ_OT_SQE_DebugDuplicates,
    BZ_OT_SQE_DebugNotLinked,
    BZ_OT_SQE_DebugMultiProjects,
)


def get_selshots_noun(nr_of_shots: int, prefix: str = "Active") -> str:
    if not nr_of_shots:
        noun = "All"
    elif nr_of_shots == 1:
        noun = f"{prefix} Shot"
    else:
        noun = "%i Shots" % nr_of_shots
    return noun


class BZ_PT_vi3d_auth(bpy.types.Panel):
    """
    Panel in 3dview that displays email, password and login operator.
    """

    bl_category = "Blezou"
    bl_label = "Login"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_order = 10

    def draw(self, context: bpy.types.Context) -> None:
        prefs = addon_prefs_get(context)
        zsession = zsession_get(context)

        layout = self.layout

        row = layout.row(align=True)
        if not zsession.is_auth():
            row.label(text=f"Email: {prefs.email}")
            row = layout.row(align=True)
            row.operator(BZ_OT_SessionStart.bl_idname, text="Login", icon="PLAY")
        else:
            row.label(text=f"Logged in: {zsession.email}")
            row = layout.row(align=True)
            row.operator(BZ_OT_SessionEnd.bl_idname, text="Logout", icon="PANEL_CLOSE")


class BZ_PT_vi3d_context(bpy.types.Panel):
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
        return zsession_auth(context)

    def draw(self, context: bpy.types.Context) -> None:
        prefs = addon_prefs_get(context)
        layout = self.layout
        category = prefs.category  # can be either 'SHOTS' or 'ASSETS'
        zproject_active = zproject_active_get()
        item_group_data = {
            "name": "Sequence",
            "zobject": zsequence_active_get(),
            "operator": BZ_OT_SequencesLoad.bl_idname,
        }
        item_data = {
            "name": "Shot",
            "zobject": zshot_active_get(),
            "operator": BZ_OT_ShotsLoad.bl_idname,
        }
        # Production
        layout.row().label(text=f"Production: {zproject_active.name}")

        # Category
        box = layout.box()
        row = box.row(align=True)
        row.prop(prefs, "category", expand=True)

        if not zsession_auth(context) or not zproject_active:
            row.enabled = False

        # Sequence / AssetType
        if category == "ASSETS":
            item_group_data["name"] = "AssetType"
            item_group_data["zobject"] = zasset_type_active_get()
            item_group_data["operator"] = BZ_OT_AssetTypesLoad.bl_idname

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
            item_data["zobject"] = zasset_active_get()
            item_data["operator"] = BZ_OT_AssetsLoad.bl_idname

        row = box.row(align=True)
        item_text = f"Select {item_data['name']}"

        if not zproject_active and item_group_data["zobject"]:
            row.enabled = False

        elif item_data["zobject"]:
            item_text = item_data["zobject"].name

        row.operator(item_data["operator"], text=item_text, icon="DOWNARROW_HLT")


class BZ_PT_SQE_auth(bpy.types.Panel):
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
        return bool(not zsession_auth(context))

    def draw(self, context: bpy.types.Context) -> None:
        prefs = addon_prefs_get(context)
        zsession = zsession_get(context)

        layout = self.layout

        row = layout.row(align=True)
        if not zsession.is_auth():
            row.label(text=f"Email: {prefs.email}")
            row = layout.row(align=True)
            row.operator(BZ_OT_SessionStart.bl_idname, text="Login", icon="PLAY")
        else:
            row.label(text=f"Logged in: {zsession.email}")
            row = layout.row(align=True)
            row.operator(BZ_OT_SessionEnd.bl_idname, text="Logout", icon="PANEL_CLOSE")


class BZ_PT_SQE_tools(bpy.types.Panel):
    """
    Panel in sequence editor that shows .blezou properties of active strip. (shot, sequence)
    """

    bl_idname = "BZ_PT_SQE_tools"
    bl_category = "Blezou"
    bl_label = "Shot Tools"
    bl_space_type = "SEQUENCE_EDITOR"
    bl_region_type = "UI"
    bl_order = 30

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return True

    def draw(self, context: bpy.types.Context) -> None:

        strip = context.scene.sequence_editor.active_strip
        selshots = context.selected_sequences
        nr_of_shots = len(selshots)
        noun = get_selshots_noun(nr_of_shots)
        zproject_active = zproject_active_get()

        strips_to_init = []
        strips_to_uninit = []
        strips_to_unlink = []

        for s in selshots:
            if not s.blezou.initialized:
                strips_to_init.append(s)
            elif s.blezou.linked:
                strips_to_unlink.append(s)
            elif s.blezou.initialized:
                strips_to_uninit.append(s)

        layout = self.layout

        # Production
        if zsession_auth(context):
            layout.row().label(text=f"Production: {zproject_active.name}")

        # Single Selection
        if nr_of_shots == 1:
            row = layout.row(align=True)

            if not strip.blezou.initialized:
                # init active
                row.operator(
                    BZ_OT_SQE_InitShot.bl_idname, text=f"Init {noun}", icon="ADD"
                )
                # link active
                row.operator(
                    BZ_OT_SQE_LinkShot.bl_idname,
                    text=f"Link {noun}",
                    icon="LINKED",
                )

            else:
                noun_unlink = "Unlink"
                icon_unlink = "UNLINKED"
                if not strip.blezou.linked:
                    noun_unlink = "Uninitialize"
                    icon_unlink = "REMOVE"

                row = layout.row(align=True)
                # unlink active
                row.operator(
                    BZ_OT_SQE_DelShotMeta.bl_idname,
                    text=f"{noun_unlink} {noun}",
                    icon=icon_unlink,
                )
                if strip.blezou.linked:
                    row.prop(context.window_manager, "advanced_delete", text="")

                    if context.window_manager.advanced_delete:
                        row = layout.row(align=True)
                        row.operator(
                            BZ_OT_SQE_PushDeleteShot.bl_idname,
                            text=f"Unlink and Delete Active Shot",
                            icon="REMOVE",
                        )

        # Multiple Selection
        elif nr_of_shots > 1:
            row = layout.row(align=True)

            # init
            if len(strips_to_init):
                row.operator(
                    BZ_OT_SQE_InitShot.bl_idname,
                    text=f"Init {len(strips_to_init)} Shots",
                    icon="ADD",
                )
            # unlink all
            if len(strips_to_unlink):
                row = layout.row(align=True)
                row.operator(
                    BZ_OT_SQE_DelShotMeta.bl_idname,
                    text=f"Unlink {len(strips_to_unlink)} Shots",
                    icon="UNLINKED",
                )
                row.prop(context.window_manager, "advanced_delete", text="")

                if context.window_manager.advanced_delete:
                    row = layout.row(align=True)
                    row.operator(
                        BZ_OT_SQE_PushDeleteShot.bl_idname,
                        text=f"Unlink and Delete {len(strips_to_unlink)} Shots",
                        icon="REMOVE",
                    )


class BZ_PT_SQE_shot_meta(bpy.types.Panel):
    """
    Panel in sequence editor that shows .blezou properties of active strip. (shot, sequence)
    """

    bl_parent_id = "BZ_PT_SQE_tools"
    bl_category = "Blezou"
    bl_label = "Metadata"
    bl_space_type = "SEQUENCE_EDITOR"
    bl_region_type = "UI"
    bl_order = 10

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        nr_of_shots = len(context.selected_sequences)
        strip = context.scene.sequence_editor.active_strip
        if nr_of_shots == 1:
            return strip.blezou.initialized
        return False

    def draw(self, context: bpy.types.Context) -> None:

        strip = context.scene.sequence_editor.active_strip
        layout = self.layout
        box = layout.box()
        col = box.column(align=True)

        # sequence
        sub_row = col.row(align=True)
        sub_row.prop(strip.blezou, "sequence_name")
        sub_row.operator(BZ_OT_SQE_LinkSequence.bl_idname, text="", icon="LINKED")

        # shot
        col.prop(strip.blezou, "shot_name")

        # description
        col.prop(strip.blezou, "shot_description")
        col.enabled = False if not strip.blezou.initialized else True


class BZ_PT_SQE_ShotMultiEdit(bpy.types.Panel):
    """
    Panel in sequence editor that shows .blezou properties of active strip. (shot, sequence)
    """

    bl_parent_id = "BZ_PT_SQE_tools"
    bl_category = "Blezou"
    bl_label = "Multi Edit"
    bl_space_type = "SEQUENCE_EDITOR"
    bl_region_type = "UI"
    bl_order = 11

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        sel_shots = context.selected_sequences
        nr_of_shots = len(sel_shots)
        unvalid = [s for s in sel_shots if s.blezou.linked or not s.blezou.initialized]
        return bool(not unvalid and nr_of_shots > 1)

    def draw(self, context: bpy.types.Context) -> None:
        addon_prefs = addon_prefs_get(context)
        nr_of_shots = len(context.selected_sequences)
        noun = get_selshots_noun(nr_of_shots)

        # UI
        layout = self.layout

        # Sequence
        row = layout.row()
        box = row.box()
        row = box.row(align=True)
        row.prop(context.window_manager, "use_sequence_new", text="New Seqeunce")
        if context.window_manager.use_sequence_new:
            row.prop(context.window_manager, "sequence_new", text="")
        else:
            row.prop(context.window_manager, "sequence_enum", text="")

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

        row = layout.row()
        row.operator(
            BZ_OT_SQE_MultiEditStrip.bl_idname,
            text=f"Edit {noun}",
            icon="TRIA_RIGHT",
        )


class BZ_PT_SQE_push(bpy.types.Panel):
    """
    Panel that shows operator to sync sequence editor metadata with backend.
    """

    bl_parent_id = "BZ_PT_SQE_tools"
    bl_category = "Blezou"
    bl_label = "Push"
    bl_space_type = "SEQUENCE_EDITOR"
    bl_region_type = "UI"
    bl_order = 20

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        # if only one strip is selected and it is not init then hide panel
        if not zsession_auth(context):
            return False
        nr_of_shots = len(context.selected_sequences)
        strip = context.scene.sequence_editor.active_strip
        if nr_of_shots == 1:
            return strip.blezou.initialized

        return True

    def draw(self, context: bpy.types.Context) -> None:
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
                strips_to_submit.append(s)

        # special case if one shot is selected and it is init but not linked
        # shows the operator but it is not enabled until user types in required metadata
        if nr_of_shots == 1 and not strip.blezou.linked:
            # new operator
            row = layout.row()
            col = row.column(align=True)
            col.operator(
                BZ_OT_SQE_PushNewShot.bl_idname,
                text="Submit New Shot",
                icon="ADD",
            )
            return

        # either way no selection one selection but linked or multiple

        # metadata operator
        row = layout.row()
        if len(strips_to_meta):
            col = row.column(align=True)
            noun = get_selshots_noun(
                len(strips_to_meta), prefix=f"{len(strips_to_meta)}"
            )
            col.operator(
                BZ_OT_SQE_PushShotMeta.bl_idname,
                text=f"Metadata {noun}",
                icon="ALIGN_LEFT",
            )

        # thumbnail operator
        if len(strips_to_tb):
            noun = get_selshots_noun(len(strips_to_tb), prefix=f"{len(strips_to_meta)}")
            col.operator(
                BZ_OT_SQE_PushThumbnail.bl_idname,
                text=f"Thumbnail {noun}",
                icon="IMAGE_DATA",
            )

        # submit operator
        if nr_of_shots > 0:
            if len(strips_to_submit):
                noun = get_selshots_noun(
                    len(strips_to_submit), prefix=f"{len(strips_to_meta)}"
                )
                row = layout.row()
                col = row.column(align=True)
                col.operator(
                    BZ_OT_SQE_PushNewShot.bl_idname,
                    text=f"Submit {noun}",
                    icon="ADD",
                )


class BZ_PT_SQE_pull(bpy.types.Panel):
    """
    Panel that shows operator to sync sequence editor metadata with backend.
    """

    bl_parent_id = "BZ_PT_SQE_tools"
    bl_category = "Blezou"
    bl_label = "Pull"
    bl_space_type = "SEQUENCE_EDITOR"
    bl_region_type = "UI"
    bl_order = 30

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        # if only one strip is selected and it is not init then hide panel
        if not zsession_auth(context):
            return False

        nr_of_shots = len(context.selected_sequences)
        strip = context.scene.sequence_editor.active_strip
        if nr_of_shots == 1:
            return strip.blezou.linked
        return True

    def draw(self, context: bpy.types.Context) -> None:
        selshots = context.selected_sequences

        if not selshots:
            selshots = context.scene.sequence_editor.sequences_all

        strips_to_meta = []

        for s in selshots:
            if s.blezou.linked:
                strips_to_meta.append(s)

        layout = self.layout
        if len(strips_to_meta):
            noun = get_selshots_noun(
                len(strips_to_meta), prefix=f"{len(strips_to_meta)}"
            )
            row = layout.row()
            row.operator(
                BZ_OT_SQE_PullShotMeta.bl_idname,
                text=f"Metadata {noun}",
                icon="ALIGN_LEFT",
            )


class BZ_PT_SQE_debug(bpy.types.Panel):
    """
    Panel that shows operator to open a debug ui
    """

    bl_parent_id = "BZ_PT_SQE_tools"
    bl_category = "Blezou"
    bl_label = "Debug"
    bl_space_type = "SEQUENCE_EDITOR"
    bl_region_type = "UI"
    bl_options = {"DEFAULT_CLOSED"}
    bl_order = 40

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return addon_prefs_get(context).enable_debug

    def draw(self, context: bpy.types.Context) -> None:
        nr_of_shots = len(context.selected_sequences)
        noun = get_selshots_noun(nr_of_shots)

        layout = self.layout
        row = layout.row()
        row.operator(
            BZ_OT_SQE_DebugDuplicates.bl_idname,
            text=f"Duplicates {noun}",
            icon="MODIFIER_ON",
        )
        row = layout.row()
        row.operator(
            BZ_OT_SQE_DebugNotLinked.bl_idname,
            text=f"Not Linked {noun}",
            icon="MODIFIER_ON",
        )
        row = layout.row()
        row.operator(
            BZ_OT_SQE_DebugMultiProjects.bl_idname,
            text=f"Multi Projects {noun}",
            icon="MODIFIER_ON",
        )


# ---------REGISTER ----------

classes = [
    BZ_PT_vi3d_auth,
    BZ_PT_SQE_auth,
    BZ_PT_vi3d_context,
    BZ_PT_SQE_tools,
    BZ_PT_SQE_shot_meta,
    BZ_PT_SQE_ShotMultiEdit,
    BZ_PT_SQE_push,
    BZ_PT_SQE_pull,
    BZ_PT_SQE_debug,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
