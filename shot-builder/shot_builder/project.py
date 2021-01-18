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

import bpy

from shot_builder.task_type import *
from shot_builder.shot import Shot
from shot_builder.sequence import ShotSequence
from shot_builder.sys_utils import *
from shot_builder.connectors.default import DefaultConnector
from shot_builder.connectors.connector import Connector

from typing import *
import types

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
        self.task_types: List[TaskType] = []
        self.task_types_connector = DefaultConnector
        self.sequences: List[ShotSequence] = []
        self.shots_connector = DefaultConnector
        self.name = ""
        self.name_connector = DefaultConnector
        self.config: Dict[str, Any] = {}
        self.__sequence_lookup: Dict[str, ShotSequence] = {}
        self.__shot_lookup: Dict[str, Shot] = {}

    def __create_connector(self,
                           connector_cls: Type[Connector],
                           context: bpy.types.Context) -> Connector:
        preferences = context.preferences.addons[__package__].preferences
        return connector_cls(production=self, preferences=preferences)

    def __format_sequence_name(self, sequence: ShotSequence) -> str:
        return sequence.name

    def __format_shot_name(self, shot: Shot) -> str:
        return shot.name

    def __build_sequence_lookup(self) -> None:
        self.__sequence_lookup = {
            sequence.sequence_id: sequence for sequence in self.sequences
        }

    def __build_shot_lookup(self, shots: List[Shot]) -> None:
        self.__shot_lookup = {
            shot.shot_id: shot for shot in shots
        }

    def __link_shots_with_sequences(self, shots: List[Shot]) -> None:
        """
        """
        for shot in shots:
            parent_id = shot.parent_id
            if parent_id is None:
                continue
            sequence = self.__sequence_lookup.get(str(parent_id))
            if sequence is None:
                logger.warn(f"shot {shot} has no sequence")
                continue
            sequence.shots.append(shot)

    def get_task_type_items(self,
                            context: bpy.types.Context
                            ) -> List[Tuple[str, str, str]]:
        """
        Get the list of task types items to be used in an item function of a
        `bpy.props.EnumProperty`
        """
        if not self.task_types:
            connector = self.__create_connector(
                self.task_types_connector, context=context)
            self.task_types = connector.get_task_types()
        return [
            (task_type.name, task_type.name, task_type.name)
            for task_type in self.task_types
        ]

    def __ensure_sequences_loaded(self, context: bpy.types.Context) -> None:
        if not self.sequences:
            connector = self.__create_connector(
                self.shots_connector, context=context)
            sequences = connector.get_sequences()
            shots = connector.get_shots()

            self.sequences = sequences
            self.__build_sequence_lookup()
            self.__build_shot_lookup(shots)
            self.__link_shots_with_sequences(shots)

    def get_shot_items(self, context: bpy.types.Context) -> List[Tuple[str, str, str]]:
        """
        Get the list of shot items to be used in an item function of a
        `bpy.props.EnumProperty` to select a shot.
        """
        self.__ensure_sequences_loaded(context)
        items: List[Tuple[str, str, str]] = []
        for sequence in self.sequences:
            if not sequence.shots:
                continue
            items.append(("", self.__format_sequence_name(
                sequence), sequence.name))
            for shot in sequence.shots:
                items.append((shot.shot_id, self.__format_shot_name(
                    shot), shot.name))

        return items

    def get_name(self, context: bpy.types.Context) -> str:
        """
        Get the name of the production
        """
        if not self.name:
            connector = self.__create_connector(
                self.name_connector, context=context)
            self.name = connector.get_name()
        return self.name

    # TODO: Use visitor pattern.
    def __load_name(self, main_config_mod: types.ModuleType) -> None:
        name = getattr(main_config_mod, "PRODUCTION_NAME", None)
        if name is None:
            return

        # Extract task types from a list of strings
        if isinstance(name, str):
            self.name = name
            return

        if issubclass(name, Connector):
            self.name = ""
            self.name_connector = name
            return

        logger.warn(
            "Skip loading of production name. Incorrect configuration detected.")

    def __load_task_types(self, main_config_mod: types.ModuleType) -> None:
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
            "Skip loading of task_types. Incorrect configuration detected.")

    def __load_shots(self, main_config_mod: types.ModuleType) -> None:
        shots = getattr(main_config_mod, "SHOTS", None)
        if shots is None:
            return

        if issubclass(shots, Connector):
            self.sequences = []
            self.shots_connector = shots
            return

        logger.warn(
            "Skip loading of shots. Incorrect configuration detected")

    def __load_connector_keys(self, main_config_mod: types.ModuleType) -> None:
        connectors = set()
        for attrname in Production.__ATTRNAMES_SUPPORTING_CONNECTOR:
            connector = getattr(self, f"{attrname}_connector")
            connectors.add(connector)

        connector_keys = set()
        for connector in connectors:
            for key in connector.PRODUCTION_KEYS:
                connector_keys.add(key)

        for connector_key in connector_keys:
            if hasattr(main_config_mod, connector_key):
                self.config[connector_key] = getattr(
                    main_config_mod, connector_key)

    def _load_config(self, main_config_mod: types.ModuleType) -> None:
        self.__load_name(main_config_mod)
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
