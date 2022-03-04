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

from typing import List, Dict, Union, Any, Set, Optional, Tuple, Generator

import bpy

from .. import constants, util

logger = logging.getLogger("BSP")


def remove_suffix_from_collection_recursive(
    collection: bpy.types.Collection, delimiter: str = constants.DELIMITER
) -> None:
    """Recursively remove a suffix to a hierarchy of collections."""
    for coll in util.traverse_collection_tree(collection):
        coll.name = delimiter.join(collection.name.split(delimiter)[:-1])


def remove_suffix_from_node_tree_recursive(
    node_tree: bpy.types.NodeTree,
    done: List[bpy.types.NodeTree],
    delimiter: str = constants.DELIMITER,
) -> List[bpy.types.NodeTree]:
    """Recursively remove a suffix from this node tree and all node trees within."""
    if not (node_tree in done or node_tree.library):
        if not node_tree.name.startswith("Shader Nodetree"):
            node_tree.name = delimiter.join(node_tree.name.split(delimiter)[:-1])
            done += [node_tree]

        for n in node_tree.nodes:
            if n.type == "GROUP" and n.node_tree:
                if not n.node_tree in done:
                    done = remove_suffix_from_node_tree_recursive(
                        n.node_tree, done, delimiter
                    )
    return done


def remove_suffix_from_hierarchy(
    collection: bpy.types.Collection, delimiter: str = constants.DELIMITER
) -> None:
    """Removes the suffix after a set delimiter from all collections, objects, object_data, materials in a collection hierarchy"""

    remove_suffix_from_collection_recursive(collection, delimiter)

    materials: Set[bpy.types.Material] = set()
    done_nt: List[bpy.types.NodeTree] = []
    done_geonodes: List[bpy.types.GeometryNode] = []

    for obj in collection.all_objects:

        # OBJECTS.
        obj.name = delimiter.join(obj.name.split(delimiter)[:-1])

        # OBJECT DATA.
        if obj.data:
            obj.data.name = delimiter.join(obj.data.name.split(delimiter)[:-1])

        # MATERIALS.
        for ms in obj.material_slots:
            m = ms.material

            if not m:
                continue

            if m in materials:
                continue

            m.name = delimiter.join(m.name.split(delimiter)[:-1])
            materials.add(m)

            if not m.node_tree:
                continue

            done_nt = remove_suffix_from_node_tree_recursive(
                m.node_tree, done_nt, delimiter
            )

        # GEO-NODES.
        for mod in obj.modifiers:
            if not mod.type == "NODES":
                continue
            if not mod.node_group:
                continue
            if mod.node_group in done_geonodes:
                continue
            mod.node_group.name = delimiter.join(
                mod.node_group.name.split(delimiter)[:-1]
            )
            done_geonodes.append(mod.node_group)


def add_suffix_to_collection_recursive(
    collection: bpy.types.Collection, suffix: str
) -> None:
    """Recursively add a suffix to a hierarchy of collections and objects."""
    for coll in util.traverse_collection_tree(collection):
        coll.name += suffix


def add_suffix_to_node_tree_recursive(
    node_tree: bpy.types.NodeTree, suffix: str
) -> None:
    """Recursively add a suffix to this node tree and all node trees within."""
    # TODO: add traverse_node_tree function
    if not (
        node_tree.name.endswith(suffix)
        or node_tree.library
        or node_tree.name == "Shader Nodetree"
    ):
        node_tree.name += suffix

    for n in node_tree.nodes:
        if n.type == "GROUP" and n.node_tree and not n.node_tree.name.endswith(suffix):
            add_suffix_to_node_tree_recursive(n.node_tree, suffix)


def add_suffix_to_hierarchy(
    collection: bpy.types.Collection, suffix: str
) -> bpy.types.Collection:
    """Add a suffix to the names of all sub-collections, objects,
    materials and node groups of a collection."""

    add_suffix_to_collection_recursive(collection, suffix)

    materials: Set[bpy.types.Material] = set()

    for obj in collection.all_objects:
        # OBJECT.
        new_name = obj.name + suffix

        # Check if new name already exists for some reason.
        if new_name in bpy.data.objects:
            bad_object = bpy.data.objects[new_name]
            bad_object.name += ".old"
            logger.warning(
                "Warning: Object %s with suffix already existed, added .old suffix.",
                new_name,
            )
        obj.name = new_name

        # OBJECT DATA.
        if obj.data:
            obj.data.name += suffix

        # MATERIALS.
        for ms in obj.material_slots:
            m = ms.material

            # Material can be None.
            if not m:
                continue

            # Material can be processed
            if m in materials:
                continue

            m.name += suffix
            materials.add(m)

            if not m.node_tree:
                continue

            add_suffix_to_node_tree_recursive(m.node_tree, suffix)

        # GEO-NODES.
        for mod in obj.modifiers:
            if not mod.type == "NODES":
                continue
            if not mod.node_group:
                continue
            if not mod.node_group.name.endswith(suffix):
                # TODO: could we run in collisions here, same
                # as object name renaming couple lines up?
                mod.node_group.name += suffix

    return collection
