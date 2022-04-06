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

import logging

from typing import List, Dict, Union, Any, Set, Optional, Tuple
from pathlib import Path

import bpy, subprocess
from bpy.props import StringProperty, BoolVectorProperty, IntProperty, EnumProperty

from send2trash import send2trash   # NOTE: For some reason, when there's any error in this file, this line seems to take the blame for it?

from .util import get_addon_prefs
from . import svn_status

logger = logging.getLogger("SVN")

def execute_svn_command(svn_root_path: str, command: str) -> str:
    """Execute an svn command in the root of the current svn repository.
    So any file paths that are part of the commend should be relative to the
    SVN root.
    """
    return str(
        subprocess.check_output(
            (command), shell=True, cwd=svn_root_path+"/"
        ),
        'utf-8'
    )

def execute_svn_command_nofreeze(svn_root_path: str, command: str) -> subprocess.Popen:
    """Execute an svn command in the root of the current svn repository using
    Popen(), which avoids freezing the Blender UI.
    """
    return subprocess.Popen(
        (command), shell=True, cwd=svn_root_path+"/", stdout=subprocess.PIPE
    )


class SVN_Operator:
    def execute_svn_command_nofreeze(self, context, command: str) -> subprocess.Popen:
        prefs = get_addon_prefs(context)
        svn_root_path = prefs.svn_directory
        return execute_svn_command_nofreeze(svn_root_path, command)
    
    def execute_svn_command(self, context, command: str) -> subprocess.Popen:
        prefs = get_addon_prefs(context)
        svn_root_path = prefs.svn_directory
        return execute_svn_command(svn_root_path, command)


class SVN_Operator_Single_File(SVN_Operator):
    """Base class for SVN operators operating on a single file."""
    file_rel_path: StringProperty()

    missing_file_allowed = False

    def execute(self, context: bpy.types.Context) -> Set[str]:
        """Most operators want to make sure that the file exists pre-execute."""
        if not self.file_exists(context) and not type(self).missing_file_allowed:
            return {'CANCELLED'}
        ret = self._execute(context)
        context.scene.svn.check_for_local_changes()
        return ret

    def _execute(self, context: bpy.types.Context) -> Set[str]:
        raise NotImplementedError

    def get_file_full_path(self, context) -> Path:
        prefs = get_addon_prefs(context)
        return Path.joinpath(Path(prefs.svn_directory), Path(self.file_rel_path))

    def file_exists(self, context) -> bool:
        exists = self.get_file_full_path(context).exists()
        if not exists and not type(self).missing_file_allowed:
            self.report({'INFO'}, "File was not found, cancelling.")
        return exists


class SVN_check_for_local_changes(bpy.types.Operator):
    bl_idname = "svn.check_for_local_changes"
    bl_label = "Check For Local Changes"
    bl_description = "Refresh the file list based only on local file changes"
    bl_options = {'INTERNAL'}

    def execute(self, context: bpy.types.Context) -> Set[str]:
        context.scene.svn.check_for_local_changes()

        return {"FINISHED"}


class SVN_check_for_updates(SVN_Operator, bpy.types.Operator):
    bl_idname = "svn.check_for_updates"
    bl_label = "Check For All Changes"
    bl_description = "Refresh the file list completely, including asking the remote repository for available updates. This may take a few seconds"
    bl_options = {'INTERNAL'}

    def execute(self, context: bpy.types.Context) -> Set[str]:
        svn_props = context.scene.svn
        svn_props.check_for_local_changes()

        # TODO: This needs to be re-written to use --xml.
        outp = self.execute_svn_command(context, 'svn status --show-updates')

        # Discard the last 2 lines that just shows current revision number.
        lines = outp.split("\n")[:-2]

        # Remove empty lines.
        while True:
            try:
                lines.remove("")
            except ValueError:
                break

        files: List[Tuple[str, str, int]] = [] # filepath, status, revision number
        for line in lines:
            status = 'none'
            split = [s for s in line.split(" ") if s]
            if len(split)==2:
                # The file is not currently on the local repository.
                # Set the revision number to 0, and the status to 'added'.
                rev_no = 0
                status = 'added'
            elif len(split)==4:
                # A file with a new version on the remote also has a non-normal status.
                # This will probably be a conflict.
                status = svn_status.SVN_STATUS_CHAR[split[0]]
                rev_no = int(split[2])
            else:
                rev_no = int(split[1])
            files.append((split[-1], status, rev_no))

        # Mark all previously outdated files as being up to date.
        svn_props.update_outdated_file_entries()

        # Mark the currently outdated files as being outdated.
        for file in files:
            tup = svn_props.get_file_by_svn_path(file[2])
            if tup:
                _idx, file_entry = tup
                file_entry.status = 'none'
                file_entry.revision = file[0]
            else:
                file_entry = svn_props.add_file_entry(Path(file[0]), file[1], file[2])
            file_entry.newer_on_remote = True
            if file_entry.status == 'modified':
                # Strange case 3: A file with an already known new version available 
                # on the remote was modified locally. SVN will give this the 'modified'
                # status, but we want it to say 'conflicted', with options to revert or update.
                file_entry.status = 'conflicted'

        return {"FINISHED"}


