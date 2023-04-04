from blender_kitsu.shot_builder.project import Production
from blender_kitsu.shot_builder.task_type import TaskType
from blender_kitsu.shot_builder.asset import Asset, AssetRef
from blender_kitsu.shot_builder.builder.build_step import BuildStep, BuildContext
from blender_kitsu.shot_builder.builder.init_asset import InitAssetStep
from blender_kitsu.shot_builder.builder.init_shot import InitShotStep
from blender_kitsu.shot_builder.builder.set_render_settings import SetRenderSettingsStep
from blender_kitsu.shot_builder.builder.new_scene import NewSceneStep
from blender_kitsu.shot_builder.builder.invoke_hook import InvokeHookStep
from blender_kitsu.shot_builder.builder.save_file import SaveFileStep

import bpy

import typing
import logging

logger = logging.getLogger(__name__)


class ShotBuilder:
    def __init__(self, context: bpy.types.Context, production: Production, task_type: TaskType, shot_name: str):
        self._steps: typing.List[BuildStep] = []

        shot = production.get_shot(context, shot_name)
        assert(shot)
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
        self._steps.append(InitShotStep())
        self._steps.append(NewSceneStep())
        self._steps.append(SetRenderSettingsStep())

        production = self.build_context.production
        task_type = self.build_context.task_type

        # Add global hooks.
        for hook in production.hooks.filter():
            self._steps.append(InvokeHookStep(hook))

        # Add task specific hooks.
        for hook in production.hooks.filter(match_task_type=task_type.name):
            self._steps.append(InvokeHookStep(hook))

        context = self.build_context.context
        shot = self.build_context.shot

        # Collect assets that should be loaded.
        asset_refs = production.get_assets_for_shot(context, shot)
        assets = []
        for asset_ref in asset_refs:
            asset = self.__find_asset(asset_ref)
            if asset is None:
                logger.warning(
                    f"cannot determine repository data for {asset_ref}")
                continue
            assets.append(asset)

        # Sort the assets on asset_type and asset.code).
        assets.sort(key=lambda asset: (asset.asset_type, asset.code))

        # Build asset specific build steps.
        for asset in assets:
            self._steps.append(InitAssetStep(asset))
            # Add asset specific hooks.
            for hook in production.hooks.filter(match_task_type=task_type.name, match_asset_type=asset.asset_type):
                self._steps.append(InvokeHookStep(hook))

        self._steps.append(SaveFileStep())

    def build(self) -> None:
        num_steps = len(self._steps)
        step_number = 1
        build_context = self.build_context
        window_manager = build_context.context.window_manager
        window_manager.progress_begin(min=0, max=num_steps)
        for step in self._steps:
            logger.info(f"Building step [{step_number}/{num_steps}]: {step} ")
            step.execute(build_context=build_context)
            window_manager.progress_update(value=step_number)
            step_number += 1
        window_manager.progress_end()
