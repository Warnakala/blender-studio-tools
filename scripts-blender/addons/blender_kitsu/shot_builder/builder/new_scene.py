from blender_kitsu.shot_builder.builder.build_step import BuildStep, BuildContext
from blender_kitsu.shot_builder.render_settings import RenderSettings
import bpy

import logging

logger = logging.getLogger(__name__)


class NewSceneStep(BuildStep):
    def __str__(self) -> str:
        return f"new scene"

    def execute(self, build_context: BuildContext) -> None:
        production = build_context.production
        scene_name = production.scene_name_format.format_map(
            build_context.as_dict())
        logger.debug(f"create scene with name {scene_name}")
        scene = bpy.data.scenes.new(name=scene_name)

        bpy.context.window.scene = scene
        build_context.scene = scene

        self.__remove_other_scenes(build_context)

    def __remove_other_scenes(self, build_context: BuildContext) -> None:
        for scene in bpy.data.scenes:
            if scene != build_context.scene:
                logger.debug(f"remove scene {scene.name}")
                bpy.data.scenes.remove(scene)
