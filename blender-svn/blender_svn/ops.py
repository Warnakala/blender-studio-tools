# ***** BEGIN GPL LICENSE BLOCK *****
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
# ***** END GPL LICENCE BLOCK *****
#
# (c) 2021, Blender Foundation - Paul Golter
# (c) 2022, Blender Foundation - Demeter Dzadik

from typing import List, Dict, Union, Any, Set, Optional, Tuple
from pathlib import Path

import bpy
from bpy.props import StringProperty, IntProperty, EnumProperty, BoolProperty

from send2trash import send2trash

from .props import SVN_file
from .execute_subprocess import execute_svn_command


class SVN_Operator:
    def execute_svn_command(self, context, command: str, use_cred=False) -> str:
        # Since a status update might already be being requested when an SVN operator is run,
        # we want to ignore the first update after any SVN operator.
        # Otherwise it can result in a predicted state being overwritten by an outdated state.
        # For example, the Commit operator sets a file to "Normal" state, then the old svn status
        # arrives and sets it back to "Modified" state, which it isn't anymore.
        return execute_svn_command(context, command, use_cred)

class SVN_Operator_Single_File(SVN_Operator):
    """Base class for SVN operators operating on a single file."""
    file_rel_path: StringProperty()

    missing_file_allowed = False

    def execute(self, context: bpy.types.Context) -> Set[str]:
        """Most operators want to make sure that the file exists pre-execute."""
        if not self.file_exists(context) and not type(self).missing_file_allowed:
            self.report({'ERROR'}, "File is no longer on the file system.")
            return {'CANCELLED'}
        ret = self._execute(context)

        svn = context.scene.svn
        file = self.get_file(context)
        if file:
            self.set_predicted_file_status(svn, file)
            file.status_predicted_flag = "SINGLE"

        return ret

    def _execute(self, context: bpy.types.Context) -> Set[str]:
        raise NotImplementedError

    def get_file_full_path(self, context) -> Path:
        svn = context.scene.svn
        return Path.joinpath(Path(svn.svn_directory), Path(self.file_rel_path))

    def get_file(self, context) -> SVN_file:
        return context.scene.svn.get_file_by_svn_path(self.file_rel_path)

    def file_exists(self, context) -> bool:
        exists = self.get_file_full_path(context).exists()
        if not exists and not type(self).missing_file_allowed:
            self.report({'INFO'}, "File was not found, cancelling.")
        return exists


class Popup_Operator:
    popup_width = 400

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=type(self).popup_width)


class Warning_Operator(Popup_Operator):

    def draw(self, context):
        layout = self.layout.column(align=True)

        warning = self.get_warning_text(context)
        for line in warning.split("\n"):
            row = layout.row()
            row.alert = True
            row.label(text=line)

    def get_warning_text(self, context):
        raise NotImplemented


class May_Modifiy_Current_Blend(SVN_Operator_Single_File, Warning_Operator):

    def file_is_current_blend(self, context) -> bool:
        return context.scene.svn.current_blend_file.svn_path == self.file_rel_path

    reload_file: BoolProperty(
        name = "Reload File",
        description = "Reload the file after the operation is completed. The UI layout will be preserved",
        default = False,
    )

    def invoke(self, context, event):
        self.reload_file = False
        if self.file_is_current_blend(context) or self.get_warning_text(context):
            return context.window_manager.invoke_props_dialog(self, width=500)

        return self.execute(context)

    def get_warning_text(self, context):
        if self.file_is_current_blend(context):
            return "This will modify the currently opened .blend file."
        return ""

    def draw(self, context):
        super().draw(context)
        if self.file_is_current_blend(context):
            self.layout.prop(self, 'reload_file')
    
    def execute(self, context):
        super().execute(context)
        if self.reload_file:
            bpy.ops.wm.open_mainfile(filepath=bpy.data.filepath, load_ui=False)
        return {'FINISHED'}

    def set_predicted_file_status(self, svn, file_entry: SVN_file):
        return


