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
from typing import *

import bpy

from shot_builder.task_type import *


logger = logging.getLogger(__name__)


class Production():
    """
    Class containing data and methods for a production.
    """
    def __init__(self, production_path: pathlib.Path):
        self.path = production_path
        self.task_types = []
        self.task_types.extend([TaskType('anim'), TaskType('light')])

    def get_task_types_items(self) -> list:
        """
        Get the list of task types items to be used in an item function of a
        `bpy.props.EnumProperty`
        """
        return [
            (task_type.name, task_type.name, task_type.name)
            for task_type in self.task_types
        ]
    

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
    
    logger.debug(f"loading new production configuration from '{production_root}'.")
    return __load_production_configuration(context, production_root)


def __load_production_configuration(context: bpy.types.Context,
                                    production_path: pathlib.Path) -> bool:
    global _PRODUCTION
    _PRODUCTION = Production(production_path)
    return False


def get_active_production() -> Production:
    global _PRODUCTION
    assert(_PRODUCTION)
    return _PRODUCTION