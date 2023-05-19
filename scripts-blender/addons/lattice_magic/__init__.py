# Copyright (C) 2020 Demeter Dzadik
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful, 
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

bl_info = {
	"name": "Lattice Magic",
	"author": "Demeter Dzadik",
	"version": (1,0),
	"blender": (2, 90, 0),
	"location": "View3D > Sidebar > Lattice Magic",
	"description": "Various Lattice-based tools to smear or adjust geometry.",
	"category": "Rigging",
	"doc_url": "https://gitlab.com/blender/lattice_magic/-/wikis/home",
	"tracker_url": "https://gitlab.com/blender/lattice_magic/-/issues/new",
}

from . import camera_lattice
from . import tweak_lattice
from . import operators
from . import utils # Just for importlib.reload()
import importlib

import bpy
from bpy.types import AddonPreferences
from bpy.props import BoolProperty

class LatticeMagicPreferences(AddonPreferences):
	bl_idname = __name__
	
	update_active_shape_key: BoolProperty(
		name = 'Update Active Shape Key',
		description = "Update the active shape key on frame change based on the current frame and the shape key's name",
		default = False
	)

modules = [
	camera_lattice
	,tweak_lattice
	,operators
	,utils
]

def register():
	from bpy.utils import register_class
	register_class(LatticeMagicPreferences)
	for m in modules:
		importlib.reload(m)
		if hasattr(m, 'register'):
			m.register()

def unregister():
	from bpy.utils import unregister_class
	unregister_class(LatticeMagicPreferences)
	for m in modules:
		if hasattr(m, 'unregister'):
			m.unregister()