class SVN_update_single(May_Modifiy_Current_Blend, bpy.types.Operator):
    bl_idname = "svn.update_single"
    bl_label = "Update File"
    bl_description = "Download the latest available version of this file from the remote repository"
    bl_options = {'INTERNAL'}

    missing_file_allowed = True

    def _execute(self, context: bpy.types.Context) -> Set[str]:
        self.will_conflict = False
        file_entry = context.scene.svn.get_file_by_svn_path(self.file_rel_path)
        if file_entry.status != 'normal':
            self.will_conflict = True

        self.execute_svn_command(context, f'svn up "{self.file_rel_path}" --accept "postpone"', use_cred=True)

        self.report({'INFO'}, f"Updated {self.file_rel_path} to the latest version.")

    def set_predicted_file_status(self, svn, file_entry: SVN_file):
        if self.will_conflict: 
            file_entry.status = 'conflicted'
        else:
            file_entry.status = 'normal'
            file_entry.repos_status = 'none'

        return {"FINISHED"}


class SVN_download_file_revision(May_Modifiy_Current_Blend, bpy.types.Operator):
    bl_idname = "svn.download_file_revision"
    bl_label = "Download Revision"
    bl_description = "Download this revision of this file"
    bl_options = {'INTERNAL'}

    missing_file_allowed = True

    revision: IntProperty()

    def invoke(self, context, event):
        file_entry = context.scene.svn.get_file_by_svn_path(self.file_rel_path)
        if self.file_is_current_blend(context) and file_entry.status != 'normal':
            self.report({'ERROR'}, 'You must first revert or commit the changes to this file.')
            return {'CANCELLED'}
        return super().invoke(context, event)

    def _execute(self, context: bpy.types.Context) -> Set[str]:
        file_entry = context.scene.svn.get_file_by_svn_path(self.file_rel_path)
        if file_entry.status == 'modified':
            # If file has local modifications, let's avoid a conflict by cancelling
            # and telling the user to resolve it in advance.
            self.report({'ERROR'}, "Cancelled: You have local modifications to this file. You must revert or commit it first!")
            return {'CANCELLED'}

        self.execute_svn_command(context, f'svn up -r{self.revision} "{self.file_rel_path}" --accept "postpone"', use_cred=True)

        self.report({'INFO'}, f"Checked out revision {self.revision} of {self.file_rel_path}")

        return {"FINISHED"}

    def set_predicted_file_status(self, svn, file_entry: SVN_file):
        file_entry['revision'] = self.revision
        latest_rev = svn.get_latest_revision_of_file(self.file_rel_path)
        file_entry.status = 'normal' if latest_rev == self.revision else 'none'


class SVN_restore_file(May_Modifiy_Current_Blend, bpy.types.Operator):
    bl_idname = "svn.restore_file"
    bl_label = "Restore File"
    bl_description = "Restore this deleted file to its previous revision"
    bl_options = {'INTERNAL'}

    missing_file_allowed = True

    def _execute(self, context: bpy.types.Context) -> Set[str]:
        self.execute_svn_command(context, f'svn revert "{self.file_rel_path}"')

        f = self.get_file(context)
        return {"FINISHED"}

    def set_predicted_file_status(self, svn, file_entry: SVN_file):
        file_entry.status = 'normal'


class SVN_revert_file(SVN_restore_file):
    bl_idname = "svn.revert_file"
    bl_label = "Revert File"
    bl_description = "PERMANENTLY DISCARD local changes to this file and return it to the state of the last local revision. Cannot be undone"
    bl_options = {'INTERNAL'}

    missing_file_allowed = False

    def _execute(self, context: bpy.types.Context) -> Set[str]:
        super()._execute(context)

        return {"FINISHED"}

    def get_warning_text(self, context) -> str:
        return "You will irreversibly and permanently lose the changes you've made to this file:\n    " + self.file_rel_path


class SVN_add_file(SVN_Operator_Single_File, bpy.types.Operator):
    bl_idname = "svn.add_file"
    bl_label = "Add File"
    bl_description = "Mark this file for addition to the remote repository. It can then be committed"
    bl_options = {'INTERNAL'}

    def _execute(self, context: bpy.types.Context) -> Set[str]:
        result = self.execute_svn_command(context, f'svn add "{self.file_rel_path}"')

        if result:
            f = self.get_file(context)
        return {"FINISHED"}

    def set_predicted_file_status(self, svn, file_entry: SVN_file):
        file_entry.status = 'added'


