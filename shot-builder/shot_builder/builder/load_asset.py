from shot_builder.builder.build_step import BuildStep
from shot_builder.asset import *
from shot_builder.project import *
from shot_builder.shot import *

import bpy

import logging

logger = logging.getLogger(__name__)


class LoadAssetStep(BuildStep):
    def __init__(self, production: Production, shot: Shot, asset: Asset):
        self.__asset = asset
        self.__production = production
        self.__shot = shot

    def __str__(self) -> str:
        return f"load asset \"{self.__asset.name}\""

    def execute(self) -> None:
        config = self.__asset.config
        assert(config)
        context = {
            "asset": self.__asset,
            "production": self.__production,
            "shot": self.__shot,
        }
        path = config.path.format(**context)
        collection = config.collection.format(**context)

        bpy.ops.wm.link(
            filepath=str(path),
            directory=str(path) + "/Collection",
            filename=collection,
        )

        # logger.info(f"loading asset {self._asset.name}")
        pass
