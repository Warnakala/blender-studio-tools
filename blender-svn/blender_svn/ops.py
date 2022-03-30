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
from bpy.props import StringProperty

from send2trash import send2trash   # NOTE: For some reason, when there's any error in this file, this line seems to take the blame for it?
from . import opsdata

logger = logging.getLogger("SVN")

class SVN_refresh_file_list(bpy.types.Operator):
    bl_idname = "svn.refresh_file_list"
    bl_label = "Check For Local Changes"
    bl_description = "Refresh the file list and create an entry for any changes in the local repository"
    bl_options = {'INTERNAL'}

    def execute(self, context: bpy.types.Context) -> Set[str]:
        # Populate context with collected asset collections.
        opsdata.refresh_file_list(context.scene)

        return {"FINISHED"}

class SVN_check_for_updates(bpy.types.Operator):
    bl_idname = "svn.check_for_updates"
    bl_label = "Check For Remote Changes"
    bl_description = "Check the remote repository for any new file versions that might be available. This can take a few seconds"
    bl_options = {'INTERNAL'}

    svn_root_abs_path: StringProperty()

    def execute(self, context: bpy.types.Context) -> Set[str]:
        opsdata.refresh_file_list(context.scene)

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

        # Remove all outdated files currently in the list
        scene = context.scene
        for i, file_entry in reversed(list(enumerate(scene.svn.external_files))):
            if file_entry.status == 'none':
                scene.svn.external_files.remove(i)

        for file in files:
            opsdata.add_file_entry(context.scene, Path(file[1]), status=('none', file[0]))

        return {"FINISHED"}


class OperatorWithWarning:
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=400)

    def draw(self, context):
        layout = self.layout.column(align=True)

        warning = self.get_warning_text(context)
        for line in warning.split("\n"):
            row = layout.row()
            row.alert = True
            row.label(text=line)

    def get_warning_text(self, context):
        raise NotImplemented


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
        opsdata.refresh_file_list(context.scene)
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


class SVN_restore_file(SVN_file_operator, bpy.types.Operator):
    bl_idname = "svn.restore_file"
    bl_label = "Restore File"
    bl_description = "Restore a file that was deleted"
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
    bl_description = "Discard local changes to the file and return it to the state of the last revision. Local changes are PERMANENTLY DELETED"
    bl_options = {'INTERNAL'}

    missing_file_allowed = False

    def _execute(self, context: bpy.types.Context) -> Set[str]:
        super()._execute(context)
        # TODO: Do anything special if we're reverting the current .blend file?

        return {"FINISHED"}

    def get_warning_text(self, context) -> str:
        return "You will irreversibly and permanently revert local modifications on this file:\n    " + self.file_rel_path


class SVN_add_file(SVN_file_operator, bpy.types.Operator):
    bl_idname = "svn.add_file"
    bl_label = "Add File"
    bl_description = "Mark a locally added file as being added to the remote repository. It will be committed"
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
    bl_description = "Un-mark a locally added file as being added to the remote repository. It will not be committed"
    bl_options = {'INTERNAL'}

    def _execute(self, context: bpy.types.Context) -> Set[str]:
        cmd = f'svn rm --keep-local "{self.file_rel_path}"'
        subprocess.call(
            (cmd), shell=True, cwd=self.svn_root_abs_path+"/"
        )

        return {"FINISHED"}


class SVN_trash_file(SVN_file_operator, bpy.types.Operator):
    bl_idname = "svn.trash_file"
    bl_label = "Trash File"
    bl_description = "Move a local file to the recycle bin"
    bl_options = {'INTERNAL'}

    svn_root_abs_path: StringProperty()
    file_rel_path: StringProperty()

    def _execute(self, context: bpy.types.Context) -> Set[str]:
        send2trash([self.file_full_path])

        return {"FINISHED"}


# ----------------REGISTER--------------.

registry = [
    SVN_refresh_file_list,
    SVN_check_for_updates,
    SVN_revert_file,
    SVN_restore_file,
    SVN_unadd_file,
    SVN_add_file,
    SVN_trash_file
]

def register():
    bpy.app.handlers.save_pre.append(opsdata.refresh_file_list)

def unregister():
    bpy.app.handlers.save_pre.remove(opsdata.refresh_file_list)