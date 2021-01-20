from shot_builder.project import Production
from shot_builder.task_type import TaskType
from shot_builder.asset import Asset, AssetRef
from shot_builder.builder.build_step import BuildStep, BuildContext
from shot_builder.builder.load_asset import LoadAssetStep
from shot_builder.builder.set_render_settings import SetRenderSettingsStep
from shot_builder.builder.new_scene import NewSceneStep
from shot_builder.builder.invoke_hook import InvokeHookStep

import bpy

import typing
import logging

logger = logging.getLogger(__name__)


class ShotBuilder():
    def __init__(self, context: bpy.types.Context, production: Production, task_type: TaskType, shot_id: str):
        self._steps: typing.List[BuildStep] = []

        shot = production.get_shot(context, shot_id)
        render_settings = production.get_render_settings(
            context, shot)
        self.build_context = BuildContext(
            context=context, production=production, shot=shot, render_settings=render_settings, task_type=task_type)

    def __find_asset(self, asset_ref: AssetRef) -> typing.Optional[Asset]:
        for asset_class in self.build_context.production.assets:
            asset = typing.cast(Asset, asset_class())
            logger.debug(f"{asset_ref.name}, {asset.name}")
            if asset_ref.name == asset.name:
                return asset
        return None

    def create_build_steps(self) -> None:
        self._steps.append(NewSceneStep())
        self._steps.append(SetRenderSettingsStep())

        production = self.build_context.production
        for hook in production.hooks.filter(is_global=True):
            self._steps.append(InvokeHookStep(hook))

        context = self.build_context.context
        shot = self.build_context.shot

        asset_refs = production.get_assets_for_shot(context, shot)
        for asset_ref in asset_refs:
            asset = self.__find_asset(asset_ref)
            if asset is None:
                logger.warning(f"cannot determine repository data for {asset}")
                continue
            self._steps.append(LoadAssetStep(asset))

    def build(self) -> None:
        num_steps = len(self._steps)
        step_number = 1
        build_context = self.build_context
        for step in self._steps:
            logger.info(f"Building step: {step} [{step_number}/{num_steps}]")
            step.execute(build_context=build_context)
            step_number += 1
