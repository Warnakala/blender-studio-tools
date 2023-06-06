# Pose Shape Keys addon for Blender
# Copyright (C) 2022 Demeter Dzadik
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
	"name": "Pose Shape Keys",
	"author": "Demeter Dzadik",
    "version": (0, 0, 2),
	"blender": (3, 1, 0),
	"location": "Properties -> Mesh Data -> Shape Keys -> Pose Keys",
	"description": "Create shape keys that blend deformed meshes into a desired shape",
	"category": "Rigging",
	"doc_url": "",
	"tracker_url": "",
}

import importlib
from bpy.utils import register_class, unregister_class
from bpy.types import AddonPreferences
from bpy.props import BoolProperty

from . import ui
from . import pose_key
from . import ui_list
from . import reset_rig
from . import symmetrize_shape_key

# Each module can have register() and unregister() functions and a list of classes to register called "registry".
modules = [
	ui
	,pose_key
	,ui_list
	,reset_rig
	,symmetrize_shape_key
]

class PoseShapeKeysPrefs(AddonPreferences):
	bl_idname = __package__

	show_shape_key_info: BoolProperty(
		name = "Reveal Shape Key Properties"
		,description = "Show and edit the properties of the corresponding shape key"
		,default = True
	)
	no_warning: BoolProperty(
		name = "No Warning"
		,description = "Do not show a pop-up warning for dangerous operations"
	)
	grid_objects_on_jump: BoolProperty(
		name = "Place Objects In Grid On Jump"
		,description = "When using the Jump To Storage Object operator, place the other storage objects in a grid"
		,default = True
	)

	def draw(self, context):
		self.layout.prop(self, 'no_warning')
		self.layout.prop(self, 'grid_objects_on_jump')

def register_unregister_modules(modules: [], register: bool):
	register_func = register_class if register else unregister_class

	for m in modules:
		if register:
			importlib.reload(m)
		if hasattr(m, 'registry'):
			for c in m.registry:
				register_func(c)

		if hasattr(m, 'modules'):
			register_unregister_modules(m.modules, register)

		if register and hasattr(m, 'register'):
			m.register()
		elif hasattr(m, 'unregister'):
			m.unregister()

def register():
	register_class(PoseShapeKeysPrefs)
	register_unregister_modules(modules, register=True)

def unregister():
	unregister_class(PoseShapeKeysPrefs)
	register_unregister_modules(modules, register=False)
