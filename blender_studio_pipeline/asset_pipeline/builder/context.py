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
import importlib
import logging

from typing import List, Dict, Union, Any, Set, Optional
from types import ModuleType

from pathlib import Path

import bpy

from ..sys_utils import SystemPathInclude
from .task_layer import TaskLayer, TaskLayerAssembly
from .. import asset_files
from ..asset_files import AssetDir, AssetPublish, AssetTask

logger = logging.getLogger("BSP")


class ProdContextFailedToInitialize(Exception):
    pass


class AssetContextFailedToInitialize(Exception):
    pass


class BuildContextFailedToInitialize(Exception):
    pass


# TODO: create global context, that holds Productio TaskLayers
# BuildContext uses that to create TaskLayerAsssembly


class ProcessPair:
    """
    Simple Class that stores a logically connected target and a pull from path.
    """

    def __init__(self, target: Path, pull_from: Path) -> None:
        self.target = target
        self.pull_from = pull_from


class ProductionContext:

    """
    A context that represents configuration on a Production Level.
    Independent from Blender, no bpy access.
    """

    def __init__(self, config_folder: Path):

        if not config_folder or not config_folder.exists():
            raise ProdContextFailedToInitialize(
                f"Failed to init ProductionContext. Invalid config folder: {config_folder}"
            )

        self._task_layers: List[type[TaskLayer]] = []
        self._config_folder: Path = config_folder
        self._module_of_task_layers: Optional[ModuleType] = None

        # Load configs from config_folder.
        self._collect_configs()
        logger.debug("Initialized Production Context")

    @property
    def config_folder(self) -> Path:
        return self._config_folder

    @property
    def task_layers(self) -> Optional[List[type[TaskLayer]]]:
        return self._task_layers

    def _collect_configs(self) -> None:

        # Add config folder temporarily to sys.path for convenient
        # import.

        with SystemPathInclude([self._config_folder]):

            # Load Task Layers.
            # TODO: information duplicated in add-on preferences
            # Make it DRY

            # Check if task layers module was already imported.
            # TODO: does not work perfectly, if we remove a TaskLayer from
            # config file and then reload, it's still there.
            # https://stackoverflow.com/questions/2918898/prevent-python-from-caching-the-imported-modules
            if self._module_of_task_layers:
                # Reload it so Users won't have to restart Blender.
                self._module_of_task_layers = importlib.reload(
                    self._module_of_task_layers
                )
            else:
                import task_layers as prod_task_layers

                self._module_of_task_layers = prod_task_layers

            # Crawl module for TaskLayers.
            self._collect_prod_task_layers()

    def _collect_prod_task_layers(self) -> None:

        # Clear task layer list, otherwise we will add new but don't
        # remove old.
        self._task_layers.clear()
        module = self._module_of_task_layers

        # Find all valid TaskLayer Classes.
        for module_item_str in dir(module):
            module_item = getattr(module, module_item_str)

            # This checks that the module item is a class definition
            # and not e.G and instance of that class.
            if module_item.__class__ != type:
                continue

            if not issubclass(module_item, TaskLayer):
                continue

            # Checks e.G that 'name' class attribute is set.
            if not module_item.is_valid():
                continue

            self._task_layers.append(module_item)

        logger.info(f"Detected Production TaskLayers: {self._task_layers}")

    def __repr__(self) -> str:
        header = "\nPRODUCTION CONTEXT\n------------------------------------"
        footer = "------------------------------------"
        prod_task_layers = (
            f"Production Task Layers: {[t.name for t in self._task_layers]}"
        )
        return "\n".join([header, prod_task_layers, footer])


class AssetContext:

    """
    Should be updated on each scene load.
    """

    def __init__(self, bl_context: bpy.types.Context, prod_context: ProductionContext):

        # Check if bl_context and config_folder are valid.
        if not all([bl_context, bl_context.scene.bsp_asset.asset_collection]):
            raise AssetContextFailedToInitialize(
                "Failed to initialize AssetContext. Invalid blender_context or asset collection not set."
            )

        self._bl_context: bpy.types.Context = bl_context
        self._asset_collection: bpy.types.Collection = (
            bl_context.scene.bsp_asset.asset_collection
        )
        self._task_layer_assembly = TaskLayerAssembly(prod_context._task_layers)

        # TODO: Load custom Task Layers.
        self._custom_task_layers: List[Any] = []

        logger.debug("Initialized Asset Context")

    @property
    def asset_collection(self) -> Optional[bpy.types.Collection]:
        return self._asset_collection

    @property
    def asset_name(self) -> str:
        return self.asset_collection.bsp_asset.entity_name

    @property
    def task_layer_assembly(self) -> TaskLayerAssembly:
        return self._task_layer_assembly

    def update_from_bl_context(self, bl_context: bpy.types.Context) -> None:
        self._asset_collection = bl_context.scene.bsp_asset.asset_collection
        self._update_task_layer_assembly_from_context(bl_context)

    def _update_task_layer_assembly_from_context(
        self, bl_context: bpy.types.Context
    ) -> None:
        # Update TaskLayerAssembly, to load the
        # previously disabled and enabled TaskLayer States.
        # They are stored in context.scene.bl_asset.task_layers

        # TODO: we should take in to account that in the meantime
        # production TaskLayers could have been updated.
        for item in bl_context.scene.bsp_asset.task_layers:
            task_layer_config = self.task_layer_assembly.get_task_layer_config(
                item.task_layer_id
            )
            task_layer_config.use = item.use

    def __repr__(self) -> str:
        header = "\nASSET CONTEXT\n------------------------------------"
        footer = "------------------------------------"
        asset_info = f"Asset: {self.asset_collection.bsp_asset.entity_name}({self.asset_collection})"
        task_layer_assembly = str(self.task_layer_assembly)

        return "\n".join(
            [
                header,
                asset_info,
                task_layer_assembly,
                footer,
            ]
        )


