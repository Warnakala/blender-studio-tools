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

from .context import BuildContext
from ..asset_files import AssetPublish
from . import suffix

logger = logging.getLogger("BSP")


class AssetImporter:
    """
    Class that handles the suffixing logic when importing another asset collection.
    """

    def __init__(self, build_context: BuildContext):
        self._build_context = build_context

    @property
    def build_context(self) -> BuildContext:
        return self._build_context

    def import_asset_task(self) -> None:
        """
        Imports that asset task that is stored in BuildContext.asset_task.
        Note: This function assumes it is run in an asset publish file.
        """

        # TODO: Add safety check to verify this function is not run in an
        # asset task. Maybe built context could receive a flag that we can check here?

        # TODO: In theroy nothing speaks against creating a new AssetPublish object here.
        # we could search it in self.build_context.asset_publishes but whats the point?
        asset_task = self.build_context.asset_task
        asset_publish = AssetPublish(Path(bpy.data.filepath))

        asset_coll_publish = self.build_context.asset_context.asset_collection
        asset_coll_name = asset_coll_publish.name

        # Make sure to suffix asset collection from current publish file.
        suffix.add_suffix_to_hierarchy(asset_coll_publish, asset_publish.data_suffix)

        # Import asset collection and all its dependencies from asset publish.
        with bpy.data.libraries.load(
            asset_task.path.as_posix(), relative=True, link=False
        ) as (
            data_from,
            data_to,
        ):
            # TODO: check for collisions
            data_to.collections.append(asset_coll_name)

        asset_coll_task = bpy.data.collections.get(asset_coll_name)
        suffix.add_suffix_to_hierarchy(asset_coll_task, asset_task.data_suffix)

        # TODO: Depending on what we choose as base we now need to either duplicate
        # asset_coll_task or _publish

    def import_asset_version(self) -> None:
        """
        Imports the latest asset publish.
        """
        # Get latest asset version.
        asset_publish = self.build_context.asset_publishes[-1]
        print(asset_publish)
        return
