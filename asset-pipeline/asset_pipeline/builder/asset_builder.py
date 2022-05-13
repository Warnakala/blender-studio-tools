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

from typing import List, Dict, Union, Any, Set, Optional, Tuple, Callable
from pathlib import Path
from datetime import datetime

import bpy

from . import asset_suffix, metadata, meta_util
from .context import BuildContext
from .asset_importer import AssetImporter
from .asset_mapping import TransferCollectionTriplet, AssetTransferMapping
from .blstarter import BuilderBlenderStarter
from .metadata import MetadataTaskLayer, MetadataTreeAsset
from .hook import HookFunction

from .. import constants, util
from ..asset_files import AssetPublish

logger = logging.getLogger("BSP")


class AssetBuilderFailedToInitialize(Exception):
    pass


class AssetBuilderFailedToPull(Exception):
    pass


class AssetBuilderFailedToPublish(Exception):
    pass


class AssetBuilder:
    """
    The AssetBuilder contains the actual logic how to process the BuildContext.
    It has 3 main functions:

    push: Starts process of opening a new Blender Instance and pickling the BuildContext. New Blender Instance
    actually then loads the BuildContext and calls AssetBuilder.pull_from_task().

    pull_from_publish: Pulls the selected TaskLayers from the AssetPublish in to the current AssetTask.
    Does not require a new Blender Instance.

    pull_from_task: Pulls the selected TaskLayers from the AssetTask in to the current AssetPublish.
    """

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

    def push(self, context: bpy.types.Context) -> None:
        """
        Starts process of opening a new Blender Instance and pickling the BuildContext. New Blender Instance
        actually then loads the BuildContext and calls AssetBuilder.pull_from_task(). That means pickling the BuildContext
        and restoring it in the other Blender Instance.
        """

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

        # Catch special case first version.
        if not self.build_context.asset_publishes:
            asset_publish = self._create_first_version()

            # Start pickling.
            pickle_path = asset_publish.pickle_path
            with open(pickle_path.as_posix(), "wb") as f:
                pickle.dump(self.build_context, f)

            logger.info(f"Pickled to {pickle_path.as_posix()}")

            # Open new blender instance, with publish script.
            # Publish script can detect a first version publish and performs
            # a special set of operations.
            BuilderBlenderStarter.start_publish(
                asset_publish.path,
                pickle_path,
            )
            return

        # Normal publish process.
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
            popen = BuilderBlenderStarter.start_publish(
                asset_publish.path,
                pickle_path,
            )
            return_code = popen.wait()

            # Update returncode property. This will be displayed
            # as icon in the UI and shows Users if something went wrong
            # during push.
            asset_file = context.scene.bsp_asset.asset_publishes.get(
                asset_publish.path.name
            )
            asset_file.returncode_publish = return_code
            print(f"Set {asset_file.path_str} to returncode {return_code}")
            if return_code != 0:
                logger.error(
                    "Push to %s exited with error code: %i",
                    asset_publish.path.name,
                    return_code,
                )

    def pull_from_publish(
        self,
        context: bpy.types.Context,
    ) -> None:

        """
        Pulls the selected TaskLayers from the AssetPublish in to the current AssetTask.
        """

        # Here we don't need to open another blender instance. We can use the current
        # one. We pull in the asset collection from the latest asset publish and
        # perform the required data transfers depending on what was selected.

        # Set is_push attribute.
        self.build_context.is_push = False

        # User does a pull. This code runs in AssetTask file.
        # Check if there are any publishes.
        if not self.build_context.asset_publishes:
            raise AssetBuilderFailedToPull(f"Failed to pull. Found no asset publishes.")

        # We always want to pull from latest asset publish.
        asset_publish = self.build_context.asset_publishes[-1]

        # Import Asset Collection form Asset Publish.
        transfer_triplet: TransferCollectionTriplet = (
            self.asset_importer.import_asset_publish()
        )

        # The target collection (base) was already decided by ASSET_IMPORTER.import_asset_task()
        # and is saved in transfer_triplet.target_coll.
        mapping_task_target = AssetTransferMapping(
            transfer_triplet.task_coll, transfer_triplet.target_coll
        )
        mapping_publish_target = AssetTransferMapping(
            transfer_triplet.publish_coll, transfer_triplet.target_coll
        )

        # Process only the TaskLayers that were ticked as 'use'.
        used_task_layers = (
            self.build_context.asset_context.task_layer_assembly.get_used_task_layers()
        )
        # Should be ordered, just in case.
        prod_task_layers = self.build_context.prod_context.task_layers
        prod_task_layers.sort(key=lambda tl: tl.order)

        transfer_triplet.reset_rigs()
        # Apparently Blender does not evaluate objects or collections in the depsgraph
        # in some cases if they are not visible. Ensure visibility here.
        transfer_triplet.ensure_vis()

        # Perform Task Layer merging.
        # Note: We always want to apply all TaskLayers except for the Task Layer with the lowest order
        # aka 'Base Task Layer'. This Task Layer gives us the starting point on which to apply all other Task Layers
        # on. The asset importer already handles this logic by supplying as with the right TARGET collection
        # after import. That's why we could exclude the first task layer here in the loop.
        # But people at the Studio pointed out it might still be useful sometimes to still let
        # this task layer run the transfer() functions as there can be cases like:
        # Prefixing modififers that are coming from a task layer with the task layer name.
        logger.info(f"Using {prod_task_layers[0].name} as base.")

        # If metafile does not exist yet create it.
        metadata_path = self.build_context.asset_task.metadata_path
        if not metadata_path.exists():
            tree = self._create_asset_metadata_tree_from_collection()
            metadata.write_asset_metadata_tree_to_file(metadata_path, tree)
            logger.info("Created metadata file: %s", metadata_path.name)
            del tree

        # Otherwise load it from disk.
        meta_asset_tree = metadata.load_asset_metadata_tree_from_file(metadata_path)

        # Get time for later metadata update.
        time = datetime.now()

        for task_layer in prod_task_layers:

            # Get metadata task layer for current task layer.
            meta_tl = meta_asset_tree.get_metadata_task_layer(task_layer.get_id())

            # Task Layer might not exist in metadata if it was added midway production
            # if so add it here.
            if not meta_tl:
                logger.warning(
                    "Detected TaskLayer that was not in metadata file yet: %s. Will be added.",
                    task_layer.get_id(),
                )
                meta_tl = meta_util.init_meta_task_layer(task_layer, asset_publish)
                meta_asset_tree.add_metadata_task_layer(meta_tl)

            # Transfer selected task layers from Publish Coll -> Target Coll.
            if task_layer in used_task_layers:

                logger.info(
                    f"Transferring {task_layer.name} from {transfer_triplet.publish_coll.name} to {transfer_triplet.target_coll.name}."
                )
                task_layer.transfer(
                    context, self.build_context, mapping_publish_target, self.transfer_settings
                )

                # Update source meta task layer source path.
                # Save path relative to asset directory, otherwise we have system paths in the start
                # which might differ on various systems.
                meta_tl.source_path = (
                    asset_publish.path_relative_to_asset_dir.as_posix()
                )
                meta_tl.updated_at = time.strftime(constants.TIME_FORMAT)

            # Transfer unselected task layers from Task Coll -> Target Coll. Retain them.
            else:
                logger.info(
                    f"Transferring {task_layer.name} from {transfer_triplet.task_coll.name} to {transfer_triplet.target_coll.name}."
                )
                task_layer.transfer(
                    context, self.build_context, mapping_task_target, self.transfer_settings
                )

                # Here we don't want to update source path, we keep it as is, as we are just 'retaining' here.

        # Set Task Collection reference to the new one.
        bsp = context.scene.bsp_asset
        bsp.task_layer_collection = mapping_task_target.collection_map.get(bsp.task_layer_collection)

        # Cleanup transfer.
        self._clean_up_transfer(context, transfer_triplet)

        # Save updated metadata.
        metadata.write_asset_metadata_tree_to_file(metadata_path, meta_asset_tree)

    def pull_from_task(
        self,
        context: bpy.types.Context,
    ) -> None:

        """
        Pulls the selected TaskLayers from the AssetTask in to the current AssetPublish.
        """
        # Set is_push attribute.
        self.build_context.is_push = True

        # User does a publish/push. This code runs ins AssetPublish file.
        # Import Asset Collection from Asset Task.
        transfer_triplet: TransferCollectionTriplet = (
            self.asset_importer.import_asset_task()
        )
        asset_publish = AssetPublish(Path(bpy.data.filepath))
        metadata_path = asset_publish.metadata_path
        locked_task_layer_ids = asset_publish.metadata.get_locked_task_layer_ids()
        meta_asset_tree = metadata.load_asset_metadata_tree_from_file(metadata_path)

        transfer_triplet.reset_rigs()
        # Ensure visibility for depsgraph evaluation.
        transfer_triplet.ensure_vis()

        # The target collection (base) was already decided by ASSET_IMPORTER.import_asset_task()
        # and is saved in transfer_triplet.target_coll.
        mapping_task_target = AssetTransferMapping(
            transfer_triplet.task_coll, transfer_triplet.target_coll
        )
        mapping_publish_target = AssetTransferMapping(
            transfer_triplet.publish_coll, transfer_triplet.target_coll
        )

        # Process only the TaskLayers that were ticked as 'use'.
        used_task_layers = (
            self.build_context.asset_context.task_layer_assembly.get_used_task_layers()
        )
        # Should be ordered, just in case.
        prod_task_layers = self.build_context.prod_context.task_layers
        prod_task_layers.sort(key=lambda tl: tl.order)

        # Perform Task Layer merging.

        # Note: We always want to apply all TaskLayers except for the Task Layer with the lowest order
        # aka 'Base Task Layer'. This Task Layer gives us the starting point on which to apply all other Task Layers
        # on. The asset importer already handles this logic by supplying as with the right TARGET collection
        # after import. That's why we could exclude the first task layer here in the loop.
        # But people at the Studio pointed out it might still be useful sometimes to still let
        # this task layer run the transfer() functions as there can be cases like:
        # Prefixing modififers that are coming from a task layer with the task layer name.
        logger.info(f"Using {prod_task_layers[0].name} as base.")

        # Get time for later metadata update.
        time = datetime.now()

        for task_layer in prod_task_layers:

            # Get metadata task layer for current task layer.
            meta_tl = meta_asset_tree.get_metadata_task_layer(task_layer.get_id())

            # Task Layer might not exist in metadata if it was added midway production
            # if so add it here.
            if not meta_tl:
                logger.warning(
                    "Detected TaskLayer that was not in metadata file yet: %s. Will be added.",
                    task_layer.get_id(),
                )
                meta_tl = meta_util.init_meta_task_layer(
                    task_layer, self.build_context.asset_task
                )
                meta_asset_tree.add_metadata_task_layer(meta_tl)

            # Transfer selected task layers from AssetTask Coll -> Target Coll.
            # Skip any Task Layers that are locked in this AssetPublish.
            # We have to do this check here because Users can push multiple Task Layer at
            # the same time. Amongst the selected TaskLayers there could be some locked and some live
            # in this asset publish.
            if (
                task_layer in used_task_layers
                and task_layer.get_id() not in locked_task_layer_ids
            ):
                logger.info(
                    f"Transferring {task_layer.name} from {transfer_triplet.task_coll.name} to {transfer_triplet.target_coll.name}."
                )

                task_layer.transfer(
                    context, self.build_context, mapping_task_target, self.transfer_settings
                )

                # Update source meta task layer source path.
                # Save path relative to asset directory, otherwise we have system paths in the start
                # which might differ on various systems.
                meta_tl.source_path = (
                    self.build_context.asset_task.path_relative_to_asset_dir.as_posix()
                )
                meta_tl.updated_at = time.strftime(constants.TIME_FORMAT)

            else:
                # Transfer unselected task layers from Publish Coll -> Target Coll. Retain them.
                logger.info(
                    f"Transferring {task_layer.name} from {transfer_triplet.publish_coll.name} to {transfer_triplet.target_coll.name}."
                )
                task_layer.transfer(
                    context, self.build_context, mapping_publish_target, self.transfer_settings
                )

                # Here we don't want to update source path, we keep it as is, as we are just 'retaining' here.

        # Cleanup transfer.
        self._clean_up_transfer(context, transfer_triplet)

        # Save updated metadata.
        metadata.write_asset_metadata_tree_to_file(metadata_path, meta_asset_tree)

        # Update asset collection properties.
        context.scene.bsp_asset.asset_collection.bsp_asset.update_props_by_asset_publish(
            asset_publish
        )

        # Run hook phase.
        self._run_hooks(context)

    def _clean_up_transfer(
        self, context: bpy.types.Context, transfer_triplet: TransferCollectionTriplet
    ):
        """
        Cleans up the transfer by removing the non target collection in the merge triplet, restoring
        the visibilities as well as purging all orphan data. It also removes the suffixes from the target
        collection and sets the asset collection.
        """
        # Restore Visibility.
        transfer_triplet.restore_vis()

        # Remove non TARGET collections.
        for coll in [transfer_triplet.publish_coll, transfer_triplet.task_coll]:
            util.del_collection(coll)

        # Purge orphan data.
        # This is quite an important one, if this goes wrong we can end up with
        # wrong data block names.
        bpy.ops.outliner.orphans_purge(do_recursive=True)

        # Enable armature poses
        for ob in transfer_triplet.target_coll.all_objects:
            if ob.type != 'ARMATURE':
                continue
            ob.data.pose_position = 'POSE'

        # Remove suffix from TARGET Collection.
        asset_suffix.remove_suffix_from_hierarchy(transfer_triplet.target_coll)

        # Remove transfer suffix.
        transfer_triplet.target_coll.bsp_asset.transfer_suffix = ""

        # Restore scenes asset collection.
        context.scene.bsp_asset.asset_collection = transfer_triplet.target_coll

    def _run_hooks(self, context: bpy.types.Context) -> None:

        if not self.build_context.prod_context.hooks:
            logger.info("No hooks to run")
            return

        asset_coll = context.scene.bsp_asset.asset_collection
        asset_data = asset_coll.bsp_asset
        params = self.build_context.get_hook_kwargs(context)
        hooks_to_run: Set[HookFunction] = set()

        # Collect global hooks first.
        for hook in self.build_context.prod_context.hooks.filter():
            hooks_to_run.add(hook)

        # Collect asset type hooks.
        for hook in self.build_context.prod_context.hooks.filter(
            match_asset_type=asset_data.entity_parent_name,
        ):
            hooks_to_run.add(hook)

        # Collect Global Layer Hooks.
        # We have to loop through each task layer here, can't give filter() function
        # a list as one of the input parameters.
        for (
            task_layer_id
        ) in (
            self.build_context.asset_context.task_layer_assembly.get_used_task_layer_ids()
        ):
            for hook in self.build_context.prod_context.hooks.filter(
                match_task_layers=task_layer_id,
            ):
                hooks_to_run.add(hook)

        # Collect asset hooks.
        for hook in self.build_context.prod_context.hooks.filter(
            match_asset=asset_data.entity_name,
        ):
            hooks_to_run.add(hook)

        # Collect asset + task layer specific hooks.
        for (
            task_layer_id
        ) in (
            self.build_context.asset_context.task_layer_assembly.get_used_task_layer_ids()
        ):
            for hook in self.build_context.prod_context.hooks.filter(
                match_asset=asset_data.entity_name,
                match_task_layers=task_layer_id,
            ):
                hooks_to_run.add(hook)

        # Run actual hooks.
        for hook in hooks_to_run:
            hook(**params)

    def _create_first_version(self) -> AssetPublish:
        first_publish = AssetPublish(
            self._build_context.asset_dir.get_first_publish_path()
        )
        asset_coll = self._build_context.asset_context.asset_collection
        data_blocks = set((asset_coll,))

        # Check if already exists.
        if first_publish.path.exists():
            raise AssetBuilderFailedToPublish(
                f"Failed to create first publish. Already exist: {first_publish.path.name}"
            )

        # Create asset meta tree.
        asset_metadata_tree = self._create_asset_metadata_tree_from_collection()

        # Adjust version metadata.
        asset_metadata_tree.meta_asset.version = first_publish.get_version()

        # Create directory if not exist.
        first_publish.path.parent.mkdir(parents=True, exist_ok=True)

        # Save asset tree.
        metadata.write_asset_metadata_tree_to_file(
            first_publish.metadata_path, asset_metadata_tree
        )

        # Create blend file.
        bpy.data.libraries.write(
            first_publish.path.as_posix(),
            data_blocks,
            path_remap="RELATIVE_ALL",
            fake_user=True,
        )

        logger.info("Created first asset version: %s", first_publish.path.as_posix())
        return first_publish

    def _create_asset_metadata_tree_from_collection(self) -> MetadataTreeAsset:
        # Create asset meta tree.
        meta_asset = (
            self.build_context.asset_context.asset_collection.bsp_asset.gen_metadata_class()
        )
        meta_task_layers: List[MetadataTaskLayer] = []

        for task_layer in self.build_context.prod_context.task_layers:
            meta_tl = meta_util.init_meta_task_layer(
                task_layer, self.build_context.asset_task
            )
            meta_task_layers.append(meta_tl)

        meta_tree_asset = MetadataTreeAsset(
            meta_asset=meta_asset, meta_task_layers=meta_task_layers
        )
        return meta_tree_asset
