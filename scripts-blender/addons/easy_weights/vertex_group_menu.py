import bpy

from .vertex_group_operators import (
	DeleteEmptyDeformGroups,
	FocusDeformBones,
	DeleteUnselectedDeformGroups,
	DeleteUnusedVertexGroups,
	CreateMirrorGroups
)

class MESH_MT_vertex_group_batch_delete(bpy.types.Menu):
	bl_label = "Batch Delete"

	def draw(self, context):
		layout = self.layout
		layout.operator(
			"object.vertex_group_remove", 
			text="All Groups",
			icon='TRASH'
		).all = True
		layout.operator(
			"object.vertex_group_remove", 
			text="All Unlocked Groups",
			icon='UNLOCKED'
		).all_unlocked = True
		layout.separator()
		layout.operator(DeleteEmptyDeformGroups.bl_idname, text="Empty Deform Groups", icon='GROUP_BONE')
		layout.operator(DeleteUnusedVertexGroups.bl_idname, text="Unused Non-Deform Groups", icon='BRUSH_DATA')
		layout.operator(DeleteUnselectedDeformGroups.bl_idname, text="Unselected Deform Groups", icon='RESTRICT_SELECT_ON')

class MESH_MT_vertex_group_symmetry(bpy.types.Menu):
	bl_label = "Symmetry"

	def draw(self, context):
		layout = self.layout
		layout.operator(
			"object.vertex_group_mirror", 
			text="Mirror Active Group (Proximity)", 
			icon='AUTOMERGE_OFF'
		).use_topology = False
		layout.operator(
			"object.vertex_group_mirror", 
			text="Mirror Active Group (Topology)", 
			icon='AUTOMERGE_ON'
		).use_topology = True

		layout.separator()

		layout.operator(
			"object.symmetrize_vertex_weights", 
			text="Symmetrize Active Group", 
			icon='MOD_MIRROR'
		).groups = 'ACTIVE'
		layout.operator(
			"object.symmetrize_vertex_weights", 
			text="Symmetrize Selected Bones' Groups", 
			icon='MOD_MIRROR'
		).groups = 'BONES'
		op = layout.operator(
			"object.symmetrize_vertex_weights", 
			text="Symmetrize All Left->Right", 
			icon='MOD_MIRROR'
		)
		op.groups = 'ALL'
		op.direction = 'LEFT_TO_RIGHT'
		op = layout.operator(
			"object.symmetrize_vertex_weights", 
			text="Symmetrize All Right->Left", 
			icon='MOD_MIRROR'
		)
		op.groups = 'ALL'
		op.direction = 'RIGHT_TO_LEFT'

class MESH_MT_vertex_group_sort(bpy.types.Menu):
	bl_label = "Sort"

	def draw(self, context):
		layout = self.layout
		layout.operator(
			"object.vertex_group_sort",
			icon='SORTALPHA',
			text="By Name",
		).sort_type = 'NAME'
		layout.operator(
			"object.vertex_group_sort",
			icon='BONE_DATA',
			text="By Bone Hierarchy",
		).sort_type = 'BONE_HIERARCHY'

class MESH_MT_vertex_group_copy(bpy.types.Menu):
	bl_label = "Copy"

	def draw(self, context):
		layout = self.layout

		# TODO: This isn't grayed out when there's no active group.
		# TODO: Maybe for things that use the active group, we should put the name of the group in the button text? Makes it harder to search tho perhaps. Not even sure if menu search supports dynamic menu text?
		layout.operator("object.vertex_group_copy", icon='DUPLICATE', text="Duplicate Group")
		layout.separator()
		layout.operator("object.vertex_group_copy_to_linked", text="Synchronize Groups on All Instances", icon='LINKED')
		layout.operator("object.vertex_group_copy_to_selected", text="Synchronize Groups on Selected", icon = 'RESTRICT_SELECT_OFF')

