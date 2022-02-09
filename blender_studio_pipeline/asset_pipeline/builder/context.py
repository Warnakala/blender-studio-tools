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
from .task_layer import TaskLayer
from .classes import ProcessPair

logger = logging.getLogger(__name__)


class BuildContext:

    """
    Class that should function as a global context for the asset build.
    Here we want to store everything that is relevant for the build.
    The Builder will process this context.
    """

    def __init__(self):
        self.bl_context: Optional[bpy.types.Context] = None
        self.config_folder: Optional[Path] = None
        self.module_task_layers: Optional[ModuleType] = None
        self.asset_collection: Optional[bpy.types.Collection] = None
        self.task_layers: List[TaskLayer] = []
        self.process_pairs: List[ProcessPair] = []

    def initialize(self, bl_context: bpy.types.Context, config_folder: Path) -> None:
        self.bl_context = bl_context
        self.config_folder = config_folder
        self.asset_collection = bl_context.scene.bsp_asset.asset_collection

        # Check if bl_context and config_folder are valid.
        if not all([self.bl_context, self.config_folder, self.asset_collection]):
            raise ValueError(
                "Could not initialize BuildContext. Invalid blender_context or config folder."
            )

        # Load configs from config_folder.
        self._collect_configs()

    def _collect_configs(self) -> None:

        # Add config folder temporarily to sys.path for convenient
        # import.
        with SystemPathInclude([self.config_folder.as_posix()]):

            # Load Task Layers.
            # TODO: information duplicated in add-on preferences
            # Make it DRY

            # Check if task layers module was already imported.
            if self.module_task_layers:
                # Reload it so Users won't have to restart Blender.
                self.module_task_layers = importlib.reload(self.module_task_layers)
            else:
                import task_layers as prod_task_layers

                self.module_task_layers = prod_task_layers

            # Crawl module for TaskLayers.
            self._collect_prod_task_layers(self.module_task_layers)

    def _collect_prod_task_layers(self, module: ModuleType) -> List[TaskLayer]:

        # Clear current task layer list
        self.task_layers.clear()

        # Find all valid TaskLayer Classes.
        for module_item_str in dir(module):
            module_item = getattr(module, module_item_str)

            if module_item.__class__ != type:
                continue

            if not issubclass(module_item, TaskLayer):
                continue

            if not module_item.is_valid():
                continue

            self.task_layers.append(module_item)

        logger.info(
            f"Detected Production TaskLayers: {', '.join([l.name for l in self.task_layers])}"
        )

    def __repr__(self) -> str:
        header = "\nBUILD CONTEXT\n------------------------------------"
        asset_info = f"Asset: {self.asset_collection.bsp_asset.entity_name}({self.asset_collection})"
        task_layer_info = (
            f"Production TaskLayers: {', '.join([l.name for l in self.task_layers])}"
        )
        footer = "\n"

        return "\n".join([header, asset_info, task_layer_info, footer])


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
