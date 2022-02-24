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

from .builder.context import AssetContext, BuildContext
from . import builder
from .asset_files import AssetPublish

logger = logging.getLogger("BSP")


def populate_task_layers(
    context: bpy.types.Context, asset_context: AssetContext
) -> None:
    # Make a backup to restore task layer settings as good as possible.
    tmp_backup: Dict[str, Dict[str, Any]] = {}
    for (
        task_layer_id,
        task_layer_prop_group,
    ) in context.scene.bsp_asset.task_layers.items():
        tmp_backup[task_layer_id] = task_layer_prop_group.as_dict()

    # Clear task layer collection property.
    clear_task_layers(context)

    # Load Task Layers from Production Context, try to restore
    # previous task layer settings
    for (
        key,
        task_layer_config,
    ) in asset_context.task_layer_assembly.task_layer_config_dict.items():
        item = context.scene.bsp_asset.task_layers.add()
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
    metadata = asset_publish.metadata

    item = context.scene.bsp_asset.asset_publishes.add()
    item.name = asset_publish.path.name
    item.path_str = asset_publish.path.as_posix()

    # Use name attribute.
    item.status = metadata.meta_asset.status.name

    # Create a task layer item for each asset file,
    # so we can display the task layer state of each
    # asset file in the UI.
    for tl in metadata.meta_task_layers:
        item.add_task_layer_from_metaclass(tl)


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
    context.scene.bsp_asset.task_layers.clear()


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
