from typing import Set, Union, Optional, List, Dict, Any

import bpy

from media_viewer.ops import (
    MV_OT_delete_all_gpencil_frames,
    MV_OT_delete_active_gpencil_frame,
    MV_OT_render_review_sqe_editor,
    MV_OT_export_annotation_data_to_3dcam,
    MV_OT_insert_empty_gpencil_frame,
)
from media_viewer import ops

from media_viewer.gpu_ops import MV_OT_render_review_img_editor


def draw_seperators(layout: bpy.types.UILayout) -> None:
    layout.separator()
    layout.separator()
    layout.separator()
    layout.separator()
    layout.separator()
    layout.separator()


def MV_TOPBAR_base(self: Any, context: bpy.types.Context) -> None:
    layout: bpy.types.UILayout = self.layout
    gpl = context.active_annotation_layer

    # Only show annotation settings if there is an actual layer
    # which should always be the case, safety.
    # And if filepath_list (represents the selected items in filebrowser)
    # is one or less. We don't support annotating more than one file as
    # annotation layers are linked to one media file, so we also can't support
    # rendering them.
    if gpl and len(ops.prev_filepath_list) <= 1:
        row = layout.row(align=True)
        row.prop(gpl, "color", icon_only=True)

        row.operator(MV_OT_insert_empty_gpencil_frame.bl_idname, text="", icon="ADD")
        row.operator(
            MV_OT_delete_active_gpencil_frame.bl_idname, text="", icon="REMOVE"
        )
        row.operator(MV_OT_delete_all_gpencil_frames.bl_idname, text="", icon="TRASH")


def MV_TOPBAR_sequencer(self: Any, context: bpy.types.Context) -> None:
    layout: bpy.types.UILayout = self.layout
    row = layout.row(align=True)

    seq_file_type = context.window_manager.media_viewer.sequence_file_type

    # Render review sequence editor operator.
    # Movie
    op = row.operator(
        MV_OT_render_review_sqe_editor.bl_idname, icon="RENDER_ANIMATION", text=""
    )
    op.render_sequence = True
    op.sequence_file_type = seq_file_type

    # Single Image
    op = row.operator(
        MV_OT_render_review_sqe_editor.bl_idname, icon="IMAGE_RGB_ALPHA", text=""
    ).render_sequence = False

    # TODO: Add proper pipeline support before exposing this.
    # Export to 3D Cam
    # row.operator(
    #     MV_OT_export_annotation_data_to_3dcam.bl_idname, icon="EXPORT", text=""
    # )


def MV_TOPBAR_image_editor(self: Any, context: bpy.types.Context) -> None:
    layout: bpy.types.UILayout = self.layout
    row = layout.row(align=True)

    seq_file_type = context.window_manager.media_viewer.sequence_file_type

    # Render review image editor operator.
    # Movie
    op = row.operator(
        MV_OT_render_review_img_editor.bl_idname, icon="RENDER_ANIMATION", text=""
    )
    op.render_sequence = True
    op.sequence_file_type = seq_file_type

    # Single Image.
    row.operator(
        MV_OT_render_review_img_editor.bl_idname,
        icon="IMAGE_RGB_ALPHA",
        text="",
    ).render_sequence = False

    # TODO: Add proper pipeline support before exposing this.
    # Export to 3D Cam
    # row.operator(
    #     MV_OT_export_annotation_data_to_3dcam.bl_idname, icon="EXPORT", text=""
    # )

    sima = context.space_data
    ima = sima.image
    iuser = sima.image_user

    if ima:
        layout.separator_spacer()
        row = layout.row(align=True)
        # draw options.
        row.prop(sima, "display_channels", icon_only=True)

        # layers.
        row.template_image_layers(ima, iuser)


class MV_PT_review_settings(bpy.types.Panel):

    bl_label = "Review Settings"
    bl_space_type = "IMAGE_EDITOR"
    bl_region_type = "HEADER"
    bl_ui_units_x = 12

    def draw(self, context: bpy.types.Context) -> None:
        layout: bpy.types.UILayout = self.layout

        # Review Output dir.
        layout.row().label(text="Output Directory")
        layout.row().prop(
            context.window_manager.media_viewer, "review_output_dir", text=""
        )

        # Sequence File Type.
        layout.row().label(text="Sequence File Type")
        layout.row().prop(
            context.window_manager.media_viewer,
            "sequence_file_type",
            expand=True,
        )


def MV_TOPBAR_settings(self: Any, context: bpy.types.Context) -> None:
    layout: bpy.types.UILayout = self.layout
    layout.separator_spacer()
    layout.popover(panel="MV_PT_review_settings", icon="PREFERENCES", text="")


# ----------------REGISTER--------------.

classes = [MV_PT_review_settings]


def register():

    for cls in classes:
        bpy.utils.register_class(cls)

    # Append header draw handler.
    bpy.types.SEQUENCER_HT_header.append(MV_TOPBAR_base)
    bpy.types.SEQUENCER_HT_header.append(MV_TOPBAR_sequencer)
    bpy.types.SEQUENCER_HT_header.append(MV_TOPBAR_settings)

    bpy.types.IMAGE_HT_header.append(MV_TOPBAR_base)
    bpy.types.IMAGE_HT_header.append(MV_TOPBAR_image_editor)
    bpy.types.IMAGE_HT_header.append(MV_TOPBAR_settings)


def unregister():

    # Remove header draw handler.
    bpy.types.SEQUENCER_HT_header.remove(MV_TOPBAR_base)
    bpy.types.SEQUENCER_HT_header.remove(MV_TOPBAR_sequencer)

    bpy.types.IMAGE_HT_header.remove(MV_TOPBAR_base)
    bpy.types.IMAGE_HT_header.remove(MV_TOPBAR_image_editor)

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
