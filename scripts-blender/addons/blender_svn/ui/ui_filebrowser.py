# SPDX-License-Identifier: GPL-2.0-or-later
# (c) 2022, Blender Foundation - Demeter Dzadik

from bpy.types import Panel
from bl_ui.space_filebrowser import FileBrowserPanel

from .ui_log import draw_svn_log
from .ui_file_list import draw_repo_file_list
from ..util import get_addon_prefs


class FILEBROWSER_PT_SVN_files(FileBrowserPanel, Panel):
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOLS'
    bl_category = "Bookmarks"
    bl_label = "SVN Files"

    @classmethod
    def poll(cls, context):
        if not super().poll(context):
            return False

        repo = context.scene.svn.get_repo(context)
        if not repo:
            return False

        return repo.is_filebrowser_directory_in_repo(context)

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        # TODO: Get repository of the current file browser's directory.
        prefs = get_addon_prefs(context)
        if len(prefs.repositories) > 0:
            repo = prefs.active_repo
            draw_repo_file_list(context, layout, repo)


class FILEBROWSER_PT_SVN_log(FileBrowserPanel, Panel):
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOLS'
    bl_category = "Bookmarks"
    bl_label = "SVN Log"

    @classmethod
    def poll(cls, context):
        if not super().poll(context):
            return False

        repo = context.scene.svn.get_repo(context)
        if not repo:
            return False

        return repo.get_filebrowser_active_file(context)

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        draw_svn_log(context, layout, file_browser=True)


registry = [
    FILEBROWSER_PT_SVN_files,
    FILEBROWSER_PT_SVN_log
]

