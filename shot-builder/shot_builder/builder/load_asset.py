from shot_builder.builder.build_step import BuildStep, BuildContext
from shot_builder.asset import *
from shot_builder.project import *
from shot_builder.shot import *

import bpy

import logging

logger = logging.getLogger(__name__)


class LoadAssetStep(BuildStep):
    def __init__(self, asset: Asset):
        self.__asset = asset

    def __str__(self) -> str:
        return f"load asset \"{self.__asset.name}\""

    def execute(self, build_context: BuildContext) -> None:
        config = self.__asset.config
        assert(config)
        build_context.asset = self.__asset
        path = config.path.format(**build_context.as_dict())
        collection = config.collection.format(**build_context.as_dict())

        bpy.ops.wm.link(
            filepath=str(path),
            directory=str(path) + "/Collection",
            filename=collection,
        )
