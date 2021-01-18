from shot_builder.project import Production
from shot_builder.builder.build_step import BuildStep
from shot_builder.builder.load_asset import LoadAssetStep
import bpy

import typing
import logging

logger = logging.getLogger(__name__)


class ShotBuilder():
    def __init__(self, context: bpy.types.Context, production: Production, shot_id: str):
        self._context = context
        self._production = production
        self._shot_id = shot_id
        self._steps: typing.List[BuildStep] = []

    def create_build_steps(self) -> None:
        shot = self._production.get_shot(self._context, self._shot_id)
        assets = self._production.get_assets_for_shot(self._context, shot)
        for asset in assets:
            self._production.update_asset_definition(asset)
            if asset.config is None:
                logger.warning(f"cannot determine repository data for {asset}")
                continue
            self._steps.append(LoadAssetStep(self._production, shot, asset))

    def build(self) -> None:
        num_steps = len(self._steps)
        step_number = 1
        for step in self._steps:
            logger.info(f"Building step: {step} [{step_number}/{num_steps}]")
            step.execute()
            step_number += 1
