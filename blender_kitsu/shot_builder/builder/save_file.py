from blender_kitsu.shot_builder.builder.build_step import BuildStep, BuildContext
from blender_kitsu.shot_builder.asset import *
from blender_kitsu.shot_builder.project import *
from blender_kitsu.shot_builder.shot import *
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
        bpy.ops.wm.save_mainfile(filepath=shot.file_path, relative_remap=True)
