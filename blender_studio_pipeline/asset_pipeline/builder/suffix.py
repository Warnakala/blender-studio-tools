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

logger = logging.getLogger("BSP")


def remove_suffix_from_hierarchy(collection, delimiter=".", material=True):
    """Removes the suffix after a set delimiter from all collections, objects, object_data, materials in a collection hierarchy"""

    print(remove_suffix_from_collection_recursive(collection, [], delimiter))

    materials = []

    done_nt = []
    done_geonodes = []

    for obj in collection.all_objects:
        # Object
        obj.name = ".".join(obj.name.split(".")[:-1])

        if obj.data:
            # Object data
            obj.data.name = ".".join(obj.data.name.split(".")[:-1])
        for ms in obj.material_slots:
            m = ms.material
            if m and m not in materials:
                # Material
                m.name = ".".join(m.name.split(".")[:-1])
                materials.append(m)
                if not m.node_tree:
                    continue
                done_nt = remove_suffix_from_node_tree_recursive(
                    m.node_tree, done_nt, delimiter
                )
        for mod in obj.modifiers:
            if not mod.type == "NODES":
                continue
            if not mod.node_group:
                continue
            if mod.node_group in done_geonodes:
                continue
            mod.node_group.name = ".".join(mod.node_group.name.split(".")[:-1])
            done_geonodes.append(mod.node_group)


def remove_suffix_from_collection_recursive(collection, done, delimiter="."):
    """Recursively remove a suffix to a hierarchy of collections."""
    if not collection in done:
        collection.name = ".".join(collection.name.split(".")[:-1])
        done += [collection]
    for child in collection.children:
        done = remove_suffix_from_collection_recursive(child, done, delimiter)
    return done


def remove_suffix_from_node_tree_recursive(node_tree, done, delimiter="."):
    """Recursively remove a suffix from this node tree and all node trees within."""
    if not (node_tree in done or node_tree.library):
        if not node_tree.name.startswith("Shader Nodetree"):
            node_tree.name = ".".join(node_tree.name.split(".")[:-1])
            done += [node_tree]

        for n in node_tree.nodes:
            if n.type == "GROUP" and n.node_tree:
                if not n.node_tree in done:
                    done = remove_suffix_from_node_tree_recursive(
                        n.node_tree, done, delimiter
                    )
    return done


def add_suffix_to_hierarchy(collection, suffix=".tmp"):
    """Add a suffix to the names of all sub-collections, objects,
    materials and node groups of a collection."""

    add_suffix_to_collection_recursive(collection, suffix)

    materials = []

    for obj in collection.all_objects:
        # Object
        new_name = obj.name + suffix
        if new_name in bpy.data.objects:
            bad_object = bpy.data.objects[new_name]
            bad_object.name += ".old"
            print(
                f"Warning: Object {new_name} with suffix already existed, added .old suffix."
            )

        obj.name = new_name
        if obj.data:
            # Object data
            obj.data.name += suffix
        for ms in obj.material_slots:
            m = ms.material
            if m and m not in materials:
                # Material
                m.name += suffix
                materials.append(m)
                if not m.node_tree:
                    continue
                add_suffix_to_node_tree_recursive(m.node_tree, suffix)
        for mod in obj.modifiers:
            if not mod.type == "NODES":
                continue
            if not mod.node_group:
                continue
            if not mod.node_group.name.endswith(suffix):
                mod.node_group.name += suffix

    return collection.all_objects


def add_suffix_to_collection_recursive(collection, suffix=".tmp"):
    """Recursively add a suffix to a hierarchy of collections and objects."""
    collection.name += suffix
    for child in collection.children:
        add_suffix_to_collection_recursive(child, suffix)


def add_suffix_to_node_tree_recursive(node_tree, suffix=".tmp"):
    """Recursively add a suffix to this node tree and all node trees within."""
    if not (
        node_tree.name.endswith(suffix)
        or node_tree.library
        or node_tree.name == "Shader Nodetree"
    ):
        node_tree.name += suffix

    for n in node_tree.nodes:
        if n.type == "GROUP" and n.node_tree and not n.node_tree.name.endswith(suffix):
            add_suffix_to_node_tree_recursive(n.node_tree, suffix)
