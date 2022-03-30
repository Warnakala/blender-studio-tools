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

from send2trash import send2trash
from . import util, opsdata

logger = logging.getLogger("SVN")

class SVN_refresh_file_list(bpy.types.Operator):
    bl_idname = "svn.refresh_file_list"
    bl_label = "Refresh File List"
    bl_description = "Refresh the file list and check for any changes that should be committed to the SVN"
    bl_options = {'INTERNAL'}

    def execute(self, context: bpy.types.Context) -> Set[str]:
        if bpy.data.is_dirty:
            self.report({'ERROR'}, "The .blend file must be saved first.")
            return {'CANCELLED'}

        # Populate context with collected asset collections.
        opsdata.populate_context_with_external_files(context)

        # Redraw UI.
        util.redraw_ui()

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

class SVN_revert_file(OperatorWithWarning, bpy.types.Operator):
    bl_idname = "svn.revert_file"
    bl_label = "Revert File"
    bl_description = "Discard local changes to the file and return it to the state of the last revision. Local changes are PERMANENTLY DELETED"
    bl_options = {'INTERNAL'}

    svn_root_abs_path: StringProperty()
    file_rel_path: StringProperty()

    def execute(self, context: bpy.types.Context) -> Set[str]:
        cmd = f'svn revert "{self.file_rel_path}"'
        subprocess.call(
            (cmd), shell=True, cwd=self.svn_root_abs_path+"/"
        )
        bpy.ops.svn.refresh_file_list()
        # TODO: Do anything special if we're reverting the current .blend file?

        return {"FINISHED"}

    def get_warning_text(self, context) -> str:
        return "You will irreversibly and permanently revert local modifications on this file:\n    " + self.file_rel_path


class SVN_add_file(bpy.types.Operator):
    bl_idname = "svn.add_file"
    bl_label = "Add File"
    bl_description = "Mark a locally added file as being added to the remote repository. It will be committed"
    bl_options = {'INTERNAL'}

    svn_root_abs_path: StringProperty()
    file_rel_path: StringProperty()

    def execute(self, context: bpy.types.Context) -> Set[str]:
        cmd = f'svn add "{self.file_rel_path}"'
        subprocess.call(
            (cmd), shell=True, cwd=self.svn_root_abs_path+"/"
        )
        bpy.ops.svn.refresh_file_list()

        return {"FINISHED"}

class SVN_unadd_file(bpy.types.Operator):
    bl_idname = "svn.unadd_file"
    bl_label = "Un-Add File"
    bl_description = "Un-mark a locally added file as being added to the remote repository. It will not be committed"
    bl_options = {'INTERNAL'}

    svn_root_abs_path: StringProperty()
    file_rel_path: StringProperty()

    def execute(self, context: bpy.types.Context) -> Set[str]:
        cmd = f'svn rm --keep-local "{self.file_rel_path}"'
        subprocess.call(
            (cmd), shell=True, cwd=self.svn_root_abs_path+"/"
        )
        bpy.ops.svn.refresh_file_list()

        return {"FINISHED"}


class SVN_trash_file(bpy.types.Operator):
    bl_idname = "svn.trash_file"
    bl_label = "Trash File"
    bl_description = "Move a local file to the recycle bin"
    bl_options = {'INTERNAL'}

    svn_root_abs_path: StringProperty()
    file_rel_path: StringProperty()

    def execute(self, context: bpy.types.Context) -> Set[str]:
        file_full_path = Path.joinpath(Path(self.svn_root_abs_path), Path(self.file_rel_path))
        send2trash([file_full_path])
        bpy.ops.svn.refresh_file_list()

        return {"FINISHED"}


# ----------------REGISTER--------------.

registry = [
    SVN_refresh_file_list,
    SVN_revert_file,
    SVN_unadd_file,
    SVN_add_file,
    SVN_trash_file
]
