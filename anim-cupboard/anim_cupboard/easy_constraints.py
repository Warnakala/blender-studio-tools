from typing import Dict, Optional
import bpy
from bpy.props import (FloatProperty, PointerProperty, StringProperty, 
	CollectionProperty, EnumProperty, IntProperty)
from uuid import uuid4

# Easy Constraints
# This will be a panel in the Sidebar that lets animators easily constrain 
# something to another thing.

# For example, by creating separate Copy Loc/Rot/Scale constraints, and 
# displaying them as one entity, with a checkbox for each behaviour, 
# which is actually just the checkbox of the constraints themselves.

# We could maybe even use Child Of constraints, as long as the inverse matrix 
# is stored separately in the add-on, so that it doesn't get lost when removing 
# the constraint.

con_icon = {
	'COPY_LOCATION' : 'CON_LOCLIKE',
	'COPY_ROTATION' : 'CON_ROTLIKE',
	'COPY_SCALE' : 'CON_SIZELIKE',
	'COPY_TRANSFORMS' : 'CON_TRANSLIKE',
	'CHILD_OF' : 'CON_CHILDOF',
}

class EasyConstraint(bpy.types.PropertyGroup):
	con_type: EnumProperty(
		name = "Constraint Type",
		description = "Type of constraint being managed",
		items = [
			('COPY_TRANSFORMS', 'Copy Transforms', 'Copy Transforms', 'CON_TRANSLIKE', 0),
			('CHILD_OF', 'Child Of', 'Child Of', 'CON_CHILDOF', 1),
		]
	)
	name: StringProperty(
		name = "UUID",
		description = "Unique identifier to match constraints to this EasyConstraint instance"
	)
	# influence: FloatProperty(
	# 	name = "Influence",
	# 	description = "Influence of the constraints",
	# 	default = 1.0,
	# 	min = 0.0,
	# 	max = 1.0
	# )
	owner_bone: StringProperty(
		name = "Owner Bone",
		description = "Bone that this EasyConstraint is on. For internal use only. This should never change after initialization"
	)

	@property
	def pose_bone(self) -> Optional[bpy.types.PoseBone]:
		"""Return the associated PoseBone.
		Won't work if the bone was renamed; This cannot be supported.
		"""
		armature = self.id_data
		pb = armature.pose.bones.get(self.owner_bone)
		assert pb, "PoseBone not found for EasyConstraint: " + self.owner_bone
		return pb

	@property
	def influence(self):
		return self.pose_bone[f'EC_influence_{self.name}']

	@influence.setter
	def influence(self, value):
		self.pose_bone[f'EC_influence_{self.name}'] = value

	def get_constraints(self) -> Dict[str, bpy.types.Constraint]:
		constraints = {
			'COPY_LOCATION' : None,
			'COPY_ROTATION' : None,
			'COPY_SCALE' : None
		}
		for c in self.pose_bone.constraints:
			if self.name in c.name:
				if c.type in constraints.keys():
					constraints[c.type] = c

		return constraints

	def update_target(self, context):
		for con_type, con in self.get_constraints().items():
			if not con:
				con = self.pose_bone.constraints.new(type=con_type)
				con.name += " " + self.name
				con.driver_remove('influence')
				d = con.driver_add('influence').driver
				d.expression = "var"
				var = d.variables.new()
				var.type = 'SINGLE_PROP'
				var.targets[0].id = self.target
				# var.targets[0].data_path = f'pose.bones["{self.owner_bone}"].easy_constraints["{self.name}"].influence'
				var.targets[0].data_path = f'pose.bones["{self.owner_bone}"]["EC_influence_{self.name}"]'

			con.target = self.target
			if hasattr(con, 'subtarget'):
				con.subtarget = self.subtarget

	target: PointerProperty(
		type = bpy.types.Object,
		name = "Object",
		description = "Object to copy the transforms of",
		update = update_target
	)
	subtarget: StringProperty(
		name = "Target Bone",
		description = "Bone to copy the transforms of",
		update = update_target
	)


class POSE_OT_easyconstraint_add(bpy.types.Operator):
	"""Stick this bone to another"""
	bl_idname = "pose.easy_constraint_add"
	bl_label = "Add Easy Constraint"
	bl_options = {'REGISTER', 'UNDO'}

	@classmethod
	def poll(cls, context):
		return context.mode == 'POSE' and context.active_pose_bone

	def execute(self, context):
		active_pb = context.active_pose_bone

		easycon = active_pb.easy_constraints.add()
		easycon.owner_bone = context.active_pose_bone.name
		easycon.name = str(uuid4())[:8]
		
		# Custom Property to work around T48975. (TODO: Remove when fixed)
		prop_name = f"EC_influence_{easycon.name}"
		context.active_pose_bone[prop_name] = 1.0
		prop_data = context.active_pose_bone.id_properties_ui(prop_name)
		prop_data.update(min=0, max=1)

		easycon.type = 'COPY_TRANSFORMS'
		if len(context.selected_pose_bones) == 2:
			easycon.target = context.object
			for pb in context.selected_pose_bones:
				if pb == active_pb:
					continue
				easycon.subtarget = pb.name

		return {'FINISHED'}


