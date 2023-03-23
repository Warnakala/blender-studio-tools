from shot_builder.builder.build_step import BuildStep, BuildContext
from shot_builder.asset import *
from shot_builder.project import *
from shot_builder.shot import *

import bpy

import logging

logger = logging.getLogger(__name__)


class InitShotStep(BuildStep):
    def __str__(self) -> str:
        return "init shot"

    def execute(self, build_context: BuildContext) -> None:
        shot = build_context.shot
        shot.file_path = shot.file_path_format.format_map(
            build_context.as_dict())
