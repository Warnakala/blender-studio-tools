from typing import Set, Union, Optional, List, Dict, Any

import bpy

from media_viewer.ops import (
    MV_OT_delete_all_gpencil_frames,
    MV_OT_delete_active_gpencil_frame,
)


def MV_TOPBAR_media_viewer(self: Any, context: bpy.types.Context) -> None:
    layout = self.layout
    gpl = context.active_annotation_layer
    if gpl:
        layout.label(text="Annotation")
        layout.prop(gpl, "color", text="")

        layout.operator(
            MV_OT_delete_active_gpencil_frame.bl_idname, text="", icon="REMOVE"
        )
        layout.operator(MV_OT_delete_all_gpencil_frames.bl_idname, text="", icon="X")


# ----------------REGISTER--------------.

classes = []


def register():

    for cls in classes:
        bpy.utils.register_class(cls)

    # Append header draw handler.
    bpy.types.SEQUENCER_HT_header.append(MV_TOPBAR_media_viewer)
    bpy.types.IMAGE_HT_header.append(MV_TOPBAR_media_viewer)


def unregister():

    # Remove header draw handler.
    bpy.types.SEQUENCER_HT_header.remove(MV_TOPBAR_media_viewer)
    bpy.types.IMAGE_HT_header.remove(MV_TOPBAR_media_viewer)

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
