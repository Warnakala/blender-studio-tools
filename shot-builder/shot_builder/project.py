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

import bpy


def is_valid_project_path(project_path: pathlib.Path) -> bool:
    """
    Test if the given project path is configured correctly.
    
    A valid project path contains a subfolder with the name `shot-builder`
    holding configuration files.
    """
    if not project_path.is_absolute():
        return False
    if not project_path.exists():
        return False
    if not project_path.is_dir():
        return False
    config_file_path = get_project_config_file_path(project_path)
    return config_file_path.exists()


def get_project_config_dir_path(project_path: pathlib.Path) -> pathlib.Path:
    """
    Get the project configuration dir path.
    """
    return project_path / "shot-builder"


def get_project_config_file_path(project_path: pathlib.Path) -> pathlib.Path:
    """
    Get the project configuration file path.
    """
    return get_project_config_dir_path(project_path) / "config.py"


def _find_production_root(path: pathlib.Path) -> pathlib.Path:
    if is_valid_project_path(path):
        return path
    try:
        parent_path = path.parents[0]
        return _find_production_root(parent_path)
    except IndexError:
        return None
    
# TODO: return type is optional
def get_production_root(context: bpy.types.Context) -> pathlib.Path:
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
        context.preferences.addons[__package__].preferences.project_path)
    if is_valid_project_path(production_root):
        return production_root
    return None