class SVN_update_all(SVN_Operator, bpy.types.Operator):
    bl_idname = "svn.update_all"
    bl_label = "SVN Update All"
    bl_description = "Download all the latest updates from the remote repository"
    bl_options = {'INTERNAL'}

    def execute(self, context: bpy.types.Context) -> Set[str]:
        self.execute_svn_command(context, 'svn up --accept "postpone"')
        context.scene.svn.update_outdated_file_entries()

        return {"FINISHED"}


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


class SVN_update_single(SVN_Operator_Single_File, bpy.types.Operator):
    bl_idname = "svn.update_single"
    bl_label = "Update File"
    bl_description = "Download the latest available version of this file from the remote repository"
    bl_options = {'INTERNAL'}

    missing_file_allowed = True

    def _execute(self, context: bpy.types.Context) -> Set[str]:
        self.execute_svn_command(context, f'svn up "{self.file_rel_path}" --accept "postpone"')
        # Remove the file entry for this file
        context.scene.svn.remove_by_svn_path(self.file_rel_path)

        self.report({'INFO'}, f"Updated {self.file_rel_path} to the latest version.")

        return {"FINISHED"}


class SVN_download_file_revision(SVN_Operator_Single_File, bpy.types.Operator):
    bl_idname = "svn.download_file_revision"
    bl_label = "Download Revision"
    bl_description = "Download this revision of this file"
    bl_options = {'INTERNAL'}

    missing_file_allowed = True

    revision: IntProperty()

    def _execute(self, context: bpy.types.Context) -> Set[str]:
        _idx, file = context.scene.svn.get_file_by_svn_path(self.file_rel_path)
        if file.status == 'modified':
            # If file has local modifications, let's avoid a conflict by cancelling
            # and telling the user to resolve it in advance.
            self.report({'ERROR'}, "Cancelled: You have local modifications to this file. You must revert or commit it first!")
            return {'CANCELLED'}

        self.execute_svn_command(context, f'svn up -r{self.revision} "{self.file_rel_path}" --accept "postpone"')

        return {"FINISHED"}
    
    def execute(self, context):
        ret = super().execute(context)
        if ret != {'FINISHED'}:
            return ret
        
        svn = context.scene.svn
        _i, file_entry = svn.get_file_by_svn_path(self.file_rel_path)
        file_entry['revision'] = self.revision
        
        latest_rev = svn.get_latest_revision_of_file(self.file_rel_path)
        file_entry.status = 'normal' if latest_rev == self.revision else 'none'

        self.report({'INFO'}, f"Checked out revision {self.revision} of {self.file_rel_path}")

        return ret


class SVN_restore_file(SVN_Operator_Single_File, bpy.types.Operator):
    bl_idname = "svn.restore_file"
    bl_label = "Restore File"
    bl_description = "Restore this deleted file to its previous revision"
    bl_options = {'INTERNAL'}

    missing_file_allowed = True

    def _execute(self, context: bpy.types.Context) -> Set[str]:
        self.execute_svn_command(context, f'svn revert "{self.file_rel_path}"')

        return {"FINISHED"}


class SVN_revert_file(SVN_restore_file, Warning_Operator):
    bl_idname = "svn.revert_file"
    bl_label = "Revert File"
    bl_description = "PREMANENTLY DISCARD local changes to this file and return it to the state of the last revision. Cannot be undone"
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
        self.execute_svn_command(context, f'svn add "{self.file_rel_path}"')

        return {"FINISHED"}


class SVN_unadd_file(SVN_Operator_Single_File, bpy.types.Operator):
    bl_idname = "svn.unadd_file"
    bl_label = "Un-Add File"
    bl_description = "Un-mark this file as being added to the remote repository. It will not be committed"
    bl_options = {'INTERNAL'}

    def _execute(self, context: bpy.types.Context) -> Set[str]:
        self.execute_svn_command(context, f'svn rm --keep-local "{self.file_rel_path}"')

        return {"FINISHED"}


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


