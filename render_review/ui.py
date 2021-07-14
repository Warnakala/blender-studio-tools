from pathlib import Path

from typing import Set, Union, Optional, List, Dict, Any

import bpy

from render_review.ops import (
    RR_OT_sqe_create_review_session,
    RR_OT_setup_review_workspace,
    RR_OT_sqe_inspect_exr_sequence,
    RR_OT_sqe_clear_exr_inspect,
    RR_OT_sqe_approve_render,
    RR_OT_sqe_update_is_approved,
    RR_OT_open_path,
    RR_OT_sqe_push_to_edit,
    RR_OT_make_contactsheet,
    RR_OT_exit_contactsheet,
)
from render_review import opsdata


class RR_PT_render_review(bpy.types.Panel):
    """ """

    bl_category = "Render Review"
    bl_label = "Render Review"
    bl_space_type = "SEQUENCE_EDITOR"
    bl_region_type = "UI"
    bl_order = 10

    def draw(self, context: bpy.types.Context) -> None:

        # handle special case if scene is contactsheet
        if context.scene.rr.is_contactsheet:
            layout = self.layout
            box = layout.box()
            box.label(text="Contactsheet", icon="MESH_GRID")

            # exti contact sheet
            row = box.row(align=True)
            row.operator(RR_OT_exit_contactsheet.bl_idname, icon="X")
            return

        active_strip = context.scene.sequence_editor.active_strip

        # create box
        layout = self.layout
        box = layout.box()

        # label and setup workspace
        row = box.row(align=True)
        row.label(text="Review", icon="CAMERA_DATA")
        row.operator(RR_OT_setup_review_workspace.bl_idname, text="", icon="WINDOW")

        # render dir prop
        row = box.row(align=True)
        row.prop(context.scene.rr, "render_dir")

        # create session
        render_dir = context.scene.rr.render_dir_path
        text = f"Invalid Render Directory"
        if render_dir:
            if opsdata.is_sequence_dir(render_dir):
                text = f"Review Sequence: {render_dir.name}"
            elif opsdata.is_shot_dir(render_dir):
                text = f"Review Shot: {render_dir.stem}"

        row = box.row(align=True)
        row.operator(RR_OT_sqe_create_review_session.bl_idname, text=text, icon="PLAY")

        if active_strip and active_strip.rr.is_render:
            # create box
            layout = self.layout
            box = layout.box()
            box.label(
                text=f"Render: {active_strip.rr.shot_name}", icon="RESTRICT_RENDER_OFF"
            )
            box.separator()

            # render dir name label and open file op
            row = box.row(align=True)
            row.label(text=f"Folder: {Path(active_strip.directory).name}")
            row.operator(
                RR_OT_open_path.bl_idname, icon="FILEBROWSER", text="", emboss=False
            ).filepath = bpy.path.abspath(active_strip.directory)

            # nr of frames
            box.row(align=True).label(
                text=f"Frames: {active_strip.rr.frames_found_text}"
            )

            # inspect exr
            text = "Inspect EXR"
            icon = "VIEWZOOM"
            if not opsdata.get_image_editor(context):
                text = "Inspect EXR: Needs Image Editor"
                icon = "ERROR"

            row = box.row(align=True)
            row.operator(RR_OT_sqe_inspect_exr_sequence.bl_idname, icon=icon, text=text)
            row.operator(RR_OT_sqe_clear_exr_inspect.bl_idname, text="", icon="X")

            # approve render & udpate approved
            row = box.row(align=True)
            row.operator(RR_OT_sqe_approve_render.bl_idname, icon="CHECKMARK")
            row.operator(
                RR_OT_sqe_update_is_approved.bl_idname, text="", icon="FILE_REFRESH"
            )

            # push to edit
            edit_storage_dir = Path(opsdata.get_edit_storage_path(active_strip))
            row = box.row(align=True)
            row.operator(RR_OT_sqe_push_to_edit.bl_idname, icon="EXPORT")
            row.operator(
                RR_OT_open_path.bl_idname, icon="FILEBROWSER", text=""
            ).filepath = edit_storage_dir.as_posix()

        # contactsheet tools
        valid_sequences = opsdata.get_valid_cs_sequences(context)
        if not context.selected_sequences and not valid_sequences:
            return

        # create box
        layout = self.layout
        box = layout.box()
        box.label(text="Contactsheet", icon="MESH_GRID")

        # make contact sheet
        row = box.row(align=True)

        if not context.selected_sequences:
            valid_sequences = opsdata.get_top_level_valid_strips_continious(context)

        text = f"Make Contactsheet with {len(valid_sequences)} strips"

        row.operator(RR_OT_make_contactsheet.bl_idname, icon="MESH_GRID", text=text)
        icon = "UNLOCKED" if context.scene.rr.use_custom_rows else "LOCKED"
        row.prop(context.scene.rr, "use_custom_rows", text="", icon=icon)

        if context.scene.rr.use_custom_rows:
            box.row(align=True).prop(context.scene.rr, "rows")

        # contact sheet resolution
        row = box.row(align=True)
        row.prop(context.scene.rr, "contactsheet_x", text="X")
        row.prop(context.scene.rr, "contactsheet_y", text="Y")


def RR_topbar_file_new_draw_handler(self: Any, context: bpy.types.Context) -> None:
    layout = self.layout
    op = layout.operator(RR_OT_setup_review_workspace.bl_idname, text="Render Review")


# ----------------REGISTER--------------

classes = [
    RR_PT_render_review,
]


def register():

    for cls in classes:
        bpy.utils.register_class(cls)

    # append to topbar file new
    bpy.types.TOPBAR_MT_file_new.append(RR_topbar_file_new_draw_handler)


def unregister():

    # remove to topbar file new
    bpy.types.TOPBAR_MT_file_new.remove(RR_topbar_file_new_draw_handler)

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
