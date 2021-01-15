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

import pathlib
import logging
import importlib
from typing import *

import bpy

from shot_builder.task_type import *
from shot_builder.sys_utils import *
from shot_builder.connectors.default import DefaultConnector
from shot_builder.connectors.connector import Connector


logger = logging.getLogger(__name__)


class Production():
    """
    Class containing data and methods for a production.

    # Data members #
    path: contains the path to the root of the production.
    task_types: contains a list of `TaskType`s or a Connector to retrieve that are defined for this
        production. By default the task_types are prefilled with anim and light.
    name: human readable name of the production.

    """

    __ATTRNAMES_SUPPORTING_CONNECTOR = ['task_types', 'shots', 'name']

    def __init__(self, production_path: pathlib.Path):
        self.path = production_path
        self.task_types = DefaultConnector
        self.shots = DefaultConnector
        self.name = "Unnamed production"
        self.config = {}

    def __create_connector(self,
                           connector_cls: Type[Connector],
                           context: bpy.types.Context) -> Connector:
        preferences = context.preferences.addons[__package__].preferences
        return connector_cls(production=self, preferences=preferences)

    def get_task_type_items(self,
                            context: bpy.types.Context
                            ) -> List[Tuple[str, str, str]]:
        """
        Get the list of task types items to be used in an item function of a
        `bpy.props.EnumProperty`
        """
        task_types: Union[List[TaskType], Type[Connector]] = self.task_types
        if not isinstance(task_types, list):
            assert(issubclass(task_types, Connector))
            connector = self.__create_connector(task_types, context=context)
            task_types = connector.get_task_types()

        return [
            (task_type.name, task_type.name, task_type.name)
            for task_type in task_types
        ]

    def get_shot_items(self, context: bpy.types.Context) -> List[Tuple[str, str, str]]:
        """
        Get the list of shot items to be used in an item function of a
        `bpy.props.EnumProperty`
        """
        shots: Union[List[Shot], Type[Connector]] = self.shots
        if not isinstance(shots, list):
            assert(issubclass(shots, Connector))
            connector = self.__create_connector(shots, context=context)
            shots = connector.get_shots()

        return [
            (shot.name, shot.name, shot.name)
            for shot in shots
        ]

    def __load_task_types(self, main_config_mod):
        task_types = getattr(main_config_mod, "TASK_TYPES", None)
        if task_types is None:
            return

        # Extract task types from a list of strings
        if isinstance(task_types, list):
            self.task_types = [TaskType(task_type) for task_type in task_types]
            return

        if issubclass(task_types, Connector):
            self.task_types = task_types

        logger.warn(
            "Skip loading of task_types. Incorrect configuration detected (task_types)")

    def __load_shots(self, main_config_mod):
        shots = getattr(main_config_mod, "SHOTS", None)
        if shots is None:
            return

        # Extract task types from a list of strings
        if isinstance(shots, list):
            self.shots = [Shot(shot_id) for shot_id in shots]
            return

        if issubclass(shots, Connector):
            self.shots = shots

        logger.warn(
            "Skip loading of shots. Incorrect configuration detected (shots)")

    def __load_connector_keys(self, main_config_mod):
        connectors = set()
        for attrname in Production.__ATTRNAMES_SUPPORTING_CONNECTOR:
            attr = getattr(self, attrname)
            if isinstance(attr, Type) and issubclass(attr, Connector):
                connectors.add(attr)

        connector_keys = set()
        for connector in connectors:
            for key in connector.PRODUCTION_KEYS:
                connector_keys.add(key)

        for connector_key in connector_keys:
            if hasattr(main_config_mod, connector_key):
                self.config[connector_key] = getattr(
                    main_config_mod, connector_key)

    # TODO: what is the typing for a module. Unable to use `: module`
    def _load_config(self, main_config_mod):
        self.name = getattr(main_config_mod, "PRODUCTION_NAME", self.name)
        self.__load_task_types(main_config_mod)
        self.__load_shots(main_config_mod)
        self.__load_connector_keys(main_config_mod)


_PRODUCTION: Optional[Production] = None


def is_valid_production_root(path: pathlib.Path) -> bool:
    """
    Test if the given project path is configured correctly.

    A valid project path contains a subfolder with the name `shot-builder`
    holding configuration files.
    """
    if not path.is_absolute():
        return False
    if not path.exists():
        return False
    if not path.is_dir():
        return False
    config_file_path = get_production_config_file_path(path)
    return config_file_path.exists()


def get_production_config_dir_path(path: pathlib.Path) -> pathlib.Path:
    """
    Get the production configuration dir path.
    """
    return path / "shot-builder"


def get_production_config_file_path(path: pathlib.Path) -> pathlib.Path:
    """
    Get the production configuration file path.
    """
    return get_production_config_dir_path(path) / "config.py"


def _find_production_root(path: pathlib.Path) -> Optional[pathlib.Path]:
    """
    Given a path try to find the production root
    """
    if is_valid_production_root(path):
        return path
    try:
        parent_path = path.parents[0]
        return _find_production_root(parent_path)
    except IndexError:
        return None


# TODO: return type is optional
def get_production_root(context: bpy.types.Context) -> Optional[pathlib.Path]:
    """
    Determine the project root based on the current file.
    When current file isn't part of a project the project root
    configured in the add-on will be used.
    """
    current_file = pathlib.Path(bpy.data.filepath)
    production_root = _find_production_root(current_file)
    if production_root:
        return production_root
    production_root = pathlib.Path(
        context.preferences.addons[__package__].preferences.production_path)
    if is_valid_production_root(production_root):
        return production_root
    return None


def ensure_loaded_production(context: bpy.types.Context) -> bool:
    """
    Ensure that the production of the current context is loaded.

    Returns if the production of for the given context is loaded.
    """
    global _PRODUCTION
    production_root = get_production_root(context)
    if production_root is None:
        _PRODUCTION = None
        return False
    if _PRODUCTION and (_PRODUCTION.path == production_root):
        return True

    logger.debug(
        f"loading new production configuration from '{production_root}'.")
    return __load_production_configuration(context, production_root)


def __load_production_configuration(context: bpy.types.Context,
                                    production_path: pathlib.Path) -> bool:
    global _PRODUCTION
    _PRODUCTION = Production(production_path)
    paths = [production_path/"shot-builder"]
    with SystemPathInclude(paths) as _include:
        import config as production_config
        importlib.reload(production_config)
        _PRODUCTION._load_config(production_config)
        pass

    return False


def get_active_production() -> Production:
    global _PRODUCTION
    assert(_PRODUCTION)
    return _PRODUCTION
