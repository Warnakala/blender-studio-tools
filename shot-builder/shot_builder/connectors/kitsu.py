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
import bpy
from typing import List
from shot_builder.shot import Shot
from shot_builder.connectors.connector import Connector
import requests

import logging

logger = logging.getLogger(__name__)


class KitsuError(Exception):
    pass


class KitsuPreferences(bpy.types.PropertyGroup):
    username: bpy.props.StringProperty(
        name="Username",
        description="Username to connect to Kitsu",)
    password: bpy.props.StringProperty(
        name="Password",
        description="Password to connect to Kitsu",
        subtype='PASSWORD',)

    def draw(self, layout: bpy.types.UILayout, context: bpy.types.Context):
        layout.label(text="Kitsu")
        layout.prop(self, "username")
        layout.prop(self, "password")


class KitsuConnector(Connector):
    PRODUCTION_KEYS = {'KITSU_BACKEND', 'KITSU_PRODUCTION_ID'}

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.__jwt_access_token = ""
        self.__authorize()

    def __authorize(self):
        username = self._preferences.kitsu.username
        password = self._preferences.kitsu.password
        backend = self._production.config['KITSU_BACKEND']
        logger.info(f"authorize {username} against {backend}")
        response = requests.post(
            url=f"{backend}/auth/login", data={'email': username, 'password': password})
        if response.status_code != 200:
            self.__jwt_access_token = ""
            raise KitsuException(
                f"unable to authorize (status code={response.status_code})")
        json_response = response.json()
        self.__jwt_access_token = json_response['access_token']

    def get_shots(self) -> List[Shot]:
        return []
