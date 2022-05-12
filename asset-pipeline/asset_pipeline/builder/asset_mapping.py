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

from .vis import EnsureCollectionVisibility

from .. import util

logger = logging.getLogger("BSP")


class TransferCollectionTriplet:
    """
    This class holds the 3 collections that are needed for the merge process. Publish, Task and Target Collection.
    During the merge we have to dynamically decide which Task Layer we take from the Publish Collection
    and which we take from the Task Collection to apply on the target.
    That's why we save these 3 Collections in a dedicated class, as we require them.
    """

    def __init__(
        self,
        task_coll: bpy.types.Collection,
        publish_coll: bpy.types.Collection,
        target_coll: bpy.types.Collection,
    ):
        self.publish_coll = publish_coll
        self.task_coll = task_coll
        self.target_coll = target_coll
        self._vis_colls: List[EnsureCollectionVisibility] = []

    def get_collections(self) -> List[bpy.types.Collection]:
        return [self.task_coll, self.publish_coll, self.target_coll]

    def reset_rigs(self) -> None:
        """To ensure correct data transferring, make sure all rigs are in their
        default positions."""
        for main_coll in self.get_collections():
            for ob in main_coll.all_objects:
                if ob.type != "ARMATURE":
                    continue
                util.reset_armature_pose(
                    ob,
                    only_selected=False,
                    reset_properties=True,
                    reset_transforms=True,
                )
                ob.data.pose_position = "REST"

    def ensure_vis(self) -> None:
        # Apparently Blender does not evaluate objects or collections in the depsgraph
        # in some cases if they are not visible. This is something Users should not have to take
        # care about when writing their transfer data instructions. So we will make sure here
        # that everything is visible and after the transfer the original state will be restored.

        # Catch mistake if someone calls this twice without restoring before.
        if self._vis_colls:
            self.restore_vis()

        for main_coll in self.get_collections():
            self._vis_colls.append(EnsureCollectionVisibility(main_coll))

    def restore_vis(self) -> None:
        for vis_coll in self._vis_colls:
            vis_coll.restore()

        self._vis_colls.clear()


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
        source_coll: bpy.types.Collection,
        target_coll: bpy.types.Collection,
    ):

        self._source_coll = source_coll
        self._target_coll = target_coll

        self._no_match_source_objs: Set[bpy.types.Object] = set()
        self._no_match_target_objs: Set[bpy.types.Object] = set()

        # TODO: gen_map functions almost have the same code,
        # refactor it to one function with the right parameters.
        self.generate_mapping()

    @property
    def source_coll(self) -> bpy.types.Collection:
        return self._source_coll

    @property
    def target_coll(self) -> bpy.types.Collection:
        return self._target_coll

    @property
    def no_match_source_objs(self) -> Set[bpy.types.Object]:
        """
        All objects that exist in source but not in target
        """
        return self._no_match_source_objs

    @property
    def no_match_target_objs(self) -> Set[bpy.types.Object]:
        """
        All objects that exist in target but not in source
        """
        return self._no_match_target_objs

    def generate_mapping(self) -> None:
        self._object_map = self._gen_object_map()
        self._collection_map = self._gen_collection_map()
        self._material_map = self._gen_material_map()

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
                self._source_coll.bsp_asset.transfer_suffix,
                self._target_coll.bsp_asset.transfer_suffix,
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
                self._no_match_source_objs.add(source_obj)
                continue
            else:
                object_map[source_obj] = target_obj
                # logger.debug(
                #     "Found match: source: %s target: %s",
                #     source_obj.name,
                #     target_obj.name,
                # )

        # Populate no match target set.
        match_target_objs = set([obj for obj in object_map.values()])
        self._no_match_target_objs = (
            set(self.target_coll.all_objects) - match_target_objs
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
                self._source_coll.bsp_asset.transfer_suffix,
                self._target_coll.bsp_asset.transfer_suffix,
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
                # logger.debug(
                #     "Found match: source: %s target: %s",
                #     s_coll.name,
                #     t_coll.name,
                # )

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
                self._source_coll.bsp_asset.transfer_suffix,
                self._target_coll.bsp_asset.transfer_suffix,
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
                # logger.debug(
                #     "Found match: source: %s target: %s",
                #     s_mat.name,
                #     t_mat.name,
                # )

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
