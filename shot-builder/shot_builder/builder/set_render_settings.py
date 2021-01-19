from shot_builder.builder.build_step import BuildStep, BuildContext
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
