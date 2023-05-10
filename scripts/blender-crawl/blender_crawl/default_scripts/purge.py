
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
# (c) 2021, Blender Foundation

import sys
import logging


logger = logging.getLogger(__name__)

import bpy

# Setup prefs.
bpy.context.preferences.filepaths.save_version = 0

# Purge.
logger.info("Starting Recursive Purge")
bpy.ops.outliner.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)

# Save.
bpy.ops.wm.save_mainfile()
logger.info("Saved file: %s", bpy.data.filepath)

# Quit.
logger.info("Closing File")
bpy.ops.wm.quit_blender()
