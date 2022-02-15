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
from . import asset_suffix

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


def rreplace(s: str, old: str, new: str, occurrence: int) -> str:
    li = s.rsplit(old, occurrence)
    return new.join(li)


class AssetTransferMapping:
    """
    This class represents a mapping between a source collection and a target collection.
    It also contains an object mapping which connects each source object with a target
    object. The mapping process relies heavily on suffixes, which is why we use
    MergeCollections as input that store a suffix.
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
        self._object_map = self._gen_object_map()
        self._collection_map = self._gen_collection_map()

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
        for s_coll in asset_suffix.traverse_collection_tree(self.source_coll):

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

    @property
    def object_map(self) -> Dict[bpy.types.Object, bpy.types.Object]:
        return self._object_map

    @property
    def collection_map(self) -> Dict[bpy.types.Collection, bpy.types.Collection]:
        return self._collection_map
