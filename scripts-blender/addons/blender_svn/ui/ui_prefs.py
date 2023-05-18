# SPDX-License-Identifier: GPL-2.0-or-later
# (c) 2023, Blender Foundation - Demeter Dzadik

from pathlib import Path

from bpy.types import UIList, Operator
from bpy_extras.io_utils import ImportHelper

from ..util import get_addon_prefs
from .ui_log import draw_svn_log, is_log_useful
from .ui_file_list import draw_repo_file_list, draw_process_info
from ..threaded.background_process import Processes

class SVN_UL_repositories(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        repo = item
        row = layout.row()
        row.label(text=repo.display_name)

        if not repo.is_valid:
            row.alert = True
        row.prop(repo, 'directory', text="")

class SVN_OT_repo_add(Operator, ImportHelper):
    """Add a repository to the list"""
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    bl_idname = "svn.repo_add"
    bl_label = "Add Repository"

    def execute(self, context):
        prefs = get_addon_prefs(context)
        repos = prefs.repositories

        path = Path(self.filepath)
        if path.is_file():
            path = path.parent

        existing_repos = repos[:]
        try:
            repo = prefs.init_repo(context, path)
        except Exception as e:
            self.report({'ERROR'}, "Failed to initialize repository. Ensure you have SVN installed, and that the selected directory is the root of a repository.")
            print(e)
            return {'CANCELLED'}
        if not repo:
            self.report({'ERROR'}, "Failed to initialize repository.")
            return {'CANCELLED'}
        if repo in existing_repos:
            self.report({'INFO'}, "Repository already present.")
        else:
            self.report({'INFO'}, "Repository added.")
        prefs.active_repo_idx = repos.find(repo.directory)
        prefs.save_repo_info_to_file()
        return {'FINISHED'}

class SVN_OT_repo_remove(Operator):
    """Remove a repository from the list"""
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    bl_idname = "svn.repo_remove"
    bl_label = "Remove Repository"

    @classmethod
    def poll(cls, context):
        return len(get_addon_prefs(context).repositories) > 0

    def execute(self, context):
        prefs = get_addon_prefs(context)
        active_index = prefs.active_repo_idx
        repos = prefs.repositories

        prefs.repositories.remove(prefs.active_repo_idx)
        to_index = min(active_index, len(repos) - 1)
        prefs.active_repo_idx = to_index
        prefs.save_repo_info_to_file()
        return {'FINISHED'}


def draw_prefs(self, context) -> None:
    layout = self.layout

    row = layout.row()
    row.use_property_split = True
    row.prop(self, 'ui_mode', expand=True)

    auth_in_progress = False
    auth_error = False
    auth_proc = Processes.get('Authenticate')
    if auth_proc:
        auth_in_progress = auth_proc.is_running
        auth_error = auth_proc.error

    if self.ui_mode == 'CURRENT_BLEND' and not context.scene.svn.get_repo(context):
        split = layout.split(factor=0.4)
        split.row()
        split.row().label(text="Current file is not in a repository.")
        return

    repo_col = layout.column()
    split = repo_col.row().split()
    split.row().label(text="SVN Repositories:")
    row = split.row()
    row.alignment = 'RIGHT'
    row.prop(self, 'debug_mode')

    repo_col.enabled = not auth_in_progress

    list_row = repo_col.row()
    if self.ui_mode == 'CURRENT_BLEND':
        list_row.enabled = False
    col = list_row.column()
    col.template_list(
        "SVN_UL_repositories",
        "svn_repo_list",
        self,
        "repositories",
        self,
        "active_repo_idx",
    )

    op_col = list_row.column()
    op_col.operator('svn.repo_add', icon='ADD', text="")
    op_col.operator('svn.repo_remove', icon='REMOVE', text="")

    if len(self.repositories) == 0:
        return
    if self.active_repo_idx-1 > len(self.repositories):
        return
    active_repo = self.repositories[self.active_repo_idx]
    if not active_repo:
        return

    repo_col.prop(active_repo, 'display_name', icon='FILE_TEXT')
    repo_col.prop(active_repo, 'url', icon='URL')
    repo_col.prop(active_repo, 'username', icon='USER')
    repo_col.prop(active_repo, 'password', icon='LOCKED')

    draw_process_info(context, layout.row())

    if not self.active_repo.authenticated and not auth_in_progress and not auth_error:
        split = layout.split(factor=0.24)
        split.row()
        col = split.column()
        col.label(text="Repository not authenticated. Enter your credentials.")
        return

    if len(self.repositories) > 0 and self.active_repo.authenticated:
        layout.separator()
        layout.label(text="Files: ")
        draw_repo_file_list(context, layout, self.active_repo)

        if is_log_useful(context):
            layout.separator()
            layout.label(text="Log: ")
            draw_svn_log(context, layout, file_browser=False)


registry = [
    SVN_UL_repositories,
    SVN_OT_repo_add,
    SVN_OT_repo_remove
]