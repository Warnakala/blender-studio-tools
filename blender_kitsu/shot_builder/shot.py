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
    is_generic = False
    kitsu_id = ""
    sequence_code = ""
    name = ""
    code = ""
    frame_start = 0
    frames = 0
    # Frame_end will be stored for debugging only.
    frame_end = 0
    frames_per_second = 24.0
    file_path_format = "{production.path}/shots/{shot.sequence_code}/{shot.name}/{shot.name}.{task_type}.blend"
    file_path = ""

    def is_valid(self) -> bool:
        """
        Check if this shot contains all data so it could be selected
        for shot building.

        When not valid it won't be shown in the shot selection field.
        """
        if not self.name:
            return False

        if self.frames <= 0:
            return False

        return True


class ShotRef:
    """
    Reference to an asset from an external system.
    """

    def __init__(self, name: str = "", code: str = ""):
        self.name = name
        self.code = code

    def sync_data(self, shot: Shot) -> None:
        pass