class POSE_OT_easyconstraint_remove(bpy.types.Operator):
	"""Remove EasyConstraint set-up"""
	bl_idname = "pose.easy_constraint_remove"
	bl_label = "Remove Easy Constraint"
	bl_options = {'REGISTER', 'UNDO'}

	@classmethod
	def poll(cls, context):
		return context.mode == 'POSE' and context.active_pose_bone \
			and len(context.active_pose_bone.easy_constraints) > 0

	def execute(self, context):
		active_pb = context.active_pose_bone

		active_ec = active_pb.easy_constraints[active_pb.easy_constraints_active_index]
		# Remove constraints and constraint drivers
		for _con_type, con in active_ec.get_constraints().items():
			if con:
				con.driver_remove('influence')
				active_ec.pose_bone.constraints.remove(con)

		# Remove influence keyframes from currently active Action
		if context.object.animation_data and context.object.animation_data.action:
			data_path = f'pose.bones["{active_ec.pose_bone.name}"]["EC_influence_{active_ec.name}"]'
			action = context.object.animation_data.action
			fc = action.fcurves.find(data_path)
			if not fc:
				print("Couldn't find fcurve ", data_path)
			else:
				action.fcurves.remove(fc)

		prop_name = f"EC_influence_{active_ec.name}"
		if prop_name in active_pb.keys():
			del active_pb[prop_name]
		active_pb.easy_constraints.remove(active_pb.easy_constraints_active_index)

		active_pb.easy_constraints_active_index = max(0, active_pb.easy_constraints_active_index-1)

		return {'FINISHED'}


class POSE_OT_easyconstraint_kill_influence(bpy.types.Operator):
	"""Set the influence to 0 while preserving the pose and inserting a keyframe. Only one bone must be selected"""
	bl_idname = "pose.easy_constraint_influence_zero"
	bl_label = "Zero Influence"
	bl_options = {'REGISTER', 'UNDO'}

	ec_name: StringProperty()

	@classmethod
	def poll(cls, context):
		# Since we're using the context-based bpy.ops.anim.keyframe_insert_menu(),
		# we want to only allow this operator when there are no other bones selected.
		return len(context.selected_pose_bones) == 1

	def execute(self, context):
		active_pb = context.active_pose_bone
		ec = active_pb.easy_constraints[self.ec_name]

		matrix = active_pb.matrix.copy()
		ec.influence = 0.0
		active_pb.matrix = matrix
		bpy.ops.anim.keyframe_insert_menu()

		return {'FINISHED'}


class EC_UL_constraint_list(bpy.types.UIList):
	def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
		if self.layout_type != 'DEFAULT':
			return

		easy_constraint = item
		row = layout.row(align=True)

		icon = con_icon[easy_constraint.con_type]
		row.label(text="", icon=icon)
		if not easy_constraint.target:
			row.prop(easy_constraint, 'target', text="  Target")
			return
		else:
			row.prop_search(easy_constraint, 'subtarget', easy_constraint.target.data, 'bones', text="")
		for _con_type, con in easy_constraint.get_constraints().items():
			if not con:
				continue
			icon = con_icon[con.type]
			row.prop(con, 'mute', text="", icon_value=row.icon(con)-con.mute+1, invert_checkbox=True)
		row.prop(context.active_pose_bone, f'["EC_influence_{easy_constraint.name}"]', text="", slider=True)
		row.operator(POSE_OT_easyconstraint_kill_influence.bl_idname, text="", icon='CANCEL').ec_name = easy_constraint.name

	def draw_filter(self, context, layout):
		pass


class EC_PT_constraints(bpy.types.Panel):
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'UI'
	bl_category = 'Animation'
	bl_label = 'Easy Constraints'
	# bl_options = {'DEFAULT_CLOSED'}

	@classmethod
	def poll(cls, context):
		return context.mode == 'POSE' and context.active_pose_bone

	def draw(self, context):
		layout = self.layout

		pb = context.active_pose_bone
		row = layout.row()
		row.template_list(
			'EC_UL_constraint_list',
			'',
			pb,
			'easy_constraints',
			pb,
			'easy_constraints_active_index',
		)

		op_col = row.column()
		op_col.operator(POSE_OT_easyconstraint_add.bl_idname, text="", icon='ADD')
		op_col.operator(POSE_OT_easyconstraint_remove.bl_idname, text="", icon='REMOVE')


registry = [
	EasyConstraint,
	POSE_OT_easyconstraint_add,
	POSE_OT_easyconstraint_remove,
	POSE_OT_easyconstraint_kill_influence,
	EC_UL_constraint_list,
	EC_PT_constraints,
]

def register():
	bpy.types.PoseBone.easy_constraints = CollectionProperty(type=EasyConstraint)
	bpy.types.PoseBone.easy_constraints_active_index = IntProperty()

def unregister():
	del bpy.types.PoseBone.easy_constraints
	del bpy.types.PoseBone.easy_constraints_active_index
