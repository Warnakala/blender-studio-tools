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
import uuid
from typing import List, Dict, Union, Any, Set, Optional, Tuple
from pathlib import Path

import bpy

from .context import BuildContext
from ..asset_files import AssetPublish
from . import asset_suffix
from .. import constants

logger = logging.getLogger("BSP")


class FileExistsError(Exception):
    pass


class ImportFailed(Exception):
    pass


def import_data_from_lib(
    libpath: Path,
    data_category: str,
    data_name: str,
    link: bool = False,
) -> Any:

    noun = "Appended"
    if link:
        noun = "Linked"

    with bpy.data.libraries.load(libpath.as_posix(), relative=True, link=link) as (
        data_from,
        data_to,
    ):

        if data_name not in eval(f"data_from.{data_category}"):
            raise ImportFailed(
                f"Failed to import {data_category} {data_name} from {libpath.as_posix()}. Doesn't exist in file.",
            )

        # Check if datablock with same name already exists in blend file.
        try:
            eval(f"bpy.data.{data_category}['{data_name}']")
        except KeyError:
            pass
        else:
            raise ImportFailed(
                f"{data_name} already in bpy.data.{data_category} of this blendfile.",
            )

        # Append data block.
        eval(f"data_to.{data_category}.append('{data_name}')")
        logger.info(
            "%s: %s from library: %s",
            noun,
            data_name,
            libpath.as_posix(),
        )

    if link:
        return eval(
            f"bpy.data.{data_category}['{data_name}', '{bpy.path.relpath(libpath.as_posix())}']"
        )

    return eval(f"bpy.data.{data_category}['{data_name}']")


class AssetImporter:
    """
    Class that handles the suffixing logic when importing another asset collection.
    """

    def __init__(self, build_context: BuildContext):
        self._build_context = build_context

    @property
    def build_context(self) -> BuildContext:
        return self._build_context

    def _duplicate_tmp_blendfile(self) -> Path:
        # Gen a UUID to minimize risk of overwriting an existing blend file.
        id = uuid.uuid4()
        filepath_tmp = Path(bpy.data.filepath)
        print(filepath_tmp)
        filepath_tmp = filepath_tmp.parent / f"{filepath_tmp.stem}-{id}.blend"

        if filepath_tmp.exists():
            raise FileExistsError(
                f"Failed to duplicate blend file. Path already exists: {filepath_tmp.as_posix()}"
            )

        # Duplicate blend file by saving it in filepath_tmp.
        bpy.ops.wm.save_as_mainfile(filepath=filepath_tmp.as_posix(), copy=True)

        logger.debug("Created temporary duplicate: %s", filepath_tmp.name)

        return filepath_tmp

    def _import_coll_with_suffix(
        self, libpath: Path, coll_name: str, coll_suffix: str
    ) -> bpy.types.Collection:

        coll = import_data_from_lib(libpath, "collections", coll_name)
        asset_suffix.add_suffix_to_hierarchy(coll, coll_suffix)
        return coll

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

        # We now need to either duplicate the asset task or publish collection
        # depending on which one is going to be the base. To make this decision we should look
        # at the enabled TaskLayers in the build context and then check the 'order' attribute of TaskLayers
        # if the asset task collection contains a task layer with the lowest order we have to take that as
        # a base.
        orders_prod: List[int] = self.build_context.prod_context.get_task_layer_orders()
        orders_asset_task: List[
            int
        ] = self.build_context.asset_context.task_layer_assembly.get_task_layer_orders(
            only_used=True
        )

        # If the smallest order of the asset task is equal the smallest order or prod orders
        # We know that we need to take the collection of the asset task as a new base.

        # BASE --> ASSET_TASK COLLECTION
        if min(orders_asset_task) == min(orders_prod):

            logger.info("Take Asset Task as Base: %s", asset_task.path.name)

            # Suffix asset_publish collection with .PUBLISH
            asset_suffix.add_suffix_to_hierarchy(
                asset_coll_publish, constants.PUBLISH_SUFFIX
            )

            # Import asset task collection with .TASK suffix.
            asset_coll_task = self._import_coll_with_suffix(
                asset_task.path, asset_coll_name, constants.TASK_SUFFIX
            )

            # Import asset_task collection again and suffix as .TARGET
            asset_coll_target = self._import_coll_with_suffix(
                asset_task.path, asset_coll_name, constants.TARGET_SUFFIX
            )

        # BASE --> ASSET_PUBLISH COLLECTION
        else:

            logger.info("Take Asset Publish as Base: %s", asset_publish.path.name)

            # Make tmp blendfile.
            # This is a little tricks that prevents us from having to duplicate the whole
            # Collection hierarchy and deal with annoyin .001 suffixes.
            # That way we can first suffix the asset publish collection and then import it again.
            tmp_blendfile_path = self._duplicate_tmp_blendfile()

            # Suffix asset_publish collection with .PUBLISH.
            asset_suffix.add_suffix_to_hierarchy(
                asset_coll_publish, constants.PUBLISH_SUFFIX
            )

            # Import asset task collection with .TASK suffix.
            asset_coll_task = self._import_coll_with_suffix(
                asset_task.path, asset_coll_name, constants.TASK_SUFFIX
            )

            # Import asset_publish collection from tmp blend file and suffix as .TARGET
            asset_coll_target = self._import_coll_with_suffix(
                tmp_blendfile_path, asset_coll_name, constants.TARGET_SUFFIX
            )

        # Link for debugging.
        bpy.context.scene.collection.children.link(asset_coll_publish)
        bpy.context.scene.collection.children.link(asset_coll_target)
        bpy.context.scene.collection.children.link(asset_coll_task)

        # Remove tmp blend file.
        tmp_blendfile_path.unlink()

    def import_asset_version(self) -> None:
        """
        Imports the latest asset publish.
        """
        # Get latest asset version.
        asset_publish = self.build_context.asset_publishes[-1]
        return
