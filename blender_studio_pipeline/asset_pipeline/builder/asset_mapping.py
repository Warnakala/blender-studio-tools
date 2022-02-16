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
from ... import util

import bpy

logger = logging.getLogger("BSP")


class MergeCollection:
    """
    Small convenient class to connect a collection and its objects to a
    specific suffix. This is needed because later we need to map objects
    to objects. These objects have the same name except of the suffix.
    If we know the suffix we can easily map them up together.
    """

    def __init__(self, collection: bpy.types.Collection, suffix: str):
        # TODO: Just realized we might not need this class if we just
        # store the SUFFIX in a custom collection property.
        self.collection = collection
        self.suffix = suffix


class MergeCollectionTriplet:
    """
    This class holds the 3 collections (with their suffixes by storing them as MergeCollection)
    that are needed for the merge process. Publish, Task and Target Collection.
    During the merge we have to dynamically decide which Task Layer we take from the Publish Collection
    and which we take from the Task Collection to apply on the target.
    That's why we save these 3 Collections in a dedicated class, as we require them.
    """

    def __init__(
        self,
        task_coll: MergeCollection,
        publish_coll: MergeCollection,
        target_coll: MergeCollection,
    ):
        self.publish_coll = publish_coll
        self.task_coll = task_coll
        self.target_coll = target_coll

    def get_merge_collections(self) -> List[MergeCollection]:
        return [self.publish_coll, self.task_coll, self.target_coll]

    def get_collections(self) -> List[bpy.types.Collection]:
        return [m.collection for m in self.get_merge_collections()]


def rreplace(s: str, old: str, new: str, occurrence: int) -> str:
    li = s.rsplit(old, occurrence)
    return new.join(li)


class AssetTransferMapping:
    """
    The AssetTranfserMapping class represents a mapping between a source and a target.
    It contains an object mapping which connects each source object with a target
    object as well as a collection mapping.
    The mapping process relies heavily on suffixes, which is why we use
    MergeCollections as input that store a suffix.

    Instances of this class will be pased TaskLayer data transfer function so Users
    can easily write their merge instructions.
    """

    def __init__(
        self,
        source_merge_coll: MergeCollection,
        target_merge_coll: MergeCollection,
    ):

        self._source_merge_coll = source_merge_coll
        self._target_merge_coll = target_merge_coll
        self._source_coll = source_merge_coll.collection
        self._target_coll = target_merge_coll.collection

        # TODO: gen_map functions almost have the same code,
        # refactor it to one function with the right parameters.
        self._object_map = self._gen_object_map()
        self._collection_map = self._gen_collection_map()
        self._material_map = self._gen_material_map()

    @property
    def source_coll(self) -> bpy.types.Collection:
        return self._source_coll

    @property
    def target_coll(self) -> bpy.types.Collection:
        return self._target_coll

    def _gen_object_map(self) -> Dict[bpy.types.Object, bpy.types.Object]:

        """
        Tries to link all objects in source collection to an object in
        target collection. Uses suffixes to match them up.
        """

        object_map: Dict[bpy.types.Object, bpy.types.Object] = {}

        for source_obj in self.source_coll.all_objects:

            # assert source_obj.name.endswith(self._source_merge_coll.suffix)

            # Replace source object suffix with target suffix to get target object.
            target_obj_name = rreplace(
                source_obj.name,
                self._source_merge_coll.suffix,
                self._target_merge_coll.suffix,
                1,
            )
            try:
                target_obj = self._target_coll.all_objects[target_obj_name]
            except KeyError:
                logger.debug(
                    "Failed to find match obj %s for %s",
                    target_obj_name,
                    source_obj.name,
                )
                continue
            else:
                object_map[source_obj] = target_obj
                logger.debug(
                    "Found match: source: %s target: %s",
                    source_obj.name,
                    target_obj.name,
                )

        return object_map

    def _gen_collection_map(self) -> Dict[bpy.types.Collection, bpy.types.Collection]:
        """
        Tries to link all source collections to a target collection.
        Uses suffixes to match them up.
        """
        coll_map: Dict[bpy.types.Collection, bpy.types.Collection] = {}

        # Link top most parents.
        coll_map[self.source_coll] = self.target_coll

        # Link up all children.
        for s_coll in util.traverse_collection_tree(self.source_coll):

            # assert source_obj.name.endswith(self._source_merge_coll.suffix)

            # Replace source object suffix with target suffix to get target object.
            target_coll_name = rreplace(
                s_coll.name,
                self._source_merge_coll.suffix,
                self._target_merge_coll.suffix,
                1,
            )
            try:
                t_coll = bpy.data.collections[target_coll_name]
            except KeyError:
                logger.debug(
                    "Failed to find match collection %s for %s",
                    s_coll.name,
                    target_coll_name,
                )
                continue
            else:
                coll_map[s_coll] = t_coll
                logger.debug(
                    "Found match: source: %s target: %s",
                    s_coll.name,
                    t_coll.name,
                )

        return coll_map

    def _gen_material_map(self) -> Dict[bpy.types.Material, bpy.types.Material]:
        material_map: Dict[bpy.types.Material, bpy.types.Material] = {}

        source_materials: List[bpy.types.Material] = self._get_all_materials_of_coll(
            self.source_coll
        )
        target_materials_dict: Dict[
            str, bpy.types.Material
        ] = self._get_all_materials_of_coll(self.target_coll, as_dict=True)

        # Link up all children.
        for s_mat in source_materials:

            # assert s_mat.name.endswith(self._source_merge_coll.suffix)

            # Replace source object suffix with target suffix to get target object.
            target_mat_name = rreplace(
                s_mat.name,
                self._source_merge_coll.suffix,
                self._target_merge_coll.suffix,
                1,
            )
            try:
                t_mat = target_materials_dict[target_mat_name]
            except KeyError:
                logger.debug(
                    "Failed to find match material %s for %s",
                    s_mat.name,
                    target_mat_name,
                )
                continue
            else:
                material_map[s_mat] = t_mat
                logger.debug(
                    "Found match: source: %s target: %s",
                    s_mat.name,
                    t_mat.name,
                )

        return material_map

    def _get_all_materials_of_coll(
        self, coll: bpy.types.Collection, as_dict: bool = False
    ) -> Union[List[bpy.types.Material], Dict[str, bpy.types.Material]]:
        materials: List[bpy.types.Material] = []
        for obj in coll.all_objects:
            for ms in obj.material_slots:
                m = ms.material

                # Material can be None.
                if not m:
                    continue

                if m in materials:
                    continue

                materials.append(m)

        # Return list.
        if not as_dict:
            return materials

        # Return dict.
        materials_dict = {}
        for mat in materials:
            materials_dict[mat.name] = mat
        return materials_dict

    @property
    def object_map(self) -> Dict[bpy.types.Object, bpy.types.Object]:
        """
        Key: Source
        Value: Target
        """
        return self._object_map

    @property
    def collection_map(self) -> Dict[bpy.types.Collection, bpy.types.Collection]:
        """
        Key: Source
        Value: Target
        """
        return self._collection_map

    @property
    def material_map(self) -> Dict[bpy.types.Material, bpy.types.Material]:
        """
        Key: Source
        Value: Target
        """
        return self._material_map
