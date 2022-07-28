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
    """
    This class is more or less boilerplate so Users can easily write their TaskLayer
    in the production config file. Users need to implement the transfer_data function
    and fille out the class attributes.
    """
    name: str = ""
    description: str = ""
    order: int = -1
    task_suffix: str = ""

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
    def transfer(
        cls,
        context: bpy.types.Context,
        build_context: "BuildContext", # Otherwise get stupid circular import errors.
        transfer_mapping: AssetTransferMapping,
        transfer_settings: bpy.types.PropertyGroup,
    ) -> None:
        cls.transfer_collections(transfer_mapping)
        cls.transfer_data(context, build_context, transfer_mapping, transfer_settings)
        cls.assign_objects(transfer_mapping)

    @classmethod
    def transfer_data(
        cls,
        context: bpy.types.Context,
        build_context: "BuildContext", # Otherwise get stupid circular import errors.
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

        You can also access the root Asset source and Target Collection:
        transfer_mapping.source_coll: bpy.types.Collection
        transfer_mapping.target_coll: bpy.types.Collection

        Further than that you can access to objects which had no match.
        transfer_mapping.no_match_target_objs: Set[bpy.types.Object] (all objs that exist in target but not in source)
        transfer_mapping.no_match_source_objs: Set[bpy.types.Object] (vice versa)


        Further then that Users can define custom transfer settings by defining a TransferSettings
        Class which inherits from a PropertyGroup in the task_layer module. Users can query these settings
        by checking the transfer_settings argument.

        transfer_settings.custom_option
        """
        raise NotImplementedError

    @classmethod
    def transfer_collections(cls, transfer_mapping: AssetTransferMapping):
        root_coll = transfer_mapping.source_coll
        transfer_suffix = root_coll.bsp_asset.transfer_suffix

        for src_coll in root_coll.children:
            original_name = src_coll.name.replace(transfer_suffix, "")
            if cls.task_suffix and original_name.endswith(cls.task_suffix):
                # If this collection is assigned to this Task Layer.
                cls.transfer_collection_objects(transfer_mapping, src_coll, root_coll)
        
        # Unlink target collections that no longer exist in source.
        for target_coll in transfer_mapping.target_coll.children:
            if cls.task_suffix and cls.task_suffix in target_coll.name:
                for child_coll in target_coll.children:
                    if child_coll in transfer_mapping.no_match_target_colls:
                        target_coll.children.unlink(child_coll)

    @classmethod
    def transfer_collection_objects(cls, 
            transfer_mapping: AssetTransferMapping, 
            src_coll: bpy.types.Collection, 
            parent_coll: bpy.types.Collection):
        """Transfer object assignments from source to target.
        If an object ends up being un-assigned, it may get purged.
        New collections will be created as necessary.
        """
        # Ensure target collection exists.
        tgt_coll = transfer_mapping.collection_map.get(src_coll)
        if not tgt_coll:
            src_suffix = transfer_mapping.source_coll.bsp_asset.transfer_suffix
            tgt_suffix = transfer_mapping.target_coll.bsp_asset.transfer_suffix
            tgt_coll = bpy.data.collections.new(src_coll.name.replace(src_suffix, tgt_suffix))
            transfer_mapping._collection_map[src_coll] = tgt_coll
            tgt_parent = transfer_mapping.collection_map.get(parent_coll)
            assert tgt_parent, "The corresponding target parent collection should've been created in the previous recursion: " + src_coll.name
            tgt_parent.children.link(tgt_coll)

        # Un-assigning everything from the target coll.
        for o in tgt_coll.objects:
            tgt_coll.objects.unlink(o)
        

        # Re-assign those objects which correspond to the ones in source coll.
        for src_ob in src_coll.objects:
            tgt_ob = transfer_mapping.object_map.get(src_ob)
            if not tgt_ob:
                tgt_ob = src_ob
            tgt_coll.objects.link(tgt_ob)
        
        # Do the same recursively for child collections.
        for child_coll in src_coll.children:
            cls.transfer_collection_objects(transfer_mapping, child_coll, src_coll)

    @classmethod
    def assign_objects(cls,
            transfer_mapping: AssetTransferMapping):
        """Unassign remaining source collections/objects and replace them with target collections/objects for the whole file.
        """
        # iterate through all collections in the file
        for coll in list(bpy.data.collections) + [scene.collection for scene in bpy.data.scenes]:
            collection_map = transfer_mapping.collection_map
            transfer_collections = set().union(*[{k, v} for k, v in collection_map.items()])
            if coll in transfer_collections:
                continue
            for child_coll in coll.children:
                if child_coll not in collection_map:
                    continue
                if child_coll in {transfer_mapping.source_coll, transfer_mapping.target_coll}:
                    continue
                tgt_coll = collection_map.get(child_coll)
                if not tgt_coll:
                    continue
                coll.children.unlink(child_coll)
                coll.children.link(tgt_coll)
            for ob in coll.objects:
                if not ob in transfer_mapping.object_map:
                    continue
                tgt_ob = transfer_mapping.object_map.get(ob)
                if not tgt_ob:
                    continue
                coll.objects.unlink(ob)
                coll.objects.link(tgt_ob)

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
    This Class holds all TaskLayers relevant for the build.
    Each TaskLayer is stored as a TaskLayerConfig object which provides
    the additional information.
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
