# SPDX-License-Identifier: GPL-2.0-or-later
# (c) 2023, Blender Foundation - Demeter Dzadik

import bpy

def draw_outdated_file_warning(self, context):
    repo = context.scene.svn.get_repo(context)
    if not repo:
        return
    try:
        current_file = repo.current_blend_file
    except ValueError:
        # This can happen if the svn_directory property wasn't updated yet (not enough time has passed since opening the file)
        pass
    if not current_file:
        # If the current file is not in an SVN repository.
        return

    if current_file.status == 'normal' and current_file.repos_status == 'none':
        return

    layout = self.layout
    row = layout.row()
    row.alert = True

    if current_file.status == 'conflicted':
        row.operator('svn.resolve_conflict',
                     text="SVN: This .blend file is conflicted.", icon='ERROR')
    elif current_file.repos_status != 'none':
        warning = row.operator(
            'svn.custom_tooltip', text="SVN: This .blend file is outdated.", icon='ERROR')
        warning.tooltip = "The currently opened .blend file has a newer version available on the remote repository. This means any changes in this file will result in a conflict, and potential loss of data. See the SVN panel for info"

def register():
    bpy.types.VIEW3D_HT_header.prepend(draw_outdated_file_warning)


def unregister():
    bpy.types.VIEW3D_HT_header.remove(draw_outdated_file_warning)
