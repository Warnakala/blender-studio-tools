import bpy
from bpy.props import BoolProperty
from .pose_key import get_deforming_armature

class CK_OT_reset_rig(bpy.types.Operator):
	"""Reset all bone transforms and custom properties to their default values"""
	bl_idname = "object.posekey_reset_rig"
	bl_label = "Reset Rig"
	bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

	reset_transforms: BoolProperty(name="Transforms", default=True, description="Reset bone transforms")
	reset_props: BoolProperty(name="Properties", default=True, description="Reset custom properties")
	selection_only: BoolProperty(name="Selected Only", default=False, description="Affect selected bones rather than all bones")

	def invoke(self, context, event):
		wm = context.window_manager
		return wm.invoke_props_dialog(self)

	def execute(self, context):
		rigged_ob = context.object
		rig = get_deforming_armature(rigged_ob)
		bones = rig.pose.bones
		if self.selection_only:
			bones = context.selected_pose_bones
		for pb in bones:
			if self.reset_transforms:
				pb.location = ((0, 0, 0))
				pb.rotation_euler = ((0, 0, 0))
				pb.rotation_quaternion = ((1, 0, 0, 0))
				pb.scale = ((1, 1, 1))

			if self.reset_props and len(pb.keys()) > 0:
				rna_properties = [prop.identifier for prop in pb.bl_rna.properties if prop.is_runtime]

				# Reset custom property values to their default value
				for key in pb.keys():
					if key.startswith("$"): continue
					if key in rna_properties: continue	# Addon defined property.

					ui_data = None
					try:
						ui_data = pb.id_properties_ui(key)
						if not ui_data: continue
						ui_data = ui_data.as_dict()
						if not 'default' in ui_data: continue
					except TypeError:
						# Some properties don't support UI data, and so don't have a default value. (like addon PropertyGroups)
						pass

					if not ui_data: continue

					if type(pb[key]) not in (float, int): continue
					pb[key] = ui_data['default']

		return {'FINISHED'}

registry = [
	CK_OT_reset_rig
]