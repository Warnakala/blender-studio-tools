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

import bpy

from . import util, opsdata

logger = logging.getLogger("SVN")

class SVN_refresh_file_list(bpy.types.Operator):
    bl_idname = "svn.refresh_file_list"
    bl_label = "Refresh File List"
    bl_description = "Refresh the file list and check for any changes that should be committed to the SVN"
    bl_options = {'INTERNAL'}

    def execute(self, context: bpy.types.Context) -> Set[str]:
        if bpy.data.is_dirty:
            self.report({'ERROR'}, "The file must be saved first.")
            return {'CANCELLED'}

        # Populate context with collected asset collections.
        opsdata.populate_context_with_external_files(context)

        # Redraw UI.
        util.redraw_ui()

        return {"FINISHED"}

# ----------------REGISTER--------------.

registry = [
    SVN_refresh_file_list
]