class SVN_unadd_file(SVN_Operator_Single_File, bpy.types.Operator):
    bl_idname = "svn.unadd_file"
    bl_label = "Un-Add File"
    bl_description = "Un-mark this file as being added to the remote repository. It will not be committed"
    bl_options = {'INTERNAL'}

    def _execute(self, context: bpy.types.Context) -> Set[str]:
        self.execute_svn_command(context, f'svn rm --keep-local "{self.file_rel_path}"')

        return {"FINISHED"}

    def set_predicted_file_status(self, svn, file_entry: SVN_file):
            file_entry.status = 'unversioned'


class SVN_trash_file(SVN_Operator_Single_File, Warning_Operator, bpy.types.Operator):
    bl_idname = "svn.trash_file"
    bl_label = "Trash File"
    bl_description = "Move this file to the recycle bin"
    bl_options = {'INTERNAL'}

    file_rel_path: StringProperty()

    def get_warning_text(self, context):
        return "Are you sure you want to move this file to the recycle bin?\n    " + self.file_rel_path

    def _execute(self, context: bpy.types.Context) -> Set[str]:
        send2trash([self.get_file_full_path(context)])

        f = self.get_file(context)
        # Since this operator is only available for Unversioned files,
        # we want to remove the file entry when removing the file.
        context.scene.svn.remove_file_entry(f)
        return {"FINISHED"}


class SVN_remove_file(SVN_Operator_Single_File, Warning_Operator, bpy.types.Operator):
    bl_idname = "svn.remove_file"
    bl_label = "Remove File"
    bl_description = "Mark this file for removal from the remote repository"
    bl_options = {'INTERNAL'}

    missing_file_allowed = True

    def get_warning_text(self, context):
        return "This file will be deleted for everyone:\n    " + self.file_rel_path + "\nAre you sure?"

    def _execute(self, context: bpy.types.Context) -> Set[str]:
        self.execute_svn_command(context, f'svn remove "{self.file_rel_path}"')

        return {"FINISHED"}

    def set_predicted_file_status(self, svn, file_entry: SVN_file):
        file_entry.status = 'deleted'


class SVN_resolve_conflict(May_Modifiy_Current_Blend, bpy.types.Operator):
    bl_idname = "svn.resolve_conflict"
    bl_label = "Resolve Conflict"
    bl_description = "Resolve a conflict, by discarding either local or remote changes"
    bl_options = {'INTERNAL'}

    resolve_method: EnumProperty(
        name = "Resolve Method",
        description = "Method to use to resolve the conflict",
        items = [
            ('mine-full', 'Keep Mine', 'Overwrite the new changes downloaded from the remote, and keep the local changes instead'),
            ('theirs-full', 'Keep Theirs', 'Overwrite the local changes with those downloaded from the remote'),
        ]
    )

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self, width=500)

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)
        col.alert=True
        col.label(text="Choose which version of the file to keep.")
        col.row().prop(self, 'resolve_method', expand=True)
        if self.resolve_method == 'mine-full':
            col.label(text="Local changes will be kept.")
            col.label(text="When committing, the changes someone else made will be overwritten.")
        else:
            col.label(text="Local changes will be permanently lost.")
            super().draw(context)

    def _execute(self, context: bpy.types.Context) -> Set[str]:
        self.execute_svn_command(context, f'svn resolve "{self.file_rel_path}" --accept "{self.resolve_method}"')

        return {"FINISHED"}

    def set_predicted_file_status(self, svn, file_entry: SVN_file):
        if self.resolve_method == 'mine-full':
            file_entry.status = 'modified'
        else:
            file_entry.status = 'normal'


class SVN_cleanup(SVN_Operator, bpy.types.Operator):
    bl_idname = "svn.cleanup"
    bl_label = "SVN Cleanup"
    bl_description = "Resolve issues that can arise from previous SVN processes having been interrupted"
    bl_options = {'INTERNAL'}

    def execute(self, context: bpy.types.Context) -> Set[str]:
        self.execute_svn_command(context, 'svn cleanup')
        self.report({'INFO'}, "SVN Cleanup complete.")

        return {"FINISHED"}



registry = [
    SVN_update_single,
    SVN_download_file_revision,
    SVN_revert_file,
    SVN_restore_file,
    SVN_unadd_file,
    SVN_add_file,
    SVN_trash_file,
    SVN_remove_file,
    SVN_cleanup,
    SVN_resolve_conflict,
]
