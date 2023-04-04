import bpy
import typing

from blender_kitsu.shot_builder.project import Production
from blender_kitsu.shot_builder.shot import Shot
from blender_kitsu.shot_builder.task_type import TaskType
from blender_kitsu.shot_builder.render_settings import RenderSettings
from blender_kitsu.shot_builder.asset import Asset


class BuildContext:
    def __init__(self, context: bpy.types.Context, production: Production, shot: Shot, render_settings: RenderSettings, task_type: TaskType):
        self.context = context
        self.production = production
        self.shot = shot
        self.task_type = task_type
        self.render_settings = render_settings
        self.asset: typing.Optional[Asset] = None
        self.scene: typing.Optional[bpy.types.Scene] = None

    def as_dict(self) -> typing.Dict[str, typing.Any]:
        return {
            'context': self.context,
            'scene': self.scene,
            'production': self.production,
            'shot': self.shot,
            'task_type': self.task_type,
            'render_settings': self.render_settings,
            'asset': self.asset,
        }


class BuildStep:
    def __str__(self) -> str:
        return "unnamed build step"

    def execute(self, build_context: BuildContext) -> None:
        raise NotImplementedError()
