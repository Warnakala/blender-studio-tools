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
import os
import logging
from typing import Optional, Any, Set, Tuple, List, Union
from pathlib import Path

import bpy


class ItemIsLocal(Exception):
    pass


def is_item_local(
    item: Union[bpy.types.Collection, bpy.types.Object, bpy.types.Camera]
) -> bool:
    # Local collection of blend file.
    if not item.override_library and not item.library:
        return True
    return False


def is_item_lib_override(
    item: Union[bpy.types.Collection, bpy.types.Object, bpy.types.Camera]
) -> bool:
    # Collection from libfile and overwritten.
    if item.override_library and not item.library:
        return True
    return False


def is_item_lib_source(
    item: Union[bpy.types.Collection, bpy.types.Object, bpy.types.Camera]
) -> bool:
    #  Source collection from libfile not overwritten.
    if not item.override_library and item.library:
        return True
    return False


def get_item_lib(
    item: Union[bpy.types.Collection, bpy.types.Object, bpy.types.Camera]
) -> bpy.types.Library:
    if is_item_local(item):
        # Local collection
        raise ItemIsLocal(f"{item} is local to this blend file. Cannot get lib.")

    if is_item_lib_source(item):
        # Source collection not overwritten.
        return item.library

    if is_item_lib_override(item):
        # Overwritten collection.
        return item.override_library.reference.library

    raise RuntimeError(f"Failed to get libfile for {item}")
