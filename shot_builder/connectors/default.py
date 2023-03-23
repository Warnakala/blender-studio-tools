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
from shot_builder.shot import Shot, ShotRef
from shot_builder.asset import Asset, AssetRef
from shot_builder.task_type import TaskType
from shot_builder.render_settings import RenderSettings
from shot_builder.connectors.connector import Connector
from typing import *


class DefaultConnector(Connector):
    """
    Default connector is a connector that returns the defaults for the shot builder add-on.
    """

    def get_name(self) -> str:
        return "unnamed production"

    def get_shots(self) -> List[ShotRef]:
        return []

    def get_assets_for_shot(self, shot: Shot) -> List[AssetRef]:
        return []

    def get_task_types(self) -> List[TaskType]:
        return [TaskType("anim"), TaskType("lighting"), TaskType("comp"), TaskType("fx")]

    def get_render_settings(self, shot: Shot) -> RenderSettings:
        """
        Retrieve the render settings for the given shot.
        """
        return RenderSettings(width=1920, height=1080, frames_per_second=24.0)
