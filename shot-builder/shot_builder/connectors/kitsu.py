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
from typing import *
from shot_builder.shot import Shot
from shot_builder.task_type import TaskType
from shot_builder.connectors.connector import Connector
import requests

import logging

logger = logging.getLogger(__name__)


class KitsuException(Exception):
    pass


class KitsuPreferences(bpy.types.PropertyGroup):
    backend: bpy.props.StringProperty(  # type: ignore
        name="Server URL",
        description="Kitsu server address",
        default="https://kitsu.blender.cloud/api")

    username: bpy.props.StringProperty(  # type: ignore
        name="Username",
        description="Username to connect to Kitsu",)

    password: bpy.props.StringProperty(  # type: ignore
        name="Password",
        description="Password to connect to Kitsu",
        subtype='PASSWORD',)

    def draw(self, layout: bpy.types.UILayout, context: bpy.types.Context):
        layout.label(text="Kitsu")
        layout.prop(self, "backend")
        layout.prop(self, "username")
        layout.prop(self, "password")


class KitsuConnector(Connector):
    PRODUCTION_KEYS = {'KITSU_BACKEND', 'KITSU_PROJECT_ID'}

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.__jwt_access_token = ""
        self.__authorize()

    def __authorize(self):
        kitsu_pref = self._preferences.kitsu
        backend = kitsu_pref.backend
        username = kitsu_pref.username
        password = kitsu_pref.password

        logger.info(f"authorize {username} against {backend}")
        response = requests.post(
            url=f"{backend}/auth/login", data={'email': username, 'password': password})
        if response.status_code != 200:
            self.__jwt_access_token = ""
            raise KitsuException(
                f"unable to authorize (status code={response.status_code})")
        json_response = response.json()
        self.__jwt_access_token = json_response['access_token']

    def __api_get(self, api: str) -> Any:
        kitsu_pref = self._preferences.kitsu
        backend = kitsu_pref.backend

        response = requests.get(url=f"{backend}{api}", headers={
            "Authorization": f"Bearer {self.__jwt_access_token}"
        })
        if response.status_code != 200:
            raise KitsuException(
                f"unable to call kitsu (api={api}, status code={response.status_code})")
        return response.json()

    def get_name(self) -> str:
        project_id = self._production.config['KITSU_PROJECT_ID']
        production = self.__api_get(f"data/projects/{project_id}")
        return str(production['name'])

    def get_task_types(self) -> List[TaskType]:
        task_types = self.__api_get(f"data/task_types/")
        import pprint
        pprint.pprint(task_types)
        return []

    def get_shots(self) -> List[Shot]:
        project_id = self._production.config['KITSU_PROJECT_ID']
        kitsu_shots = self.__api_get(f"data/projects/{project_id}/shots")
        return [
            Shot(kitsu_shot['name']) for kitsu_shot in kitsu_shots
        ]