class SVN_resolve_conflict(SVN_Operator_Single_File, bpy.types.Operator):
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
        layout.alert=True
        layout.label(text="Choose which version to keep. The other will be discarded!")
        layout.prop(self, 'resolve_method', expand=True)
        if self.resolve_method == 'mine-full':
            layout.label(text="Your changes will be kept, but they were made on top of an outdated file.")
            layout.label(text="When you commit your changes, the changes someone else made will be lost.")
        else:
            layout.label(text="Your changes will be PERMANENTLY DELETED!")

    def _execute(self, context: bpy.types.Context) -> Set[str]:
        self.execute_svn_command(context, f'svn resolve "{self.file_rel_path}" --accept "{self.resolve_method}"')

        return {"FINISHED"}


commit_message = StringProperty(
    name = "Commit Message",
    description = "Describe the changes being committed",
    options={'SKIP_SAVE'}
)

class SVN_commit(SVN_Operator, Popup_Operator, bpy.types.Operator):
    bl_idname = "svn.commit"
    bl_label = "SVN Commit"
    bl_description = "Commit a selection of files to the remote repository"
    bl_options = {'INTERNAL'}
    bl_property = "commit_message_0"  # Focus the text input box

    MAX_LINES = 32
    __annotations__ = {f'commit_message_{i}' : commit_message for i in range(MAX_LINES)}

    selection: BoolVectorProperty(
        size=32,
        options={'SKIP_SAVE'},
        default = [True]*32
    )

    def get_committable_files(self, context) -> List[str]:
        """Return the list of file entries whose status allows committing"""
        svn_file_list = context.scene.svn.external_files
        committable_statuses = ['modified', 'added', 'deleted']
        files_to_commit = [f for f in svn_file_list if f.status in committable_statuses]
        return files_to_commit

    def draw(self, context):
        """Draws the boolean toggle list with a list of strings for the button texts."""
        layout = self.layout
        files = self.get_committable_files(context)
        layout.label(text="These files will be pushed to the remote repository:")
        for idx, file in enumerate(files):
            row = layout.row()
            row.prop(self, "selection", index=idx, text=file.name)
            row.label(text=file.status_name, icon=file.status_icon)

        row = layout.row()
        row.label(text="Commit message:")
        self.last_idx = 0
        for i in range(type(self).MAX_LINES):
            if getattr(self, f'commit_message_{i}') != "":
                self.last_idx = min(i+1, self.MAX_LINES)
        for i in range(0, self.last_idx+1):
            # Draw input boxes until the last one that has text, plus one.
            layout.prop(self, f'commit_message_{i}', text="")
            continue

    def execute(self, context: bpy.types.Context) -> Set[str]:
        committable_files = self.get_committable_files(context)
        files_to_commit = [f for i, f in enumerate(committable_files) if self.selection[i]]

        if not files_to_commit:
            self.report({'ERROR'}, "No files were selected, nothing to commit.")
            return {'CANCELLED'}

        if len(self.commit_message_0) < 2:
            self.report({'ERROR'}, "Please describe your changes in the commit message!")
            return {'CANCELLED'}
        
        commit_message_lines = [getattr(self, f'commit_message_{i}') for i in range(self.last_idx)]
        commit_message = "\n".join(commit_message_lines)

        report = f"{(len(files_to_commit))} files."
        if len(files_to_commit) == 1:
            report = files_to_commit[0].svn_path
        print(f"Committing {report}")

        filepaths = " ".join([f'"{f.svn_path}"' for f in files_to_commit])

        self.execute_svn_command(context, f'svn commit -m "{commit_message}" {filepaths}')

        # Update the file list.
        # The freshly committed files should now have the 'normal' status.
        context.scene.svn.check_for_local_changes()

        self.report({'INFO'}, f"Committed {report}")

        return {"FINISHED"}


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
    SVN_check_for_local_changes,
    SVN_check_for_updates,
    SVN_update_all,
    SVN_update_single,
    SVN_download_file_revision,
    SVN_revert_file,
    SVN_restore_file,
    SVN_unadd_file,
    SVN_add_file,
    SVN_trash_file,
    SVN_remove_file,
    SVN_commit,
    SVN_cleanup,
    SVN_resolve_conflict,
]
