# SPDX-License-Identifier: GPL-2.0-or-later
# (c) 2022, Blender Foundation - Demeter Dzadik

import bpy
from pathlib import Path
from bl_ui.space_filebrowser import FileBrowserPanel

from .ui_log import draw_svn_log
from .ui_sidebar import draw_svn_file_list
from ..commands.background_process import BackgroundProcess, process_in_background


class FILEBROWSER_PT_SVN_files(FileBrowserPanel, bpy.types.Panel):
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

        draw_svn_file_list(context, layout)


class FILEBROWSER_PT_SVN_log(FileBrowserPanel, bpy.types.Panel):
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


class BGP_SVN_Activate_File(BackgroundProcess):
    """This crazy hacky method of activating the file with some delay is necessary 
    because Blender won't let us select the file immediately when changing the 
    directory - some time needs to pass before the files actually appear.
    (This is visible with the naked eye as the file browser is empty for a 
    brief moment whenever params.dictionary is changed.)
    """

    name = "Activate File"
    needs_authentication = False
    tick_delay = 0.1
    debug = False

    def acquire_output(self, context, prefs):
        self.output = "dummy"

    def process_output(self, context, prefs):
        if not hasattr(context.scene, 'svn'):
            return

        repo = context.scene.svn.get_repo(context)
        for area in context.screen.areas:
            if area.type == 'FILE_BROWSER':
                area.spaces.active.activate_file_by_relative_path(
                    relative_path=repo.active_file.name)

        self.stop()

    def get_ui_message(self, context):
        return ""


registry = [
    FILEBROWSER_PT_SVN_files,
    FILEBROWSER_PT_SVN_log
]


def register():
    process_in_background(BGP_SVN_Activate_File)
