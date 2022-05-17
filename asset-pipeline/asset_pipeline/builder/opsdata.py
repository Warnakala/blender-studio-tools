# ***** BEGIN GPL LICENSE BLOCK *****
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
# ***** END GPL LICENCE BLOCK *****
#
# (c) 2021, Blender Foundation - Paul Golter

import logging

from typing import List, Dict, Union, Any, Set, Optional, Tuple
from pathlib import Path

import bpy

from .context import AssetContext, BuildContext
from .task_layer import TaskLayer
from .lock_plan import TaskLayerLockPlan

from .. import builder
from ..asset_files import AssetPublish

logger = logging.getLogger("BSP")


def populate_task_layers(
    context: bpy.types.Context, asset_context: AssetContext
) -> None:

    for prop_group in [
        context.scene.bsp_asset.task_layers_push,
        context.scene.bsp_asset.task_layers_pull,
    ]:
        # Make a backup to restore task layer settings as good as possible.
        tmp_backup: Dict[str, Dict[str, Any]] = {}
        for (
            task_layer_id,
            task_layer_prop_group,
        ) in prop_group.items():
            tmp_backup[task_layer_id] = task_layer_prop_group.as_dict()

        # Clear task layer collection property.
        prop_group.clear()

        # Load Task Layers from Production Context, try to restore
        # previous task layer settings
        for (
            key,
            task_layer_config,
        ) in asset_context.task_layer_assembly.task_layer_config_dict.items():
            item = prop_group.add()
            item.name = key
            item.task_layer_id = key
            item.task_layer_name = task_layer_config.task_layer.name

            # Restore previous settings.
            if key in tmp_backup:
                item.use = tmp_backup[key]["use"]

                # Update actual ASSET_CONTEXT, which will transfer the task layer settings,
                # which we restored from scene level.
                task_layer_config.use = tmp_backup[key]["use"]


def add_asset_publish_to_context(
    context: bpy.types.Context, asset_publish: AssetPublish
) -> None:

    item = context.scene.bsp_asset.asset_publishes.add()
    item.update_props_by_asset_publish(asset_publish)


def update_asset_publishes_by_build_context(
    context: bpy.types.Context, build_context: BuildContext
) -> None:

    for asset_publish in build_context.asset_publishes:
        item = context.scene.bsp_asset.asset_publishes.get(asset_publish.path.name)
        if item:
            item.update_props_by_asset_publish(asset_publish)


def populate_asset_publishes_by_asset_context(
    context: bpy.types.Context, asset_context: AssetContext
) -> None:

    """
    This populates the context with asset publishes based on the asset context.
    Meaning it will take all found asset publishes (asset_context.asset_publishes).
    """

    # Clear asset_publishes collection property.
    clear_asset_publishes(context)

    # Load Asset Publishes from Asset Context.
    for asset_publish in asset_context.asset_publishes:
        add_asset_publish_to_context(context, asset_publish)


def populate_asset_publishes_by_build_context(
    context: bpy.types.Context, build_context: BuildContext
) -> None:
    """
    This populates the context with asset publishes based on the build context.
    Meaning it will only take the asset publishes it will find in
    build_context.process_pairs.
    """

    # Clear asset_publishes collection property.
    clear_asset_publishes(context)

    # Load Asset Publishes from Asset Context.
    for process_pair in build_context.process_pairs:
        asset_publish = process_pair.asset_publish
        add_asset_publish_to_context(context, asset_publish)


def clear_task_layers(context: bpy.types.Context) -> None:
    context.scene.bsp_asset.task_layers_push.clear()
    context.scene.bsp_asset.task_layers_pull.clear()


def clear_task_layer_lock_plans(context: bpy.types.Context) -> None:
    context.scene.bsp_asset.task_layer_lock_plans.clear()


def clear_asset_publishes(context: bpy.types.Context) -> None:
    context.scene.bsp_asset.asset_publishes.clear()


def get_active_asset_publish(context: bpy.types.Context) -> AssetPublish:
    index = context.scene.bsp_asset.asset_publishes_index
    asset_file = context.scene.bsp_asset.asset_publishes[index]
    return AssetPublish(asset_file.path)


def get_task_layers_for_bl_enum(
    self: bpy.types.Operator, context: bpy.types.Context
) -> List[Tuple[str, str, str]]:
    if not builder.ASSET_CONTEXT:
        return []
    return builder.ASSET_CONTEXT.task_layer_assembly.get_task_layers_for_bl_enum()


def get_task_layer_lock_plans(asset_context: AssetContext) -> List[TaskLayerLockPlan]:

    """
    This function should be called when you want to know which task layers of which asset publishes
    need to be locked after creating a new asset publish with a selection of task layers.
    This information will be returned in the form of a List of TaskLayerLockPlan classes.
    """

    task_layer_lock_plans: List[TaskLayerLockPlan] = []
    task_layers_to_push = asset_context.task_layer_assembly.get_used_task_layers()

    for asset_publish in asset_context.asset_publishes[:-1]:

        task_layers_to_lock: List[TaskLayer] = []

        for task_layer in task_layers_to_push:

            # This is an interesting case, that means the task layer is not even in the assset publish
            # metadata file. Could happen if there was a new production task layer added midway production.
            if task_layer.get_id() not in asset_publish.metadata.get_task_layer_ids():
                # TODO: How to handle this case?
                logger.warning(
                    "TaskLayer: %s does not exist in %s. Maybe added during production?",
                    task_layer.get_id(),
                    asset_publish.metadata_path.name,
                )
                continue

            # Task Layer is already locked.
            if (
                task_layer.get_id()
                in asset_publish.metadata.get_locked_task_layer_ids()
            ):
                continue

            # Otherwise this Task Layer should be locked.
            task_layers_to_lock.append(task_layer)

        # If task layers need to be locked
        # Store that in TaskLayerLockPlan.
        if task_layers_to_lock:
            task_layer_lock_plans.append(
                TaskLayerLockPlan(asset_publish, task_layers_to_lock)
            )

    return task_layer_lock_plans


def populate_context_with_lock_plans(
    context: bpy.types.Context, lock_plan_list: List[TaskLayerLockPlan]
) -> None:

    context.scene.bsp_asset.task_layer_lock_plans.clear()

    # Add asset publishes.
    for lock_plan in lock_plan_list:
        item = context.scene.bsp_asset.task_layer_lock_plans.add()
        item.path_str = lock_plan.asset_publish.path.as_posix()

        # Add task layers to lock for that asset publish.
        for tl_to_lock in lock_plan.task_layers_to_lock:
            tl_item = item.task_layers.add()
            tl_item.name = tl_to_lock.get_id()
            tl_item.task_layer_id = tl_to_lock.get_id()
            tl_item.task_layer_name = tl_to_lock.name


def are_any_task_layers_enabled_push(context: bpy.types.Context) -> bool:
    """
    Returns true if any task layers are selected in the task layer push list.
    """
    bsp = context.scene.bsp_asset
    enabled_task_layers = [
        tlg for tlg in bsp.task_layers_push.values() if tlg.use
    ]
    return bool(enabled_task_layers)