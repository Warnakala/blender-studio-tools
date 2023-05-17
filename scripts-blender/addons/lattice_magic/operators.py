import bpy
from bpy.props import FloatProperty
from .utils import get_lattice_point_original_position

class LATTICE_OT_Reset(bpy.types.Operator):
	"""Reset selected lattice points to their default position"""
	bl_idname = "lattice.reset_points"
	bl_label = "Reset Lattice Points"
	bl_options = {'REGISTER', 'UNDO'}

	factor: FloatProperty(name="Factor", min=0, max=1, default=1)

	@classmethod
	def poll(cls, context):
		return len(context.selected_objects)>0 and context.mode=='EDIT_LATTICE'

	def draw(self, context):
		layout = self.layout
		layout.use_property_split = True
		layout.prop(self, 'factor', slider=True)

	def execute(self, context):
		bpy.ops.object.mode_set(mode='OBJECT')
		for ob in context.selected_objects:
			if ob.type!='LATTICE': 
				continue
			
			# Resetting shape key or Basis shape
			if ob.data.shape_keys:
				active_index = ob.active_shape_key_index
				key_blocks = ob.data.shape_keys.key_blocks
				active_block = key_blocks[active_index]
				basis_block = key_blocks[0]
				if active_index > 0:
					for i, skp in enumerate(active_block.data):
						if not ob.data.points[i].select: continue
						skp.co = skp.co.lerp(basis_block.data[i].co, self.factor)
					continue
				else:
					for i, skp in enumerate(active_block.data):
						if not ob.data.points[i].select: continue
						base = get_lattice_point_original_position(ob.data, i)
						# Resetting the Basis shape
						mix = basis_block.data[i].co.lerp(base, self.factor)
						basis_block.data[i].co = mix
				continue

			# Otherwise, reset the actual points.
			for i in range(len(ob.data.points)):
				point = ob.data.points[i]
				if not point.select: continue
				base = get_lattice_point_original_position(ob.data, i)
				mix = point.co_deform.lerp(base, self.factor)
				point.co_deform = mix

		bpy.ops.object.mode_set(mode='EDIT')
		return {'FINISHED'}

def draw_shape_key_reset(self, context):
	layout = self.layout
	ob = context.object
	if ob.type=='MESH':
		op = layout.operator('mesh.blend_from_shape', text='Reset Shape Key', icon='FILE_REFRESH')
		op.shape = ob.data.shape_keys.key_blocks[0].name
		op.blend = 1
		op.add = False
	else:
		layout.operator(LATTICE_OT_Reset.bl_idname, text="Reset Shape Key", icon='FILE_REFRESH')

def draw_lattice_reset(self, context):
	self.layout.operator(LATTICE_OT_Reset.bl_idname, text="Reset Point Positions", icon='FILE_REFRESH')

classes = [
	LATTICE_OT_Reset
]

def register():
	from bpy.utils import register_class
	for c in classes:
		register_class(c)
	bpy.types.MESH_MT_shape_key_context_menu.append(draw_shape_key_reset)
	bpy.types.VIEW3D_MT_edit_lattice.append(draw_lattice_reset)

def unregister():
	from bpy.utils import unregister_class
	for c in reversed(classes):
		unregister_class(c)

	bpy.types.MESH_MT_shape_key_context_menu.remove(draw_shape_key_reset)
	bpy.types.VIEW3D_MT_edit_lattice.remove(draw_lattice_reset)