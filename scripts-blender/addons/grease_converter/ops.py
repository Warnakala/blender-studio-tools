import logging
from typing import Set, Union, Any, List

import bpy
from mathutils import Vector

logger = logging.getLogger("grease_converter")


def srgb2lin(s: float) -> float:
    if s <= 0.0404482362771082:
        lin = s / 12.92
    else:
        lin = pow(((s + 0.055) / 1.055), 2.4)
    return lin


def lin2srgb(lin: float) -> float:
    if lin > 0.0031308:
        s = 1.055 * (pow(lin, (1.0 / 2.4))) - 0.055
    else:
        s = 12.92 * lin
    return s


def copy_attributes_by_name(source, target):
    ignore = ["rna_type", "name"]
    for key in source.bl_rna.properties.keys():
        if key in ignore:
            continue
        if hasattr(target, key):
            value = getattr(source, key)
            try:
                setattr(target, key, value)
            except:
                print(f"Failed to set {target}.{key} = {value}")

            else:
                print(f"Set {str(target)}.{key}={value}")


class GC_OT_convert_to_grease_pencil(bpy.types.Operator):
    bl_idname = "grease_converter.convert_to_grease_pencil"
    bl_label = "Convert to Grease Pencil"
    bl_description = "Converts Annotation to Grease Pencil Object"

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        annotation: bpy.types.GreasePencil = context.annotation_data
        return bool(annotation)

    def execute(self, context: bpy.types.Context) -> Set[str]:
        annotation: bpy.types.GreasePencil = context.annotation_data

        if not annotation:
            logging.error("No active annotation found")
            return {"CANCELLED"}

        obj_name = f"{annotation.name}_convert_to_gpencil"
        gp: bpy.types.GreasePencil = bpy.data.grease_pencils.new(obj_name)

        # Remove Default layer.
        if len(gp.layers) == 1:
            gp.layers.remove(gp.layers[0])

        copy_attributes_by_name(annotation, gp)

        # This is how annoation behaves even tough its set to "WORLDSPACE"?
        gp.stroke_thickness_space = "SCREENSPACE"

        for alayer in annotation.layers:

            # Create new layer.
            layer = gp.layers.new(alayer.info)
            copy_attributes_by_name(alayer, layer)

            # For some reason on GPencil obj this is 'tint_color'
            layer.tint_color = (
                srgb2lin(alayer.color[0]),
                srgb2lin(alayer.color[1]),
                srgb2lin(alayer.color[2]),
            )

            # Set factor to 1 otherwise tint_color takes no effect.
            layer.tint_factor = 1

            # Needs to be roughly half of annotation thickness to match.
            layer.line_change = layer.thickness

            for aframe in alayer.frames:

                # Create new frame.
                frame = layer.frames.new(aframe.frame_number)
                copy_attributes_by_name(aframe, frame)

                for astroke in aframe.strokes:

                    # Create new stroke.
                    stroke: bpy.types.GPencilStroke = frame.strokes.new()
                    copy_attributes_by_name(astroke, stroke)
                    stroke.line_width = 1  # Otherwise will collide layer.line_change

                    for idx, apoint in enumerate(astroke.points):

                        # Create new point.
                        stroke.points.add(
                            1, pressure=apoint.pressure, strength=apoint.strength
                        )
                        point: bpy.types.GPencilStrokePoint = stroke.points[idx]

                        # Set point coordinates.
                        # point.co = apoint.co
                        copy_attributes_by_name(apoint, point)

        # Create Object that holds gpencil data.
        obj: bpy.types.Object = bpy.data.objects.new(obj_name, gp)

        # Link object in scene.
        context.scene.collection.objects.link(obj)
        return {"FINISHED"}


def new_annotation() -> bpy.types.GreasePencil:
    existing = list(bpy.data.grease_pencils)
    bpy.ops.gpencil.annotation_add()
    for gp in bpy.data.grease_pencils:
        if gp not in existing:
            return gp


class GC_OT_convert_to_annotation(bpy.types.Operator):
    bl_idname = "grease_converter.convert_to_annotation"
    bl_label = "Convert to Annotation"
    bl_description = "Converts Grease Pencil Object to Annotation"

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        gp = context.active_object
        return all(
            [gp, issubclass(bpy.types.GreasePencil, type(context.active_object.data))]
        )

    def execute(self, context: bpy.types.Context) -> Set[str]:
        obj = context.active_object
        gp = obj.data  # Must be GPencil Obj because of poll.
        obj_name = f"{gp.name}_convert_to_annotation"
        annotation: bpy.types.GreasePencil = new_annotation()

        # Remove Default layer.
        if len(annotation.layers) == 1:
            annotation.layers.remove(annotation.layers[0])

        copy_attributes_by_name(gp, annotation)
        annotation.name = obj_name

        for glayer in gp.layers:

            # Create new layer.
            layer = annotation.layers.new(glayer.info)
            copy_attributes_by_name(glayer, layer)

            # For some reason on GPencil obj this is 'tint_color'
            layer.color = (
                lin2srgb(glayer.tint_color[0]),
                lin2srgb(glayer.tint_color[1]),
                lin2srgb(glayer.tint_color[2]),
            )

            # Represents stroke thickness.
            layer.thickness = glayer.line_change

            for gframe in glayer.frames:

                # Create new frame.
                frame = layer.frames.new(gframe.frame_number)
                copy_attributes_by_name(gframe, frame)

                for gstroke in gframe.strokes:

                    # Create new stroke.
                    stroke: bpy.types.GPencilStroke = frame.strokes.new()
                    copy_attributes_by_name(gstroke, stroke)

                    for idx, gpoint in enumerate(gstroke.points):

                        # Create new point.
                        stroke.points.add(
                            1, pressure=gpoint.pressure, strength=gpoint.strength
                        )
                        point: bpy.types.GPencilStrokePoint = stroke.points[idx]

                        # Set point coordinates.
                        copy_attributes_by_name(gpoint, point)

                        # Add global coordinates of object
                        point.co += obj.matrix_world.translation

            return {"FINISHED"}

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event) -> Set[str]:
        obj: bpy.types.Object = context.active_object

        if not obj:
            return {"CANCELLED"}

        # Check if object has any non default roatation or scale values.
        if (
            any([any(obj.rotation_euler), any(obj.scale - Vector((1, 1, 1)))])
            or obj.parent
        ):
            return context.window_manager.invoke_props_dialog(self, width=300)
        else:
            return self.execute(context)

    def draw(self, context: bpy.types.Context) -> None:
        obj: bpy.types.Object = context.active_object
        layout = self.layout

        if any([any(obj.rotation_euler), any(obj.scale - Vector((1, 1, 1)))]):
            layout.label(text="Object tranformations are not applied", icon="ERROR")
        if obj.parent:
            layout.label(text="Object has a parent", icon="ERROR")


# ---------REGISTER ----------.

classes = [GC_OT_convert_to_grease_pencil, GC_OT_convert_to_annotation]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
