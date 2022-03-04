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

from typing import List, Dict, Union, Any, Set, Optional, Tuple, Callable
from pathlib import Path

import bpy

from ... import lib_util

logger = logging.getLogger("BSP")


class AssetUpdater:
    def __init__(self):
        self._asset_collections: Set[bpy.types.Collection] = set()

    def collect_asset_collections_in_scene(
        self, context: bpy.types.Context
    ) -> List[bpy.types.Collection]:
        """
        Collects all asset collections that have coll.bsp_asset.is_publish==True in current scene.
        Only collects them if they are linked in or library overwritten.
        """
        self._asset_collections.clear()

        for coll in context.scene.collection.children_recursive:

            # If item is not coming from a library: Skip.
            if lib_util.is_item_local(coll):
                continue

            if coll.bsp_asset.is_publish:
                self._asset_collections.add(coll)

    @property
    def asset_collections(self) -> Set[bpy.types.Collection]:
        return self._asset_collections

    def update_asset_collection_libpath(
        self, asset_collection: bpy.types.Collection, libpath: Path
    ) -> None:
        lib = lib_util.get_item_lib(asset_collection)
        bpy.ops.wm.lib_relocate(
            library=lib.name,
            directory=libpath.parent.as_posix(),
            filename=libpath.name,
        )
