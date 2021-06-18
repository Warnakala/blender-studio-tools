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
"""
This module contains the Connector class. It is an abstract base class for concrete connectors.
"""

from shot_builder.shot import Shot, ShotRef
from shot_builder.sequence import Sequence, SequenceRef
from shot_builder.asset import Asset, AssetRef
from shot_builder.task_type import TaskType
from shot_builder.render_settings import RenderSettings
from typing import *


if TYPE_CHECKING:
    from shot_builder.project import Production
    from shot_builder.properties import ShotBuilderPreferences


class Connector:
    """
    A Connector is used to retrieve data from a source. This source can be an external system.

    Connectors can be configured for productions in its `shot-builder/config.py` file.

    # Members

    _production: reference to the production that we want to read data for.
    _preference: reference to the add-on preference to read settings for.
        Connectors can add settings to the add-on preferences.

    # Class Members

    PRODUCTION_KEYS: Connectors can register production configuration keys that will be loaded from the production config file.
        When keys are added the content will be read and stored in the production.

    # Usage

    Concrete connectors only overrides methods that they support. All non-overridden methods will raise an
    NotImplementerError.


    Example of using predefined connectors in a production config file:
        ```shot-builder/config.py
        from shot_builder.connectors.default import DefaultConnector
        from shot_builder.connectors.kitsu import KitsuConnector

        PRODUCTION_NAME = DefaultConnector
        TASK_TYPES = KitsuConnector
        KITSU_PROJECT_ID = "...."
        ```
    """
    PRODUCTION_KEYS: Set[str] = set()

    def __init__(self, production: 'Production', preferences: 'ShotBuilderPreferences'):
        self._production = production
        self._preferences = preferences

    def get_name(self) -> str:
        """
        Retrieve the production name using the connector.
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} does not support retrieval of production name")

    def get_task_types(self) -> List[TaskType]:
        """
        Retrieve the task types using the connector.
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} does not support retrieval of task types")

    def get_shots(self) -> List[ShotRef]:
        """
        Retrieve the shots using the connector.
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} does not support retrieval of shots")

    def get_sequences(self) -> List[SequenceRef]:
        """
        Retrieve the sequences using the connector.
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} does not support retrieval of sequences")


    def get_assets_for_shot(self, shot: Shot) -> List[AssetRef]:
        """
        Retrieve the sequences using the connector.
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} does not support retrieval of assets for a shot")

    def get_render_settings(self, shot: Shot) -> RenderSettings:
        """
        Retrieve the render settings for the given shot.
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} does not support retrieval of render settings for a shot")
