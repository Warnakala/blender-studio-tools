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
import types
import pathlib


class Asset:
    def __init__(self, asset_id: str, code: str, name: str, description: str):
        self.asset_id = asset_id
        self.code = code
        self.name = name
        self.description = description
        self.config: typing.Optional[AssetConfig] = None

    def __str__(self) -> str:
        return self.name


class AssetConfig:
    """
    Container to hold data where the asset can be located in the production repository.

    path: absolute path to the blend file containing this asset.

    """
