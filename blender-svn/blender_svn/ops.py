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

import logging

from typing import List, Dict, Union, Any, Set, Optional, Tuple
from pathlib import Path

import bpy, subprocess
from bpy.props import StringProperty, BoolVectorProperty

from send2trash import send2trash   # NOTE: For some reason, when there's any error in this file, this line seems to take the blame for it?

from .util import get_addon_prefs
from .props import SVN_STATUS_DATA

logger = logging.getLogger("SVN")


class SVN_file_operator:
    """Base class for SVN operators operating on a single file."""
    svn_root_abs_path: StringProperty()
    file_rel_path: StringProperty()

    missing_file_allowed = False

    def execute(self, context: bpy.types.Context) -> Set[str]:
        """All of these operators want to make sure that the file exists,
        before trying to execute."""
        if not self.file_exists() and not type(self).missing_file_allowed:
            return {'CANCELLED'}
        ret = self._execute(context)
        context.scene.svn.check_for_local_changes()
        return ret

    def _execute(self, context: bpy.types.Context) -> Set[str]:
        raise NotImplementedError

    @property
    def file_full_path(self) -> Path:
        return Path.joinpath(Path(self.svn_root_abs_path), Path(self.file_rel_path))

    def file_exists(self) -> bool:
        exists = self.file_full_path.exists()
        if not exists and not type(self).missing_file_allowed:
            self.report({'INFO'}, "File was not found, cancelling.")
        return exists


class SVN_check_for_local_changes(bpy.types.Operator):
    # TODO: Maybe this operator doesn't need to be in the UI, since it runs on file save anyways, and
    # having two different types of refresh buttons may be confusing.
    bl_idname = "svn.check_for_local_changes"
    bl_label = "Check For Local Changes"
    bl_description = "Refresh the file list based only on local file changes"
    bl_options = {'INTERNAL'}

    def execute(self, context: bpy.types.Context) -> Set[str]:
        context.scene.svn.check_for_local_changes()

        return {"FINISHED"}


class SVN_check_for_updates(bpy.types.Operator):
    bl_idname = "svn.check_for_updates"
    bl_label = "Check For All Changes"
    bl_description = "Refresh the file list completely, including asking the remote repository for available updates. This may take a few seconds"
    bl_options = {'INTERNAL'}

    svn_root_abs_path: StringProperty()

    def execute(self, context: bpy.types.Context) -> Set[str]:
        svn_props = context.scene.svn
        svn_props.check_for_local_changes()

        cmd = f'svn status --show-updates'
        outp = str(
            subprocess.check_output(
                (cmd), shell=True, cwd=self.svn_root_abs_path+"/"
            ),
            'utf-8'
        )
        # Discard the last 2 lines that just shows current revision number.
        lines = outp.split("\n")[:-2]
        # Only keep files with no status indicator ("none" status).
        lines = [l for l in lines if l.startswith(" ")]

        # Remove empty lines.
        while True:
            try:
                lines.remove("")
            except ValueError:
                break

        files: List[Tuple[int, str]] = [] # Revision number, filepath
        for line in lines:
            split = [s for s in line.split(" ") if s]
            files.append((int(split[1]), split[2]))

        svn_props.remove_outdated_file_entries()

        prefs = get_addon_prefs(context)
        for file in files:
            abspath = Path.joinpath(Path(prefs.svn_directory), Path(file[1]))
            svn_props.add_file_entry(abspath, status=('none', file[0]))

        return {"FINISHED"}


class SVN_update_all(bpy.types.Operator):
    bl_idname = "svn.update_all"
    bl_label = "SVN Update All"
    bl_description = "Download all the latest updates from the remote repository"
    bl_options = {'INTERNAL'}

    svn_root_abs_path: StringProperty()

    def execute(self, context: bpy.types.Context) -> Set[str]:
        cmd = f'svn up'
        subprocess.call(
            (cmd), shell=True, cwd=self.svn_root_abs_path+"/"
        )
        context.scene.svn.remove_outdated_file_entries()

        return {"FINISHED"}


class OperatorWithPopup:
    popup_width = 400

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=type(self).popup_width)


