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


logger = logging.getLogger("BSP")


class AssetUpdater:
    def __init__(self, context: bpy.types.Context):
        self._asset_collections: Set[bpy.types.Collection] = set()

        self.collect_asset_collections_in_scene(context)

    def collect_asset_collections_in_scene(
        self, context: bpy.types.Context
    ) -> List[bpy.types.Collection]:

        self._asset_collections.clear()

        # TODO: only load linked collections, check for that.
        for coll in context.scene.collection.children_recursive:
            if coll.bsp_asset.is_publish:
                self._asset_collections.add(coll)

    @property
    def asset_collections(self) -> Set[bpy.types.Collection]:
        return self._asset_collections
