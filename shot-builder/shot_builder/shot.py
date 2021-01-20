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


class Shot:
    kitsu_id = ""
    sequence_code = ""
    name = ""
    code = ""
    frames = 0
    frames_per_second = 24.0


class ShotRef:
    """
    Reference to an asset from an external system.
    """

    def __init__(self, name: str = "", code: str = ""):
        self.name = name
        self.code = code

    def sync_data(self, shot: Shot) -> None:
        pass