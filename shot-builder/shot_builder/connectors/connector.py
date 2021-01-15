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
from shot_builder.shot import Shot
from shot_builder.task_type import TaskType
from typing import List


class Connector:
    PRODUCTION_KEYS = set()
    # Local imports for type-info
    # TODO: Add type info (shot_builder.project.Production, shot_builder.properties.ShotBuilderPreferences)

    def __init__(self, production, preferences):
        self._production = production
        self._preferences = preferences

    def get_name(self) -> str:
        raise NotImplementedError(
            f"{self.__class__.__name__} does not support retrieval of production name")

    def get_task_types(self) -> List[TaskType]:
        raise NotImplementedError(
            f"{self.__class__.__name__} does not support retrieval of task types")

    def get_shots(self) -> List[Shot]:
        raise NotImplementedError(
            f"{self.__class__.__name__} does not support retrieval of shots")
