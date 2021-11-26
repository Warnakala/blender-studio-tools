from typing import Set, Union, Optional, List, Dict, Any

import bpy

from media_viewer.ops import (
    MV_OT_delete_all_gpencil_frames,
    MV_OT_delete_active_gpencil_frame,
    MV_OT_render_review,
)
from media_viewer import ops


def MV_TOPBAR_media_viewer(self: Any, context: bpy.types.Context) -> None:
    layout = self.layout
    gpl = context.active_annotation_layer

    # Only show annotation settings if there is an actual layer
    # which should always be the case, safety.
    # And if filepath_list (represents the selected items in filebrowser)
    # is one or less. We don't support annotating more than one file as
    # annotation layers are linked to one media file, so we also can't support
    # rendering them.
    if gpl and len(ops.prev_filepath_list) <= 1:
        layout.label(text="Annotation")
        layout.prop(gpl, "color", icon_only=True)

        layout.operator(
            MV_OT_delete_active_gpencil_frame.bl_idname, text="", icon="REMOVE"
        )
        layout.operator(MV_OT_delete_all_gpencil_frames.bl_idname, text="", icon="X")

        layout.separator()
        layout.separator()
        layout.separator()
        layout.separator()
        layout.separator()
        layout.separator()
        layout.label(text="Render Review")
        layout.prop(context.window_manager.media_viewer, "review_output_dir", text="")
        layout.operator(
            MV_OT_render_review.bl_idname, icon="RESTRICT_RENDER_OFF", text=""
        )


def MV_TOPBAR_draw_exr_options(self: Any, context: bpy.types.Context) -> None:
    layout = self.layout

    layout.separator()
    layout.separator()
    layout.separator()
    layout.separator()
    layout.separator()
    layout.separator()

    sima = context.space_data
    ima = sima.image
    iuser = sima.image_user

    if ima:
        # draw options.
        layout.prop(sima, "display_channels", icon_only=True)

        # layers.
        layout.template_image_layers(ima, iuser)


# ----------------REGISTER--------------.

classes = []


def register():

    for cls in classes:
        bpy.utils.register_class(cls)

    # Append header draw handler.
    bpy.types.SEQUENCER_HT_header.append(MV_TOPBAR_media_viewer)
    bpy.types.IMAGE_HT_header.append(MV_TOPBAR_media_viewer)
    bpy.types.IMAGE_HT_header.append(MV_TOPBAR_draw_exr_options)


def unregister():

    # Remove header draw handler.
    bpy.types.SEQUENCER_HT_header.remove(MV_TOPBAR_media_viewer)
    bpy.types.IMAGE_HT_header.remove(MV_TOPBAR_media_viewer)
    bpy.types.IMAGE_HT_header.remove(MV_TOPBAR_draw_exr_options)

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
