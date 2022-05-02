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

from .. import constants

logger = logging.getLogger("BSP")


def recursive_get_referenced_datablocks(data: Any, others=set()):
    """Return a set of all Blender datablocks referenced by this one.
    This was implemented in a rush, hopefully to be replaced soon by a Blender
    PyAPI function.
    """
    if data in others:
        return others

    # Build key/value pairs of python properties
    items = []
    for key in dir(data):
        if key in {'bl_rna', 'original', 'rna_type', 'id_data'}:
            continue
        value = getattr(data, key)
        if not value or callable(value):
            continue
        items.append((key, value))

    # Build key/value pairs of custom properties
    if isinstance(data, bpy.types.ID):
        if type(data) not in {bpy.types.PoseBone, bpy.types.Pose, bpy.types.ShaderNodeTree}:
            others.add(data)
        for key in data.keys():
            value = data[key]
            if value:
                items.append((key, value))

    # Go through the key/value pairs. Add values that are datablocks to the list.
    # Recurse into datablocks and lists that could contain datablocks.
    for key, value in items:
        if key in ['cycles', 'user', 'name', 'parent'] or key.startswith("__"):
            continue
        typ = type(value)

        if isinstance(value, bpy.types.ID) or isinstance(value, bpy.types.Pose):
            # print("Recurse into Datablock: ", key, value)
            recursive_get_referenced_datablocks(value, others)
        elif 'bpy_prop_collection_idprop' in str(typ):
            # print("Recurse into elements of CollectionProperty: ", key)
            for elem in value:
                recursive_get_referenced_datablocks(elem, others)
        elif isinstance(data, bpy.types.PropertyGroup):
            # print("Recurse into PropertyGroup: ", key)
            recursive_get_referenced_datablocks(value, others)

    # Special handling for certain types
    if type(data) == bpy.types.ShaderNodeTree:
        for node in data.nodes:
            recursive_get_referenced_datablocks(node, others)
    if type(data) == bpy.types.Collection:
        for object in data.objects:
            recursive_get_referenced_datablocks(object, others)
        for coll in data.children:
            recursive_get_referenced_datablocks(coll, others)
    if type(data) == bpy.types.Object:
        if data.type == 'ARMATURE':
            for bone in data.pose.bones:
                recursive_get_referenced_datablocks(bone, others)
                for c in bone.constraints:
                    recursive_get_referenced_datablocks(c, others)
        elif data.type == 'MESH':
            for m in data.modifiers:
                recursive_get_referenced_datablocks(m, others)
        for c in data.constraints:
            recursive_get_referenced_datablocks(c, others)

    return others

def remove_suffix_from_hierarchy(
    collection: bpy.types.Collection, delimiter: str = constants.DELIMITER
):
    """Removes the suffix after a set delimiter from all datablocks
    referenced by a collection, itself included"""

    others = set()
    datablocks = recursive_get_referenced_datablocks(collection, others)
    for db in datablocks:
        try:
            db.name = delimiter.join(db.name.split(delimiter)[:-1])
        except:
            pass

def add_suffix_to_hierarchy(collection: bpy.types.Collection, suffix: str):
    """Add a suffix to the names of all datablocks referenced by a collection,
    itself included."""

    others = set()
    datablocks = recursive_get_referenced_datablocks(collection, others)
    for db in datablocks:
        try:
            db.name += suffix
        except:
            pass
