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
from shot_builder.connectors.connector import Connector
from typing import List


class DefaultConnector(Connector):
    def get_name(self) -> str:
        return "unnamed production"

    def get_shots(self) -> List[Shot]:
        return []

    def get_task_types(self) -> List[TaskType]:
        return [TaskType("anim"), TaskType("light")]