class BuildContext:

    """
    Class that should function as Context for the asset build.
    Here we want to store everything that is relevant for the build.
    The Builder will process this context.
    Should be updated on start publish/pull and only be relevant for publish/pull.
    """

    def __init__(
        self,
        prod_context: ProductionContext,
        asset_context: AssetContext,
        is_publish: bool,
    ):
        if not all([prod_context, asset_context]):
            raise BuildContextFailedToInitialize(
                "Failed to initialize Build Context. Production or Asset Context not initialized."
            )

        self._prod_context: ProductionContext = prod_context
        self._asset_context: AssetContext = asset_context
        self._is_publish = is_publish
        self._asset_publishes: List[AssetPublish] = []
        self._process_pairs: List[ProcessPair] = []
        self._is_first_publish: bool = False
        self._asset_dir = AssetDir(Path(bpy.data.filepath).parent)
        self._asset_task = AssetTask(Path(bpy.data.filepath))
        self._asset_disk_name = self._asset_dir.asset_name

        self._collect_asset_publishes()

        if self._is_publish:
            self._init_publish()

    @classmethod
    def init_publish(
        cls, prod_context: ProductionContext, asset_context: AssetContext
    ) -> "BuildContext":
        return cls(prod_context, asset_context, True)

    @classmethod
    def init_pull(
        cls, prod_context: ProductionContext, asset_context: AssetContext
    ) -> "BuildContext":
        return cls(prod_context, asset_context, False)

    def _collect_asset_publishes(self) -> None:
        self._asset_publishes.extend(self._asset_dir.get_asset_publishes())

    def _init_publish(self) -> None:
        if not self._asset_publishes:
            self._is_first_publish = True

    @property
    def asset_task(self) -> AssetTask:
        return self._asset_task

    @property
    def asset_dir(self) -> AssetDir:
        return self._asset_dir

    @property
    def prod_context(self) -> ProductionContext:
        return self._prod_context

    @property
    def asset_context(self) -> AssetContext:
        return self._asset_context

    def __repr__(self) -> str:
        header = "\nBUILD CONTEXT\n------------------------------------"
        footer = "------------------------------------"
        asset_task = f"Asset Task: {str(self._asset_task)}"
        asset_disk_name = f"Asset Disk Name: {self._asset_disk_name}"
        asset_dir = f"Asset Dir: {str(self.asset_dir)}"
        return "\n".join(
            [
                header,
                asset_disk_name,
                asset_task,
                asset_dir,
                str(self.prod_context),
                str(self.asset_context),
                footer,
            ]
        )


# Assembling an asset means
# Identifying push or pull is not too important for the actual logic as we kind of do the
# same thing in both. If we push we actually open the asset version file and perform a pull as well.
# We only need to differentiate the last step: Execute Post Merge Hook (Push) / Override Restore Hook (Pull)

# # Init BuildContext:
# - Collect Production Task Layers + Metadata
# - Collect Custom Task Layers + Metadata

# # Input BuildOptions:
# - Get input: Push or Pull
# - Get input: Task Layer Selection to process

# # Finalize BuildContext:
# - Collect Metadata:
#   Push:
#   - Collect 1 source (current file) + Metadata
#   - Collect MULTI Targets (Has live task layer, validate if source might be different) + Metadata
# - Pull:
#   - Collect 1 Source + Metadata
#   - Collect 1 Target (current file) + Metadata
# - Create ProcessPair ([{"source": rex.v001.blend, "target": rex.shading.blend}, {"source": rex.shading.blend, "target": rex.v001.blend}])
# - Collect Post Merge Hooks
# - Collect Override Restore Data
# - --> Create Build Context that has all that information

# # For each ProcessPair:
# - Open target file if current file not target
#   - Collect Target Asset Collection
# - Read Source file as library
#   - Collect Source Asset Collection
# - Identify if Source or Target Asset Collection will be Base
# - Suffix Target
# - Append Source Asset Collection
# - Suffix Source
# - Duplicate Base
# - Suffix Base
# - Merge Task Layers
# - Execute Post Merge Hooks (On Push)
# - Execute Override Restore Hooks (On Pull)
