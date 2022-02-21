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
import pickle
import logging

from typing import List, Dict, Union, Any, Set, Optional, Tuple
from pathlib import Path

import bpy

from .context import BuildContext
from ..asset_files import AssetTask, AssetPublish
from .asset_importer import AssetImporter
from .asset_mapping import TransferCollectionTriplet, AssetTransferMapping
from .blstarter import BuilderBlenderStarter
from .vis import EnsureVisible
from ... import util
from . import asset_suffix
from . import metadata
from .metadata import AssetMetadataTree, MetadataAsset, MetaDataTaskLayer
from . import meta_util

logger = logging.getLogger("BSP")


class AssetBuilderFailedToInitialize(Exception):
    pass


class AssetBuilderFailedToPull(Exception):
    pass


class AssetBuilderFailedToPublish(Exception):
    pass


class AssetBuilder:
    def __init__(self, build_context: BuildContext):
        if not build_context:
            raise AssetBuilderFailedToInitialize(
                "Failed to initialize AssetBuilder. Build_context not valid."
            )

        self._build_context = build_context
        self._asset_importer = AssetImporter(self._build_context)
        self._transfer_settings = bpy.context.scene.bsp_asset_transfer_settings

    @property
    def build_context(self) -> BuildContext:
        return self._build_context

    @property
    def asset_importer(self) -> AssetImporter:
        return self._asset_importer

    @property
    def transfer_settings(self) -> bpy.types.PropertyGroup:
        return self._transfer_settings

    def push(self) -> None:
        # Catch special case first version.
        if not self.build_context.asset_publishes:
            self._create_first_version()
            return

        # Normal publish process.

        # No here it gets a little tricky. We cannot just simply
        # perform a libraries.write() operation. The merge process
        # requires additional operations to happen so we need to actually
        # open the asset version blend file and perform them.

        # Now we already assembled this huge BuildContext, in which we have
        # all the information we need for whatever needs to be done.
        # The question is how can we share this info with the new Blender Instance
        # that knows nothing about it.

        # A very effective and easy ways seems to be pickling the BuildContext
        # and unpickling  it in the new Blender Instance again.
        # Some objects cannot be pickled (like the blender context or a collection)
        # (We can add custom behavior to work around this please see: ./context.py)

        for process_pair in self.build_context.process_pairs:

            asset_publish = process_pair.asset_publish

            logger.info("Processing %s", asset_publish.path.as_posix())

            # Start pickling.
            pickle_path = (
                asset_publish.pickle_path
            )  # TODO: Do we need a pickle for all of them? I think one would be enough.
            with open(pickle_path.as_posix(), "wb") as f:
                pickle.dump(self.build_context, f)
            logger.info(f"Pickled to {pickle_path.as_posix()}")

            # Open new blender instance, with publish script.
            BuilderBlenderStarter.start_publish(
                asset_publish.path,
                pickle_path,
            )

    def pull(
        self,
        context: bpy.types.Context,
        source_type: Union[type[AssetTask], type[AssetPublish]],
    ) -> None:

        """
        This function is used to pull task layers from an asset publish in to an asset task
        but also to pull an asset task in to an asset publish. The source_type argument controls
        the direction.
        """

        # TODO: Refactor this to get rif of the if else checking depending on the source
        # type.

        # Here we don't need to open another blender instance. We can use the current
        # one. We pull in the asset collection from the latest asset publish and
        # perform the required data transfers depending on what was selected.

        if issubclass(source_type, AssetTask):
            # Import Asset Collection form Asset Task.
            merge_triplet: TransferCollectionTriplet = (
                self.asset_importer.import_asset_task()
            )

        elif issubclass(source_type, AssetPublish):

            # Check if there are any publishes.
            if not self.build_context.asset_publishes:
                raise AssetBuilderFailedToPull(
                    f"Failed to pull. Found no asset publishes."
                )

            # Import Asset Collection form Asset Publish.
            merge_triplet: TransferCollectionTriplet = (
                self.asset_importer.import_asset_publish()
            )

        # Apparently Blender does not evaluate objects or collections in the depsgraph
        # in some cases if they are not visible. This is something Users should not have to take
        # care about when writing their transfer data instructions. So we will make sure here
        # that everything is visible and after the transfer the original state will be restored.
        vis_objs: List[EnsureVisible] = []
        for coll in merge_triplet.get_collections():
            for obj in coll.all_objects:
                vis_objs.append(EnsureVisible(obj))

        # The target collection (base) was already decided by ASSET_IMPORTER.import_asset_task()
        # and is saved in merge_triplet.target_coll.
        mapping_task_target = AssetTransferMapping(
            merge_triplet.task_coll, merge_triplet.target_coll
        )
        mapping_publish_target = AssetTransferMapping(
            merge_triplet.publish_coll, merge_triplet.target_coll
        )

        # Process only the TaskLayers that were ticked as 'use'.
        used_task_layers = (
            self.build_context.asset_context.task_layer_assembly.get_used_task_layers()
        )

        # Should be ordered, just in case.
        task_layers = self.build_context.prod_context.task_layers
        task_layers.sort(key=lambda tl: tl.order)

        # Perform Task Layer merging.

        # Note: We always want to apply all TaskLayers except for the Task Layer with the lowest order
        # aka 'Base Task Layer'. This Task Layer gives us the starting point on which to apply all other Task Layers
        # on. The asset importer already handles this logic by supplying as with the right TARGET collection
        # after import. That's why we exclude the first task layer here in the loop.
        logger.info(f"Using {task_layers[0].name} as base.")
        for task_layer in task_layers[1:]:

            # Now we need to decide if we want to transfer data from
            # the task collection to the target collection
            # or
            # the publish collection to the target collection
            # This is reversed depending if we do a push or a pull.

            if source_type == AssetTask:
                # If source type is AssetTask (User does a publish/push):
                # Transfer selected task layers from AssetTask Coll -> Target Coll.
                if task_layer in used_task_layers:
                    logger.info(
                        f"Transferring {task_layer.name} from {merge_triplet.task_coll.name} to {merge_triplet.target_coll.name}."
                    )
                    task_layer.transfer_data(
                        context, mapping_task_target, self.transfer_settings
                    )
                else:
                    # Transfer unselected task layers from Publish Coll -> Target Coll.
                    logger.info(
                        f"Transferring {task_layer.name} from {merge_triplet.publish_coll.name} to {merge_triplet.target_coll.name}."
                    )
                    task_layer.transfer_data(
                        context, mapping_publish_target, self.transfer_settings
                    )
                pass

            elif source_type == AssetPublish:
                # If source type is AssetPublish (User does a pull):
                # Transfer selected task layers from Publish Coll -> Target Coll.
                if task_layer in used_task_layers:

                    logger.info(
                        f"Transferring {task_layer.name} from {merge_triplet.publish_coll.name} to {merge_triplet.target_coll.name}."
                    )
                    task_layer.transfer_data(
                        context, mapping_publish_target, self.transfer_settings
                    )

                # Transfer unselected task layers from Task Coll -> Target Coll.
                else:
                    logger.info(
                        f"Transferring {task_layer.name} from {merge_triplet.task_coll.name} to {merge_triplet.target_coll.name}."
                    )
                    task_layer.transfer_data(
                        context, mapping_task_target, self.transfer_settings
                    )

        # Restore Visibility.
        for obj in vis_objs:
            obj.restore()

        # Remove non TARGET collections.
        for coll in [merge_triplet.publish_coll, merge_triplet.task_coll]:
            util.del_collection(coll)

        # Remove suffix from TARGET Collection.
        asset_suffix.remove_suffix_from_hierarchy(merge_triplet.target_coll)

        # Remove transfer suffix.
        merge_triplet.target_coll.bsp_asset.transfer_suffix = ""

        # Restore scenes asset collection.
        context.scene.bsp_asset.asset_collection = merge_triplet.target_coll

    def _create_first_version(self) -> None:
        target = AssetPublish(self._build_context.asset_dir.get_first_publish_path())
        asset_coll = self._build_context.asset_context.asset_collection
        data_blocks = set((asset_coll,))

        from xml.etree.ElementTree import ElementTree
        from .metadata import AssetElement, TaskLayerElement

        # Create asset meta tree.
        asset_tree = self._create_asset_meta_tree()

        # Create directory if not exist.
        target.path.parent.mkdir(parents=True, exist_ok=True)

        # Save asset tree.
        metadata.write_tree_to_file(target.metadata_path, asset_tree)

        # Check if already exists.
        if target.path.exists():
            raise AssetBuilderFailedToPublish(
                f"Failed to create first publish. Already exist: {target.path.name}"
            )

        # Create blend file.
        bpy.data.libraries.write(
            target.path.as_posix(),
            data_blocks,
            path_remap="RELATIVE_ALL",
            fake_user=True,
        )

        logger.info("Created first asset version: %s", target.path.as_posix())

    def _create_asset_meta_tree(self) -> AssetMetadataTree:
        # Create asset meta tree.
        meta_asset = (
            self.build_context.asset_context.asset_collection.bsp_asset.gen_meta_asset()
        )
        meta_task_layers: List[MetaDataTaskLayer] = []

        for task_layer in self.build_context.prod_context.task_layers:
            meta_tl = meta_util.init_meta_task_layer(task_layer)
            meta_task_layers.append(meta_tl)

        return AssetMetadataTree(meta_asset, meta_task_layers)
