# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

# <pep8 compliant>

from typing import List, Dict, Union, Any, Optional, Tuple, Generator

import bpy


def get_property_group_items(
    property_group: bpy.types.PropertyGroup,
) -> Generator[Tuple[str, bpy.types.Property], None, None]:

    for i in range(len(property_group.bl_rna.properties.items())):
        item = property_group.bl_rna.properties.items()[i]
        iname, iprop = item

        if iname in ["rna_type", "bl_rna", "name"]:
            continue

        yield item
