from blender_kitsu.shot_builder.builder.build_step import BuildStep, BuildContext
import bpy

import typing
import logging

logger = logging.getLogger(__name__)


class SetRenderSettingsStep(BuildStep):
    def __str__(self) -> str:
        return f"set render settings"

    def execute(self, build_context: BuildContext) -> None:
        scene = typing.cast(bpy.types.Scene, build_context.scene)
        render_settings = build_context.render_settings
        logger.debug(
            f"set render resolution to {render_settings.width}x{render_settings.height}")
        scene.render.resolution_x = render_settings.width
        scene.render.resolution_y = render_settings.height
        scene.render.resolution_percentage = 100

        shot = build_context.shot
        scene.frame_start = shot.frame_start
        scene.frame_current = shot.frame_start
        scene.frame_end = shot.frame_start + shot.frames -1
        logger.debug(f"set frame range to ({scene.frame_start}-{scene.frame_end})")
