import bpy
from bpy.types import Object, Scene, PropertyGroup
from bpy.props import (
	IntProperty, PointerProperty, BoolProperty,
	FloatVectorProperty, StringProperty, EnumProperty,
	FloatProperty
)

class BoneGizmoProperties(PropertyGroup):
	enabled: BoolProperty(
		name		 = "Enable Gizmo"
		,description = "Attach a custom gizmo to this bone"
		,default	 = False
	)

	operator: EnumProperty(
		name		 = "Operator"
		,description = "Operator to use when click and dragging on the gizmo"
		,items		 = [
			('None', "None", "Only select the bone on click & drag, ignoring the dragging")
			,('transform.translate', "Translate", "Translate the bone on click & drag")
			,('transform.rotate', "Rotate", "Rotate the bone on click & drag")
			,('transform.resize', "Scale", "Scale the bone on click & drag")
		]
		,default	 = 'transform.translate'
	)
	rotation_mode: EnumProperty(
		name		 = "Rotation Mode"
		,description = "How the bone should rotate on initial click & drag interaction"
		,items		 = [
			('VIEW', "View", "Viewing angle dependent rotation,  same as pressing R or using the outer white ring of the rotation gizmo")
			,('TRACKBALL', "Trackball", "Trackball-type rotation, could be useful for eyes")
			,('X', "X", "Rotate along local X axis")
			,('Y', "Y", "Rotate along local Y axis")
			,('Z', "Z", "Rotate along local Z axis")
		]
		,default	 = 'VIEW'
	)

	shape_object: PointerProperty(
		name		 = "Shape"
		,type		 = Object
		,description = "Object to use as shape for this gizmo"
		,poll		 = lambda self, object: object.type == 'MESH'
	)
	face_map_name: StringProperty(
		name		 = "Face Map"
		,description = "Face Map to use as shape for this gizmo"
	)
	vertex_group_name: StringProperty(
		name		 = "Vertex Group"
		,description = "Vertex Group to use as shape for this gizmo"
	)
	use_face_map: BoolProperty(
		name		 = "Mesh Mask Type"
		,description = "Toggle between using Face Maps or Vertex Groups as the mesh masking data"	# Currently it seems face maps are just worse vertex groups, but maybe they are faster, or maybe it's good to have them separated.
	)

	draw_style: EnumProperty(
		name		 = "Style"
		,description = "Display style of the gizmo"
		,items		 = [
			('POINTS', "Points", "Points")
			,('LINES', "Lines", "Lines")
			,('TRIS', "Tris", "Tris")
		]
		,default	 = 'LINES'
	)


	use_bone_group_color: BoolProperty(
		name		 = "Use Bone Group Color"
		,description = "Use the bone group color for this Gizmo, rather than the unique colors"
		,default	 = True
	)
	color: FloatVectorProperty(
		name		 = "Color"
		,description = "Color of the gizmo"
		,subtype	 = 'COLOR'
		,size		 = 3
		,min		 = 0.0
		,max		 = 1.0
		,default	 = (1.0, 0.05, 0.38)
	)

	color_highlight: FloatVectorProperty(
		name		 = "Highlight Color"
		,description = "Color of the gizmo when mouse hovered"
		,subtype	 = 'COLOR'
		,size		 = 3
		,min		 = 0.0
		,max		 = 1.0
		,default	 = (1.0, 0.5, 1.0)
	)

	line_width: IntProperty(
		name		 = "Line Width"
		,description = "Thickness of the drawn lines in pixels"
		,min		 = 1
		,max		 = 10
		,default	 = 1
	)

	# This is made redundant by the ability to set the color to fully transparent.
	use_draw_hover: BoolProperty(
		name		 = "Hover Only"
		,description = "Draw the gizmo only when it is being mouse hovered"
		,default	 = False
	)

	# These functionalities sadly don't work when the gizmo uses target_set_operator,
	# which we absolutely need.
	use_draw_modal: BoolProperty(
		name		 = "Draw During Interact"
		,description = "Draw the gizmo during interaction"
		,default	 = True
	)

	use_draw_value: BoolProperty(
		name		 = "Draw Interact Value"
		,description = "Draw values in the top-left corner of the viewport during interaction"
		,default	 = True
	)

	use_draw_cursor: BoolProperty(
		name		 = "Draw Interact Mouse"
		,description = "Draw the mouse cursor during interaction"
		,default	 = True
	)

classes = (
	BoneGizmoProperties,
)
register_cls, unregister_cls = bpy.utils.register_classes_factory(classes)


def register():
	register_cls()

	bpy.types.PoseBone.bone_gizmo = PointerProperty(type=BoneGizmoProperties)

	Scene.bone_gizmos_enabled = BoolProperty(
		name		 = "Bone Gizmos"
		,description = "Globally toggle bone gizmos"
		,default	 = True
	)


def unregister():
	unregister_cls()

	del bpy.types.PoseBone.bone_gizmo
	del Scene.bone_gizmos_enabled