class OperatorWithWarning(OperatorWithPopup):

    def draw(self, context):
        layout = self.layout.column(align=True)

        warning = self.get_warning_text(context)
        for line in warning.split("\n"):
            row = layout.row()
            row.alert = True
            row.label(text=line)

    def get_warning_text(self, context):
        raise NotImplemented


class SVN_update_single(SVN_file_operator, bpy.types.Operator):
    bl_idname = "svn.update_single"
    bl_label = "Update File"
    bl_description = "Download the latest available version of this file from the remote repository"
    bl_options = {'INTERNAL'}

    missing_file_allowed = True

    def _execute(self, context: bpy.types.Context) -> Set[str]:
        cmd = f'svn up "{self.file_rel_path}"'
        subprocess.call(
            (cmd), shell=True, cwd=self.svn_root_abs_path+"/"
        )

        # Remove the file entry for this file
        context.scene.svn.remove_by_path(str(self.file_full_path))

        return {"FINISHED"}


class SVN_restore_file(SVN_file_operator, bpy.types.Operator):
    bl_idname = "svn.restore_file"
    bl_label = "Restore File"
    bl_description = "Restore this deleted file to its previous revision"
    bl_options = {'INTERNAL'}

    missing_file_allowed = True

    def _execute(self, context: bpy.types.Context) -> Set[str]:
        cmd = f'svn revert "{self.file_rel_path}"'
        subprocess.call(
            (cmd), shell=True, cwd=self.svn_root_abs_path+"/"
        )

        return {"FINISHED"}


class SVN_revert_file(SVN_restore_file, OperatorWithWarning):
    bl_idname = "svn.revert_file"
    bl_label = "Revert File"
    bl_description = "PREMANENTLY DISCARD local changes to this file and return it to the state of the last revision. Cannot be undone"
    bl_options = {'INTERNAL'}

    missing_file_allowed = False

    def _execute(self, context: bpy.types.Context) -> Set[str]:
        super()._execute(context)
        # TODO: Do anything special if we're reverting the current .blend file?

        return {"FINISHED"}

    def get_warning_text(self, context) -> str:
        return "You will irreversibly and permanently lose the changes you've made to this file:\n    " + self.file_rel_path


class SVN_add_file(SVN_file_operator, bpy.types.Operator):
    bl_idname = "svn.add_file"
    bl_label = "Add File"
    bl_description = "Mark this file for addition to the remote repository. It can then be committed"
    bl_options = {'INTERNAL'}

    def _execute(self, context: bpy.types.Context) -> Set[str]:
        cmd = f'svn add "{self.file_rel_path}"'
        subprocess.call(
            (cmd), shell=True, cwd=self.svn_root_abs_path+"/"
        )

        return {"FINISHED"}


class SVN_unadd_file(SVN_file_operator, bpy.types.Operator):
    bl_idname = "svn.unadd_file"
    bl_label = "Un-Add File"
    bl_description = "Un-mark this file as being added to the remote repository. It will not be committed"
    bl_options = {'INTERNAL'}

    def _execute(self, context: bpy.types.Context) -> Set[str]:
        cmd = f'svn rm --keep-local "{self.file_rel_path}"'
        subprocess.call(
            (cmd), shell=True, cwd=self.svn_root_abs_path+"/"
        )

        return {"FINISHED"}


class SVN_trash_file(SVN_file_operator, OperatorWithWarning, bpy.types.Operator):
    bl_idname = "svn.trash_file"
    bl_label = "Trash File"
    bl_description = "Move this file to the recycle bin"
    bl_options = {'INTERNAL'}

    svn_root_abs_path: StringProperty()
    file_rel_path: StringProperty()

    def get_warning_text(self, context):
        return "Are you sure you want to move this file to the recycle bin?\n    " + self.file_rel_path

    def _execute(self, context: bpy.types.Context) -> Set[str]:
        send2trash([self.file_full_path])

        return {"FINISHED"}


