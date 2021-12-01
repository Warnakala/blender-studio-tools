from typing import List, Dict, Tuple, Union, Any, Optional, Set
from pathlib import Path

import bpy
import gpu
import bgl
import gpu_extras.presets
from mathutils import Matrix

from media_viewer import gpu_opsdata
from media_viewer import opsdata
from media_viewer.log import LoggerFactory

logger = LoggerFactory.getLogger(name=__name__)


class MV_OT_render_img_with_annotation(bpy.types.Operator):

    bl_idname = "media_viewer.render_img_with_annotation"
    bl_label = "Render Image with Annotation"
    bl_description = (
        "Renders out active image with annotations on top"
        "Uses custom openGL rendering"
    )

    def execute(self, context: bpy.types.Context) -> Set[str]:

        # Check if image editor area available.
        area = opsdata.find_area(context, "IMAGE_EDITOR")
        if not area:
            logger.error("Failed to render image. No Image Editor area available.")
            return {"CANCELLED"}

        # Get active image that is loaded in the image editor.
        image: bpy.types.Image = area.spaces.active.image
        width = int(image.size[0])
        height = int(image.size[1])

        # Get output path for rendering.
        media_filepath = Path(bpy.path.abspath(image.filepath))
        review_output_dir = Path(context.window_manager.media_viewer.review_output_dir)
        output_path: Path = opsdata.get_review_output_path(
            review_output_dir, media_filepath
        )
        # Overwrite suffix to be .jpg.
        output_path = output_path.parent.joinpath(f"{output_path.stem}.jpg")

        # Reading image dimensions is not supported for multilayer EXRs
        # https://developer.blender.org/T53768
        # Workaround:
        # If exr image, and multilayer connect it to the viewer node
        # so we can read the size from bpy.data.images["Viewer Node"]
        # Edit: This workaround does not work because of:
        # https://developer.blender.org/T54314
        # The workaround of the workaround would be to write out the image and then
        # read the resolution of the jpg.
        if (
            Path(image.filepath).suffix == ".exr"
        ):  # Could also be: image.file_format == "OPEN_EXR"
            if image.type == "MULTILAYER":  # Single layer is: IMAGE

                tmp_res_path = output_path.parent.joinpath(
                    f"{output_path.stem}_tmp.jpg"
                )
                image.save_render(tmp_res_path.as_posix())
                tmp_image = bpy.data.images.load(tmp_res_path.as_posix())

                # Read resolution from 'Viewer Node' image databablock.
                width = int(tmp_image.size[0])
                height = int(tmp_image.size[1])

                # Delete image again.
                bpy.data.images.remove(tmp_image)
                tmp_res_path.unlink(missing_ok=True)

        # Load image in to an OpenGL texture, will give us image.bindcode that we will later use
        # in gpu_extras.presets.draw_texture_2d()
        # Note: Colors read from the texture will be in scene linear color space
        pass_idx = area.spaces.active.image_user.multilayer_pass
        layer_idx = area.spaces.active.image_user.multilayer_layer
        print(f"Loading image (layer: {layer_idx}, pass: {pass_idx}")
        image.gl_load(
            frame=0, layer_idx=layer_idx, pass_idx=pass_idx
        )  # TODO: Image sequence

        # Create new image datablack to save our newly composited image
        # (source image + annotation) to.
        new_image = bpy.data.images.new(
            f"{image.name}_annotated", width, height, float_buffer=True
        )

        # Create a Buffer on GPU that will be used to first render the image into,
        # then the annotation.

        # We can't user gpu.types.GPUOffscreen() here because the depth is not enough.
        # This leads to banding issues.
        # Instead we create a GPUFramebuffer(). Here we can use a GPUTexture with
        # the format="RGBA16F" which solves most of the banding.
        gpu_texture = gpu.types.GPUTexture((width, height), format="RGBA16F")
        frame_buffer = gpu.types.GPUFrameBuffer(color_slots={"texture": gpu_texture})

        # TODO: always writes out first layer unaffected from what is selected in the image editor

        with frame_buffer.bind():

            # Debugging: Flood image with color.
            # bgl.glClearColor(0, 1, 0, 1)
            # bgl.glClear(bgl.GL_COLOR_BUFFER_BIT)

            with gpu.matrix.push_pop():
                # Our drawing is not in the right place, we need to use
                # a projection matrix to transform it.
                # This matrix scales it up twice and centers it (starts out in the top right
                # corner)
                mat = Matrix(
                    (
                        (2.0, 0.0, 0.0, -1.0),
                        (0.0, 2.0, 0.0, -1.0),
                        (0.0, 0.0, 1.0, 0.0),
                        (0.0, 0.0, 0.0, 1.0),
                    )
                )
                gpu.matrix.load_matrix(Matrix.Identity(4))
                gpu.matrix.load_projection_matrix(mat)

                # Draw the texture.
                gpu_extras.presets.draw_texture_2d(image.bindcode, (0, 0), 1, 1)

                # Draw grease pencil over it.
                gp_drawer = gpu_opsdata.GPDrawerCustomShader()
                gpu_opsdata.draw_callback(gp_drawer)

            # Create the buffer with dimensions: r, g, b, a (width * height * 4)
            # Make sure that we use bgl.GL_FLOAT as this solves the colorspace issue
            # that the saved image would be in linear space. (?)
            buffer = bgl.Buffer(bgl.GL_FLOAT, width * height * 4)
            bgl.glReadBuffer(bgl.GL_BACK)
            bgl.glReadPixels(0, 0, width, height, bgl.GL_RGBA, bgl.GL_FLOAT, buffer)

            # new_image.scale(width, height) does not seem to do a difference?
            # Set new_image.pixels to the composited buffer.
            new_image.pixels = [v for v in buffer]

            # Save image to disk.
            # TODO: colorspace seems to be slightly off
            # if Path(image.filepath).suffix == ".exr":
            #     )
            #     # new_image.use_view_as_render = True
            #     area.spaces.active.image = image
            # else:
            #      new_image.save_render(output_path)

            new_image.save_render(output_path.as_posix())

        print(f"Saved new image({width}:{height}) to {output_path.as_posix()}")

        return {"FINISHED"}


# ---------REGISTER ----------.

classes = [MV_OT_render_img_with_annotation]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


# OLDER APPROACHES FOR REFERENCE:
# We get an error from bgl.Buffer() that dimension must be between 1-255
# Question: Can this be solved without having to write out the image like this?
# if Path(image.filepath).suffix == ".exr":
#     old_image = image
#     filepath = "/tmp/convert.png"
#     # TODO: messes up topbar dropdown menu, maybe trigger redraw?
#     bpy.ops.image.save_as(
#         {"area": area}, filepath=filepath, save_as_render=False
#     )

#     print("Exported convert image")
#     image = bpy.data.images.load(filepath, check_existing=False)
#     area.spaces.active.image = old_image
#     area.tag_redraw()  # Does not solve mess up of topbar


# Also taking in to account: The image.gl_load() function
# Colors read from the texture will be in scene linear color space
# --> We need to convert them from lin to srgb
# print(list(buffer))


# # Startupblend contains image node connected to viewer node.
# image_node = context.scene.node_tree.nodes["Image"]
# viewer_node = context.scene.node_tree.nodes["Viewer"]

# # This might reset connection to viewer node.
# print(f"Assigning image({image}) to image node ({image_node})")
# image_node.image = image

# # Connect to image viewer to first output of image node.
# context.scene.node_tree.links.new(
#     viewer_node.inputs["Image"], image_node.outputs.values()[0]
# )
