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

from .asset_updater import AssetUpdater

from ..asset_files import AssetPublish
from ..asset_status import AssetStatus


logger = logging.getLogger("BSP")


def add_imported_asset_coll_to_context(
    context: bpy.types.Context, asset_coll: bpy.types.Collection
) -> None:

    asset_publish: AssetPublish = asset_coll.bsp_asset.get_asset_publish()

    # Add item.
    item = context.scene.bsp_asset.imported_asset_collections.add()

    # Set collection property.
    item.collection = asset_coll

    # Collect all publishes on disk for that asset collection.
    asset_dir = asset_publish.asset_dir
    for publish in asset_dir.get_asset_publishes():

        # Dont' offer asset publishes that are still in review.
        # But still append the current imported version (if its in review state)
        if (
            publish.metadata.meta_asset.status == AssetStatus.REVIEW
            and asset_publish != publish
        ):
            logger.debug(
                "Asset-Updater: %s skip %s as status is %s",
                asset_publish.metadata.meta_asset.name,
                publish.path.name,
                AssetStatus.REVIEW.name,
            )
            continue

        item_publish = item.asset_publishes.add()
        item_publish.update_props_by_asset_publish(publish)
        logger.debug(
            "Asset-Updater: %s found: %s",
            asset_publish.metadata.meta_asset.name,
            publish.path.name,
        )

    # Set enum property to latest version.
    if item.asset_publishes:
        item.target_publish = item.asset_publishes[-1].name


def populate_context_with_imported_asset_colls(
    context: bpy.types.Context, asset_updater: AssetUpdater
) -> None:
    def sorting_keys(coll: bpy.types.Collection) -> Tuple[bool, str]:
        """
        This sorting functions moves assets that are deprecated to the top and sorts
        the rest of the collections in alphabetical order.
        """
        asset_publish: AssetPublish = coll.bsp_asset.get_asset_publish()
        return (
            asset_publish.metadata.meta_asset.status != AssetStatus.DEPRECATED,
            coll.name,
        )

    context.scene.bsp_asset.imported_asset_collections.clear()

    asset_collections = sorted(asset_updater.asset_collections, key=sorting_keys)
    # Add asset publishes.
    for asset_coll in asset_collections:
        add_imported_asset_coll_to_context(context, asset_coll)