class SVN_remove_file(SVN_file_operator, OperatorWithWarning, bpy.types.Operator):
    bl_idname = "svn.remove_file"
    bl_label = "Remove File"
    bl_description = "Mark this file for removal from the remote repository"
    bl_options = {'INTERNAL'}

    missing_file_allowed = True

    svn_root_abs_path: StringProperty()
    file_rel_path: StringProperty()

    def get_warning_text(self, context):
        return "This file will be deleted for everyone:\n    " + self.file_rel_path + "\nAre you sure?"

    def _execute(self, context: bpy.types.Context) -> Set[str]:
        cmd = f'svn remove "{self.file_rel_path}"'
        subprocess.call(
            (cmd), shell=True, cwd=self.svn_root_abs_path+"/"
        )

        return {"FINISHED"}


class SVN_commit(OperatorWithPopup, bpy.types.Operator):
    bl_idname = "svn.commit"
    bl_label = "SVN Commit"
    bl_description = "Commit a selection of files to the remote repository"
    bl_options = {'INTERNAL'}
    bl_property = "commit_message"  # Focus the text input box

    selection: BoolVectorProperty(
        size=32,
        options={'SKIP_SAVE'},
        default = [True]*32
    )
    commit_message: StringProperty(
        name = "Commit Message",
        description = "Describe the changes being committed",
        options={'SKIP_SAVE'}
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
        if 0 < len(self.commit_message) < 15:
            row = row.row()
            row.alert = True
            row.label(text="(min 15 characters!)")
        layout.prop(self, 'commit_message', text="")

    def execute(self, context: bpy.types.Context) -> Set[str]:
        committable_files = self.get_committable_files(context)
        files_to_commit = [f for i, f in enumerate(committable_files) if self.selection[i]]

        if not files_to_commit:
            self.report({'ERROR'}, "No files were selected, nothing to commit.")
            return {'CANCELLED'}

        if len(self.commit_message) < 15:
            self.report({'ERROR'}, "Please describe your changes in the commit message!")
            return {'CANCELLED'}

        report = f"{(len(files_to_commit))} files."
        if len(files_to_commit) == 1:
            report = files_to_commit[0].svn_relative_path
        print(f"Committing {report}")

        svn_root_abs_path = get_addon_prefs(context).svn_directory
        filepaths = " ".join([f'"{f.svn_relative_path}"' for f in files_to_commit])

        cmd = f'svn commit -m "{self.commit_message}" {filepaths}'
        subprocess.call(
            (cmd), shell=True, cwd=svn_root_abs_path+"/"
        )

        # Update the file list.
        # The freshly committed files should now have the 'normal' status.
        context.scene.svn.check_for_local_changes()

        self.report({'INFO'}, f"Committed {report}")

        return {"FINISHED"}


class SVN_cleanup(bpy.types.Operator):
    bl_idname = "svn.cleanup"
    bl_label = "SVN Cleanup"
    bl_description = "Resolve issues that can arise from previous SVN processes having been interrupted"
    bl_options = {'INTERNAL'}

    svn_root_abs_path: StringProperty()

    def execute(self, context: bpy.types.Context) -> Set[str]:
        cmd = f'svn cleanup'
        subprocess.call(
            (cmd), shell=True, cwd=self.svn_root_abs_path+"/"
        )
        self.report({'INFO'}, "SVN Cleanup complete.")

        return {"FINISHED"}


class SVN_explain_status(OperatorWithPopup, bpy.types.Operator):
    bl_idname = "svn.explain_status"
    bl_label = "Explain SVN Status"
    bl_description = "Show an explanation of this status, using a dynamic tooltip"
    bl_options = {'INTERNAL'}

    popup_width = 600

    status: StringProperty(
        description = "Identifier of the status to show an explanation for"
    )

    @staticmethod
    def get_explanation(status: str):
        return SVN_STATUS_DATA[status][1]

    @classmethod
    def description(cls, context, properties):
        return cls.get_explanation(properties.status)

    def draw(self, context):
        self.layout.label(text=self.get_explanation(self.status))

    def execute(self, context):
        return {'FINISHED'}


# ----------------REGISTER--------------.

registry = [
    SVN_check_for_local_changes,
    SVN_check_for_updates,
    SVN_update_all,
    SVN_update_single,
    SVN_revert_file,
    SVN_restore_file,
    SVN_unadd_file,
    SVN_add_file,
    SVN_trash_file,
    SVN_remove_file,
    SVN_commit,
    SVN_cleanup,
    SVN_explain_status,
]