class MESH_MT_vertex_group_lock(bpy.types.Menu):
	bl_label = "Batch Lock"

	def draw(self, context):
		layout = self.layout

		props = layout.operator("object.vertex_group_lock", icon='LOCKED', text="Lock All")
		props.action, props.mask = 'LOCK', 'ALL'
		props = layout.operator("object.vertex_group_lock", icon='UNLOCKED', text="Unlock All")
		props.action, props.mask = 'UNLOCK', 'ALL'
		props = layout.operator("object.vertex_group_lock", icon='UV_SYNC_SELECT', text="Invert All Locks")
		props.action, props.mask = 'INVERT', 'ALL'

class MESH_MT_vertex_group_weight(bpy.types.Menu):
	bl_label = "Weights"

	def draw(self, context):
		layout = self.layout

		layout.operator(
			"object.vertex_group_remove_from",
			icon='MESH_DATA',
			text="Remove Selected Verts from All Groups",
		).use_all_groups = True
		layout.operator(
			"object.vertex_group_clean", 
			icon='BRUSH_DATA', 
			text="Clean 0 Weights from All Groups"
		).group_select_mode = 'ALL'

		layout.separator()

		layout.operator(
			"object.vertex_group_remove_from", 
			icon='TRASH',
			text="Remove All Verts from Selected Group"
		).use_all_verts = True

		layout.separator()

		layout.operator(
			'paint.weight_from_bones', 
			text="Assign Automatic from Bones",
			icon='BONE_DATA'
			).type='AUTOMATIC'
		op = layout.operator(
			'object.vertex_group_normalize_all', 
			text="Normalize Deform",
			icon='IPO_SINE'
			)
		op.group_select_mode = 'BONE_DEFORM'
		op.lock_active = False

def draw_misc(self, context):
	layout = self.layout
	layout.operator(FocusDeformBones.bl_idname, icon='ZOOM_IN')

	# TODO: Add an operator called "Smart Cleanup" that creates missing mirror groups,
	# Cleans 0 weights,
	# Deletes unused deforming groups,
	# and deletes unused non-deforming groups.

def draw_vertex_group_menu(self, context):
	layout = self.layout
	layout.row().menu(menu='MESH_MT_vertex_group_batch_delete', icon='TRASH')
	layout.row().menu(menu='MESH_MT_vertex_group_symmetry', icon='ARROW_LEFTRIGHT')
	layout.row().menu(menu='MESH_MT_vertex_group_sort', icon='SORTALPHA')
	layout.row().menu(menu='MESH_MT_vertex_group_copy', icon='DUPLICATE')
	layout.row().menu(menu='MESH_MT_vertex_group_lock', icon='LOCKED')
	layout.row().menu(menu='MESH_MT_vertex_group_weight', icon='MOD_VERTEX_WEIGHT')

classes = [
	MESH_MT_vertex_group_batch_delete,
	MESH_MT_vertex_group_symmetry,
	MESH_MT_vertex_group_sort,
	MESH_MT_vertex_group_copy,
	MESH_MT_vertex_group_lock,
	MESH_MT_vertex_group_weight
]

def register():
	from bpy.utils import register_class
	for c in classes:
		register_class(c)


	bpy.types.MESH_MT_vertex_group_context_menu.old_draw = bpy.types.MESH_MT_vertex_group_context_menu.draw
	bpy.types.MESH_MT_vertex_group_context_menu.remove(bpy.types.MESH_MT_vertex_group_context_menu.draw)
	
	bpy.types.MESH_MT_vertex_group_context_menu.append(draw_vertex_group_menu)
	bpy.types.MESH_MT_vertex_group_context_menu.append(draw_misc)

def unregister():
	from bpy.utils import unregister_class
	
	bpy.types.MESH_MT_vertex_group_context_menu.draw = bpy.types.MESH_MT_vertex_group_context_menu.old_draw
	del bpy.types.MESH_MT_vertex_group_context_menu.old_draw
	bpy.types.MESH_MT_vertex_group_context_menu.remove(draw_vertex_group_menu)
	bpy.types.MESH_MT_vertex_group_context_menu.remove(draw_misc)
	
	for c in classes:
		unregister_class(c)