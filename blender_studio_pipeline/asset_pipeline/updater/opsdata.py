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
from ..asset_files import AssetPublish, AssetDir


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
        item_publish = item.asset_publishes.add()
        item_publish.update_props_by_asset_publish(publish)


def populate_context_with_imported_asset_colls(
    context: bpy.types.Context, asset_updater: AssetUpdater
) -> None:

    context.scene.bsp_asset.imported_asset_collections.clear()

    # Add asset publishes.
    for asset_coll in asset_updater.asset_collections:
        add_imported_asset_coll_to_context(context, asset_coll)
