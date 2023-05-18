# SPDX-License-Identifier: GPL-2.0-or-later
# (c) 2022, Blender Foundation - Demeter Dzadik

from bpy.types import Panel

from ..util import get_addon_prefs
from .ui_file_list import draw_repo_file_list, draw_process_info


class VIEW3D_PT_svn_credentials(Panel):
    """Prompt the user to enter their username and password for the remote repository of the current .blend file."""
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'SVN'
    bl_label = 'SVN Credentials'

    @classmethod
    def poll(cls, context):
        prefs = get_addon_prefs(context)
        if prefs.ui_mode == 'CURRENT_BLEND':
            repo = context.scene.svn.get_scene_repo(context)
        else:
            repo = context.scene.svn.get_repo(context)

        return repo and not repo.authenticated

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        col = layout.column(align=True)
        repo = context.scene.svn.get_repo(context)
        row = col.row()
        row.prop(repo, 'display_name', text="Repo Name", icon='FILE_TEXT')
        url = row.operator('svn.custom_tooltip', text="", icon='URL')
        url.tooltip = repo.url
        url.copy_on_click = True
        col.prop(repo, 'username', icon='USER')
        col.prop(repo, 'password', icon='UNLOCKED')
        draw_process_info(context, layout)


class VIEW3D_PT_svn_files(Panel):
    """Display a list of files in the SVN repository of the current .blend file."""
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'SVN'
    bl_label = 'SVN Files'

    @classmethod
    def poll(cls, context):
        repo = context.scene.svn.get_repo(context)
        return repo and repo.authenticated

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        repo = context.scene.svn.get_repo(context)
        draw_process_info(context, layout)
        draw_repo_file_list(context, layout, repo)


registry = [
    VIEW3D_PT_svn_credentials,
    VIEW3D_PT_svn_files,
]

