import importlib
from bpy.utils import register_class, unregister_class
from . import bone_gizmo_properties
from . import bone_gizmo
from . import bone_gizmo_ui
from . import bone_gizmo_group

from bpy.props import FloatProperty
from bpy.types import Scene, AddonPreferences

bl_info = {
	'name' : "Bone Gizmos"
	,'author': "Demeter Dzadik"
	,'version' : (0, 0, 1)
	,'blender' : (3, 0, 0)
	,'description' : "Bone Gizmos for better armature interaction"
	,'location': "Properties->Bone->Viewport Display->Custom Gizmo"
	,'category': 'Rigging'
	# ,'doc_url' : "https://gitlab.com/blender/CloudRig/"
}

modules = (
	bone_gizmo_properties,
	bone_gizmo,
	bone_gizmo_ui,
	bone_gizmo_group,
)

class BoneGizmoPreferences(AddonPreferences):
	bl_idname = __package__

	bone_gizmo_alpha: FloatProperty(
		name = "Gizmo Opacity"
		,description = "Mesh Gizmo opacity"
		,min = 0.0
		,max = 1.0
		,default = 0.0
		,subtype = 'FACTOR'
	)
	bone_gizmo_alpha_select: FloatProperty(
		name = "Gizmo Opacity (Selected)"
		,description = "Mesh Gizmo opacity when selected"
		,min = 0.0
		,max = 1.0
		,default = 0.1
		,subtype = 'FACTOR'
	)
	bone_gizmo_alpha_highlight: FloatProperty(
		name = "Gizmo Opacity (Highlighted)"
		,description = "Mesh Gizmo opacity when highlighted"
		,min = 0.0
		,max = 1.0
		,default = 0.2
		,subtype = 'FACTOR'
	)

	def draw(self, context):
		layout = self.layout

		layout.prop(self, 'bone_gizmo_alpha')
		layout.prop(self, 'bone_gizmo_alpha_select')
		layout.prop(self, 'bone_gizmo_alpha_highlight')

def register():
	register_class(BoneGizmoPreferences)
	for m in modules:
		importlib.reload(m)
		if hasattr(m, 'registry'):
			for c in m.registry:
				register_class(c)
		if hasattr(m, 'register'):
			m.register()

def unregister():
	unregister_class(BoneGizmoPreferences)
	for m in reversed(modules):
		if hasattr(m, 'unregister'):
			m.unregister()
		if hasattr(m, 'registry'):
			if hasattr(m, 'registry'):
				for c in m.registry:
					unregister_class(c)