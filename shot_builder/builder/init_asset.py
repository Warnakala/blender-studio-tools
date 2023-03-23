from shot_builder.builder.build_step import BuildStep, BuildContext
from shot_builder.asset import *
from shot_builder.project import *
from shot_builder.shot import *

import bpy

import logging

logger = logging.getLogger(__name__)


class InitAssetStep(BuildStep):
    def __init__(self, asset: Asset):
        self.__asset = asset

    def __str__(self) -> str:
        return f"init asset \"{self.__asset.name}\""

    def execute(self, build_context: BuildContext) -> None:
        build_context.asset = self.__asset
        self.__asset.path = self.__asset.path.format_map(build_context.as_dict())
        self.__asset.collection = self.__asset.collection.format_map(build_context.as_dict())
