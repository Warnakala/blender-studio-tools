from shot_builder.builder.build_step import BuildStep, BuildContext
from shot_builder.asset import *
from shot_builder.project import *
from shot_builder.shot import *
import pathlib

import bpy

import logging

logger = logging.getLogger(__name__)


class SaveFileStep(BuildStep):
    def __str__(self) -> str:
        return "save file"

    def execute(self, build_context: BuildContext) -> None:
        shot = build_context.shot
        file_path = pathlib.Path(shot.file_path)
        file_path.mkdir(parents=True, exist_ok=True)

        logger.info(f"save file {shot.file_path}")
        bpy.ops.wm.save_mainfile(filepath=shot.file_path)

        logger.debug(f"make paths relative")
        bpy.ops.file.make_paths_relative()
        logger.debug(f"save with relative paths")
        bpy.ops.wm.save_mainfile()
