# SPDX-License-Identifier: GPL-2.0-or-later
# (c) 2023, Blender Foundation - Demeter Dzadik

import bpy
from bpy.types import Context, UIList, Operator
from bpy.props import StringProperty
from pathlib import Path

class SVN_OT_open_blend_file(Operator):
    # This is needed because drawing a button for wm.open_mainfile in the UI
    # directly simply does not work; Blender just opens a full-screen filebrowser,
    # instead of opening the .blend file. Probably a bug.
    bl_idname = "svn.open_blend_file"
    bl_label = "Open Blend File"
    bl_description = "Open Blend File"
    bl_options = {'INTERNAL'}

    filepath: StringProperty()

    def execute(self, context):
        bpy.ops.wm.open_mainfile(filepath=self.filepath, load_ui = False)
        return {'FINISHED'}


def check_context_match(context: Context, uilayout_type: str, bl_idname: str) -> bool:
    """For example, when right-clicking on a UIList, the uilayout_type will 
    be `ui_list` and the bl_idname is that of the UIList being right-clicked.
    """
    uilayout = getattr(context, uilayout_type, None)
    return uilayout and uilayout.bl_idname == bl_idname


def svn_file_list_context_menu(self: UIList, context: Context) -> None:
    if not check_context_match(context, 'ui_list', 'SVN_UL_file_list'):
        return

    layout = self.layout
    layout.separator()
    active_file = context.scene.svn.get_repo(context).active_file
    if active_file.name.endswith("blend"):
        layout.operator("svn.open_blend_file",
                    text=f"Open {active_file.name}").filepath = active_file.absolute_path
    else:
        layout.operator("wm.path_open",
                        text=f"Open {active_file.name}").filepath = str(Path(active_file.absolute_path))
    layout.operator("wm.path_open",
                    text=f"Open Containing Folder").filepath = Path(active_file.absolute_path).parent.as_posix()
    layout.separator()


def svn_log_list_context_menu(self: UIList, context: Context) -> None:
    if not check_context_match(context, 'ui_list', 'SVN_UL_log'):
        return

    is_filebrowser = context.space_data.type == 'FILE_BROWSER'
    layout = self.layout
    layout.separator()

    repo = context.scene.svn.get_repo(context)
    active_log = repo.active_log_filebrowser if is_filebrowser else repo.active_log
    layout.operator("svn.download_repo_revision",
                    text=f"Revert Repository To r{active_log.revision_number}").revision = active_log.revision_number
    layout.separator()


def register():
    bpy.types.UI_MT_list_item_context_menu.append(svn_file_list_context_menu)
    bpy.types.UI_MT_list_item_context_menu.append(svn_log_list_context_menu)

def unregister():
    bpy.types.UI_MT_list_item_context_menu.remove(svn_file_list_context_menu)
    bpy.types.UI_MT_list_item_context_menu.remove(svn_log_list_context_menu)

registry = [SVN_OT_open_blend_file]