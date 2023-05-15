import bpy
from pathlib import Path

def svn_file_list_context_menu(self: bpy.types.UIList, context: bpy.types.Context) -> None:
    def is_svn_file_list() -> bool:
        # Important: Must check context first, or the menu is added for every kind of list.
        ui_list = getattr(context, "ui_list", None)
        return ui_list and ui_list.bl_idname == 'SVN_UL_file_list'

    if not is_svn_file_list():
        return

    layout = self.layout
    layout.separator()
    active_file = context.scene.svn.get_repo(context).active_file
    layout.operator("wm.path_open",
                    text=f"Open {active_file.name}").filepath = active_file.relative_path
    layout.operator("wm.path_open",
                    text=f"Open Containing Folder").filepath = Path(active_file.absolute_path).parent.as_posix()
    layout.separator()


def svn_log_list_context_menu(self: bpy.types.UIList, context: bpy.types.Context) -> None:
    def is_svn_log_list() -> bool:
        # Important: Must check context first, or the menu is added for every kind of list.
        ui_list = getattr(context, "ui_list", None)
        return ui_list and ui_list.bl_idname == 'SVN_UL_log'

    if not is_svn_log_list():
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