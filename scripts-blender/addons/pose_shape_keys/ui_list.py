import bpy
from bpy.types import Operator, UILayout
from bpy.props import EnumProperty, StringProperty

def get_context_attr(context, data_path):
	return eval("context." + data_path)

def set_context_attr(context, data_path, value):
	# NOTE: str(value) has to evaluate back to value, so this will only work for simple types.
	exec("context." + data_path + " = " + str(value))

class GenericUIListOperator(Operator):
	bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

	# Sadly operators don't seem to inherit parameters, so this
	# has no use beside being the source of copy-pasting.
	list_context_path: StringProperty()
	active_idx_context_path: StringProperty()

	def get_list(self, context):
		return get_context_attr(context, self.list_context_path)

	def get_active_index(self, context):
		return get_context_attr(context, self.active_idx_context_path)

	def set_active_index(self, context, index):
		set_context_attr(context, self.active_idx_context_path, index)

class UILIST_OT_Entry_Remove(GenericUIListOperator):
	"""Remove the selected entry from the list"""

	bl_idname = "ui.list_entry_remove"
	bl_label = "Remove Selected Entry"

	list_context_path: StringProperty()
	active_idx_context_path: StringProperty()

	def execute(self, context):
		my_list = self.get_list(context)
		active_index = self.get_active_index(context)

		# This behaviour is inconsistent with other UILists in Blender, but I am right and they are wrong!
		to_index = active_index
		if to_index > len(my_list)-2:
			to_index = len(my_list)-2

		my_list.remove(active_index)
		self.set_active_index(context, to_index)

		return { 'FINISHED' }

class UILIST_OT_Entry_Add(GenericUIListOperator):
	"""Add an entry to the list"""

	bl_idname = "ui.list_entry_add"
	bl_label = "Add Entry"

	list_context_path: StringProperty()
	active_idx_context_path: StringProperty()

	def execute(self, context):
		my_list = self.get_list(context)
		active_index = self.get_active_index(context)

		to_index = active_index + 1
		if len(my_list)==0:
			to_index = 0

		my_list.add()
		my_list.move(len(my_list)-1, to_index)
		self.set_active_index(context, to_index)

		return { 'FINISHED' }

class UILIST_OT_Entry_Move(GenericUIListOperator):
	"""Move an entry in the list up or down"""

	bl_idname = "ui.list_entry_move"
	bl_label = "Move Entry"

	direction: EnumProperty(
		name		 = "Direction"
		,items 		 = [
			('UP', 'UP', 'UP'),
			('DOWN', 'DOWN', 'DOWN'),
		]
		,default	 = 'UP'
	)

	def execute(self, context):
		my_list = self.get_list(context)
		active_index = self.get_active_index(context)

		to_index = active_index + (1 if self.direction=='DOWN' else -1)

		if to_index > len(my_list)-1:
			to_index = 0
		if to_index < 0:
			to_index = len(my_list)-1

		my_list.move(active_index, to_index)
		self.set_active_index(context, to_index)

		return { 'FINISHED' }

def draw_ui_list(
			layout
			,context
			,class_name = 'UI_UL_list'
			,*	# Only keyword arguments from here.
			,list_context_path = 'object.data.vertex_groups'
			,active_idx_context_path = 'object.data.vertex_groups.active_index'
			,insertion_operators = True
			,move_operators = True
			,menu_class_name = ''
			,**kwargs
		) -> UILayout:
	"""This is intended as a replacement for row.template_list().
	By changing the requirements of the parameters, we can provide the Add, Remove and Move Up/Down operators
	without the person implementing the UIList having to worry about that stuff.
	"""
	row = layout.row()

	list_owner = eval("context." + ".".join(list_context_path.split(".")[:-1]))
	list_prop_name = list_context_path.split(".")[-1]
	idx_owner = eval("context." + ".".join(active_idx_context_path.split(".")[:-1]))
	idx_prop_name = active_idx_context_path.split(".")[-1]

	my_list = get_context_attr(context, list_context_path)

	row.template_list(
		class_name
		,list_context_path if class_name == 'UI_UL_list' else ""

		,list_owner
		,list_prop_name
		,idx_owner
		,idx_prop_name

		,rows = 4 if len(my_list) > 0 else 1
		,**kwargs
	)

	col = row.column()
	if insertion_operators:
		add_op = col.operator('ui.list_entry_add', text="", icon='ADD')
		add_op.list_context_path = list_context_path
		add_op.active_idx_context_path = active_idx_context_path

		row = col.row()
		row.enabled = len(my_list) > 0
		remove_op = row.operator('ui.list_entry_remove', text="", icon='REMOVE')
		remove_op.list_context_path = list_context_path
		remove_op.active_idx_context_path = active_idx_context_path

		col.separator()

	if menu_class_name != '':
		col.menu(menu_class_name, icon='DOWNARROW_HLT', text="")
		col.separator()

	if move_operators and len(my_list) > 0:
		col = col.column()
		col.enabled = len(my_list) > 1
		move_up_op = col.operator('ui.list_entry_move', text="", icon='TRIA_UP')
		move_up_op.direction='UP'
		move_up_op.list_context_path = list_context_path
		move_up_op.active_idx_context_path = active_idx_context_path

		move_down_op = col.operator('ui.list_entry_move', text="", icon='TRIA_DOWN')
		move_down_op.direction='DOWN'
		move_down_op.list_context_path = list_context_path
		move_down_op.active_idx_context_path = active_idx_context_path

	# Return the right-side column.
	return col

# Below is the implementation of the default behaviours of
# UIList built-in functions.
# These are not used anywhere, they are merely templates you can
# copy-paste to start coding your custom behaviours in your UIList class.

def filter_items(self, context, data, propname):
	"""Default filtering functionality:
		- Filter by name
		- Invert filter
		- Sort alphabetical by name
	"""
	flt_flags = []
	flt_neworder = []
	list_items = getattr(data, propname)

	helper_funcs = bpy.types.UI_UL_list

	if self.use_filter_sort_alpha:
		flt_neworder = helper_funcs.sort_items_by_name(list_items, "name")

	if self.filter_name:
		flt_flags = helper_funcs.filter_items_by_name(self.filter_name, self.bitflag_filter_item, list_items, "name",
														reverse=self.use_filter_sort_reverse)

	if not flt_flags:
		flt_flags = [self.bitflag_filter_item] * len(island_groups)

	if self.use_filter_invert:
		for idx, flag in enumerate(flt_flags):
			flt_flags[idx] = 0 if flag else self.bitflag_filter_item

	return flt_flags, flt_neworder

def draw_filter(self, context, layout):
	"""Default filtering UI:
	- String input for name filtering
	- Toggles for invert, sort alphabetical, reverse sort
	"""
	main_row = layout.row()
	row = main_row.row(align=True)

	row.prop(self, 'filter_name', text="")
	row.prop(self, 'use_filter_invert', toggle=True, text="", icon='ARROW_LEFTRIGHT')

	row = main_row.row(align=True)
	row.use_property_split=True
	row.use_property_decorate=False
	row.prop(self, 'use_filter_sort_alpha', toggle=True, text="")
	icon = 'SORT_DESC' if self.use_filter_sort_reverse else 'SORT_ASC'
	row.prop(self, 'use_filter_sort_reverse', toggle=True, text="", icon=icon)

def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
	my_item = item
	if self.layout_type in {'DEFAULT', 'COMPACT'}:
		layout.prop(my_item, 'name')
	elif self.layout_type in {'GRID'}:
		pass

registry = [
	UILIST_OT_Entry_Remove,
	UILIST_OT_Entry_Add,
	UILIST_OT_Entry_Move,
]
