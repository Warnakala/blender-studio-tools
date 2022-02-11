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

from .context import ProductionContext, AssetContext, BuildContext

logger = logging.getLogger("BSP")


class AssetBuilderFailedToInitialize(Exception):
    pass


class AssetBuilder:
    def __init__(self, build_context: BuildContext):
        if not build_context:
            raise AssetBuilderFailedToInitialize(
                "Failed to initialize AssetBuilder. Build_context not valid."
            )

        self._build_context = build_context

    def build(self) -> None:

        # Catch special case first version.
        if self._build_context._is_first_publish:
            self._create_first_version()
            return

    def _create_first_version(self) -> None:
        target = self._build_context.process_pairs[0].target
        asset_coll = self._build_context.asset_context.asset_collection
        # with bpy.data.libraries.load(target.as_posix(), relative=True, link=False) as (
        #     data_from,
        #     data_to,
        # ):
        #     data_to.collections.append(asset_coll.name)
        data_blocks = set((asset_coll,))

        # Create directory if not exist.
        target.parent.mkdir(parents=True, exist_ok=True)

        bpy.data.libraries.write(
            target.as_posix(), data_blocks, path_remap="RELATIVE_ALL", fake_user=True
        )
        logger.info("Created first asset version: %s", target.as_posix())
