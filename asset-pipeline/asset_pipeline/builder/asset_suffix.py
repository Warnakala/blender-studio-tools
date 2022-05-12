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
from bpy_extras.id_map_utils import get_id_reference_map, get_all_referenced_ids

from .. import constants

logger = logging.getLogger("BSP")


def remove_suffix_from_hierarchy(
    collection: bpy.types.Collection, delimiter: str = constants.DELIMITER
):
    """Removes the suffix after a set delimiter from all datablocks
    referenced by a collection, itself included"""

    ref_map = get_id_reference_map()
    datablocks = get_all_referenced_ids(collection, ref_map)
    datablocks.add(collection)
    for db in datablocks:
        try:
            db.name = delimiter.join(db.name.split(delimiter)[:-1])
        except:
            pass


def add_suffix_to_hierarchy(collection: bpy.types.Collection, suffix: str):
    """Add a suffix to the names of all datablocks referenced by a collection,
    itself included."""

    ref_map = get_id_reference_map()
    datablocks = get_all_referenced_ids(collection, ref_map)
    datablocks.add(collection)
    for db in datablocks:
        try:
            db.name += suffix
        except:
            pass
