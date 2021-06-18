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

import typing


class Sequence:
    is_generic = False
    kitsu_id = ""
    name = ""
    code = ""

    def is_valid(self) -> bool:
        """
        Check if this sequence contains all data so it could be selected
        for shot building.

        When not valid it won't be shown in the shot selection field.
        """
        if not self.name:
            return False

        return True


class SequenceRef:
    """
    Reference to a sequence from an external system.
    """

    def __init__(self, name: str = "", code: str = ""):
        self.name = name
        self.code = code

    def sync_data(self, seqeunce: Sequence) -> None:
        pass
