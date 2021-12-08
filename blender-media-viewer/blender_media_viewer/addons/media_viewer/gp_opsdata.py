import bpy
from typing import Any, Union, Dict, List, Tuple
from mathutils import Vector


def get_translation_vector_to_3dview(
    resolution: Tuple[int, int], origin_area_type: str
) -> Vector:
    """
    Returns a Vector that can be used to transform annotation points
    coming from SEQUENCE_EDITOR or IMAGE_EDITOR so the (0,0,0) is in the
    bottom left and matches the way the 3D_CAMERA_VIEW Screen coordinate
    system works.
    """
    if origin_area_type not in ["SEQUENCE_EDITOR", "IMAGE_EDITOR"]:
        raise ValueError(
            f"{origin_area_type} not in ['SEQUENCE_EDITOR', 'IMAGE_EDITOR']"
        )

    # We assume gpobj was painted on media file that had same resolution
    # as current scene has.
    res_x = resolution[0]
    res_y = resolution[1]

    if origin_area_type == "SEQUENCE_EDITOR":
        return Vector((res_x / 2, res_y / 2, 0))

    else:
        return Vector((0, 0, 0))


def get_scale_vector_to_3dview(
    resolution: Tuple[int, int], origin_area_type: str
) -> Vector:
    """
    Returns a Vector that can be used to scale annotation points
    coming from SEQUENCE_EDITOR or IMAGE_EDITOR to fit 3D_CAMERA_VIEW
    coordinate system. (Makes them fit between 0-100)
    """
    if origin_area_type not in ["SEQUENCE_EDITOR", "IMAGE_EDITOR"]:
        raise ValueError(
            f"{origin_area_type} not in ['SEQUENCE_EDITOR', 'IMAGE_EDITOR']"
        )

    # We assume gpobj was painted on media file that had same resolution
    # as current scene has.
    res_x = resolution[0]
    res_y = resolution[1]

    if origin_area_type == "SEQUENCE_EDITOR":
        return Vector((100 / res_x, 100 / res_y, 1))

    else:
        return Vector((100, 100, 0))


def gplayer_sqe_to_3d(
    gpobj: bpy.types.GreasePencil,
    v_translate: Vector,
    v_scale: Vector,
) -> bpy.types.GreasePencil:
    """
    Loops through all points of input gpobj and first translates them with v_translate Vector
    and then scales them with the v_scale Vector.
    v_translate should move all points so the bottom left corner is (0,0,0) and thus matches
    the coordinate system of the 4D_CAMERA_VIEW. v_scale then scales all points so they fit in
    the range of 0-100.
    """
    # Should copy the data but currently there seems to be no way to change active
    # annotation_data (context.annotation_data) with Python.
    try:
        gp_exists = bpy.data.grease_pencils[f"{gpobj.name}_3D_CONVERT"]
    except KeyError:
        pass
    else:
        bpy.data.grease_pencils.remove(gp_exists)

    gp_convert: bpy.types.GreasePencil = gpobj.copy()
    gp_convert.name = f"{gpobj.name}_3D_CONVERT"

    # We assume gpobj was painted on media file that had same resolution
    # as current scene has.

    # To understand here is an image of how the SQE calculates
    # its screen coordinates with the example resolution
    # of (2048, 858)

    """
    (-1024,429,0)----------(1024,429,0)
    |                      |
    |        C(0,0,0)      |
    |                      |
    (-1024,-429,0)---------(1024,-429,0)
    """

    # Here is a graphic of how the ImageEditor calculates
    # its screen coordinates with the example resolution
    # of (2048, 858)

    """
    (0,1,0)----------------(1,1,0)
    |                      |
    |        C(0.5,0.5,0)  |
    |                      |
    (0,0,0)----------------(1,0,0)
    """
    # The graphic here shows what the coordinates
    # of the screen corners are in the 3D camera view
    # This applies to Grease Pencil
    # when stroke.display_mode = "SCREEN"
    # scene render resolution is (2048, 858)

    """
    (0,100,0)--------------(100,100,0)
    |                      |
    |        C(50,50,0)    |
    |                      |
    (0,0,0)----------------(100,0,0)
    """
    # Note: No matter what the resolution is the
    # coordinates on corners are always 100

    # We want to convert the point coordinates that were
    # drawn in the SQE to coordinates to coordinates that work
    # in the 3D Camera View when stroke.display_mode = "SCREEN"

    for layer in gp_convert.layers:

        for frame in layer.frames:

            # For autocomplete.
            frame: bpy.types.GPencilFrame = frame

            for stroke in frame.strokes:
                # For autocomplete.
                stroke: bpy.types.GPencilStroke = stroke

                # Set stroke to screen.
                stroke.display_mode = "SCREEN"

                for point in stroke.points:
                    v_point: Vector = point.co

                    # First we want to translate all points of the sqe so the DOWN_LEFT
                    # one is at (0,0,0) same to 3D Camera View
                    v_point = v_point + v_translate
                    # print(f"{point.co} -> {v_point}")
                    # Then we want to multiply the point by a factor
                    # so it fits in 0-100 respectively.

                    # v_print = v_point
                    v_point = v_point * v_scale
                    # print(f"{v_print} -> {v_point}")
                    # print("\n")

                    # Update actual point coordinate.
                    point.co = v_point

    return gp_convert


if __name__ == "__main__":
    resolution = (
        bpy.context.scene.render.resolution_x,
        bpy.context.scene.render.resolution_y,
    )
    v_translate = get_translation_vector_to_3dview(resolution, "IMAGE_EDITOR")
    v_scale = get_scale_vector_to_3dview(resolution, "IMAGE_EDITOR")

    gpobj = bpy.data.grease_pencils["TEST_IMAGE_EDITOR"]
    gplayer_sqe_to_3d(gpobj, v_translate, v_scale)

# Calculate corner coordinates of SQE with that resolution.
# sqe_up_left = Vector((-res_x / 2, res_y / 2, 0))
# sqe_up_right = Vector((res_x / 2, res_y / 2, 0))
# sqe_down_left = Vector((-res_x / 2, -res_y / 2, 0))
# sqe_down_right = Vector((res_x / 2, -res_y / 2, 0))
