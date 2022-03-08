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
from types import ModuleType

from pathlib import Path

import bpy

from .asset_mapping import AssetTransferMapping

logger = logging.getLogger("BSP")


# TODO: Do we maybe need a BaseTask Layer that has default order = 0
# and has no transfer_data function?
# The Base Task Layer gives us the base data on which we apply all other
# TaskLayers. Merging this layer just means, take it as a starting point.
# Note: Right now the Asset Importer already handles this logic by checking if the
# asset task source has the TaskLayer with the lowest order enabled and creates a TARGET collection.


class TaskLayer:

    name: str = ""
    description: str = ""
    order: int = -1

    @classmethod
    def get_id(cls) -> str:
        """
        Used to uniquely identify a TaskLayer as we expect that there are not 2 TaskLayer Classes
        That have the same name.
        """
        return cls.__name__

    @classmethod
    def is_valid(cls) -> bool:
        return bool(cls.name and cls.order >= 0)

    @classmethod
    def transfer_data(
        cls,
        context: bpy.types.Context,
        transfer_mapping: AssetTransferMapping,
        transfer_settings: bpy.types.PropertyGroup,
    ) -> None:

        # TODO: transfer_settings can be None if Users didn't provide a
        # TransferSettings class in the task layer module. We should update this.
        """
        The AssetTranfserMapping class represents a mapping between a source and a target.
        It contains an object mapping which connects each source object with a target.
        The maps are just dictionaries where the key is the source and the value the target.
        Both key and target are actual Blender ID Datablocks.
        This makes it easy to write Merge Instructions.
        With it you can do access things like:

        transfer_mapping.object_map: Dict[bpy.types.Object, bpy.types.Object]
        transfer_mapping.collection_map: Dict[bpy.types.Collection, bpy.types.Collection]
        transfer_mapping.material_map: Dict[bpy.types.Material, bpy.types.Material]

        For all mappings:
        Key: Source
        Value: Target

        Further then that Users can define custom transfer settings by defining a TransferSettings
        Class which inherits from a PropertyGroup in the task_layer module. Users can query these settings
        by checking the transfer_settings argument.

        transfer_settings.custom_option
        """
        raise NotImplementedError

    def __repr__(self) -> str:
        return f"TaskLayer{self.name}"


class TaskLayerConfig:
    """
    This Class holds a TaskLayer and additional Information that
    determine how this TaskLayer is handeled during build.
    For example .use controls if TaskLayer should be used for build.
    """

    def __init__(self, task_layer: type[TaskLayer]):
        self._task_layer = task_layer
        self._use: bool = False

    @property
    def task_layer(self) -> type[TaskLayer]:
        return self._task_layer

    @property
    def use(self) -> bool:
        return self._use

    @use.setter
    def use(self, value: bool) -> None:
        self._use = value

    def reset(self) -> None:
        self._use = False

    def __repr__(self) -> str:
        return f"{self.task_layer.name}(use: {self.use})"


class TaskLayerAssembly:

    """
    This Class holds all TaskLayers relevant for build.
    Each TaskLayer is stored as TaskLayerConfig object which provides
    the built additional information.
    """

    def __init__(self, task_layers: List[type[TaskLayer]]):
        # Create a dictionary data structure here, so we can easily control
        # from within Blender by string which TaskLayers to enable and disable for built.
        # As key we will use the class.get_id() attribute of each TaskLayer. (Should be unique)
        self._task_layer_config_dict: Dict[str, TaskLayerConfig] = {}
        self._task_layers = task_layers
        self._task_layer_configs: List[TaskLayerConfig] = []
        # For each TaskLayer create a TaskLayerConfig and add entry in
        # dictionary.
        for task_layer in task_layers:

            # Make sure that for whatever reason there are no 2 identical TaskLayer.
            if task_layer.get_id() in self._task_layer_config_dict:

                self._task_layer_config_dict.clear()
                raise Exception(
                    f"Detected 2 TaskLayers with the same Class name. [{task_layer.get_id()}]"
                )
            tc = TaskLayerConfig(task_layer)
            self._task_layer_configs.append(tc)
            self._task_layer_config_dict[task_layer.get_id()] = tc

        # Sort lists.
        self._task_layer_configs.sort(key=lambda tc: tc.task_layer.order)
        self._task_layers.sort(key=lambda tl: tl.order)

    def get_task_layer_config(self, key: str) -> TaskLayerConfig:
        return self._task_layer_config_dict[key]

    def get_used_task_layers(self) -> List[type[TaskLayer]]:
        return [tc.task_layer for tc in self.task_layer_configs if tc.use]

    def get_used_task_layer_ids(self) -> List[str]:
        return [t.get_id() for t in self.get_used_task_layers()]

    def get_task_layers_for_bl_enum(self) -> List[Tuple[str, str, str]]:
        return [(tl.get_id(), tl.name, tl.description) for tl in self.task_layers]

    @property
    def task_layer_config_dict(self) -> Dict[str, TaskLayerConfig]:
        return self._task_layer_config_dict

    @property
    def task_layer_configs(self) -> List[TaskLayerConfig]:
        return self._task_layer_configs

    @property
    def task_layers(self) -> List[type[TaskLayer]]:
        return self._task_layers

    @property
    def task_layer_names(self) -> List[str]:
        return [l.name for l in self.task_layers]

    def get_task_layer_orders(self, only_used: bool = False) -> List[int]:
        """
        Returns a list of all TaskLayers.order values.
        """
        if not only_used:
            return [t.order for t in self.task_layers]
        else:
            return [tc.task_layer.order for tc in self.task_layer_configs if tc.use]

    def __repr__(self) -> str:
        body = f"{', '.join([str(t) for t in self.task_layer_configs])}"
        return f"TaskLayerAssembly: ({body})"

    def __bool__(self) -> bool:
        return bool(self._task_layer_config_dict)
