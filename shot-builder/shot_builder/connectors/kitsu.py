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
from shot_builder.shot import Shot, ShotRef
from shot_builder.asset import Asset, AssetRef
from shot_builder.task_type import TaskType
from shot_builder.render_settings import RenderSettings
from shot_builder.connectors.connector import Connector
import requests

import typing
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

    def draw(self, layout: bpy.types.UILayout, context: bpy.types.Context) -> None:
        layout.label(text="Kitsu")
        layout.prop(self, "backend")
        layout.prop(self, "username")
        layout.prop(self, "password")

    def _validate(self):
        if not (self.backend and self.username and self.password):
            raise KitsuException(
                "Kitsu connector has not been configured in the add-on preferences")


class KitsuDataContainer():
    def __init__(self, data: typing.Dict[str, typing.Optional[str]]):
        self._data = data

    def get_parent_id(self) -> typing.Optional[str]:
        return self._data['parent_id']

    def get_id(self) -> str:
        return str(self._data['id'])

    def get_name(self) -> str:
        return str(self._data['name'])

    def get_code(self) -> typing.Optional[str]:
        return self._data['code']

    def get_description(self) -> str:
        result = self._data['description']
        if result is None:
            return ""
        return result


class KitsuProject(KitsuDataContainer):
    def get_resolution(self) -> typing.Tuple[int, int]:
        """
        Get the resolution and decode it to (width, height)
        """
        res_str = str(self._data['resolution'])
        splitted = res_str.split("x")
        return (int(splitted[0]), int(splitted[1]))


class KitsuSequenceRef(ShotRef):
    def __init__(self, kitsu_id: str, name: str, code: str):
        super().__init__(name=name, code=code)
        self.kitsu_id = kitsu_id

    def sync_data(self, shot: Shot) -> None:
        shot.sequence_code = self.name


class KitsuShotRef(ShotRef):
    def __init__(self, kitsu_id: str, name: str, code: str, frames: int, frames_per_second: float, sequence: KitsuSequenceRef):
        super().__init__(name=name, code=code)
        self.kitsu_id = kitsu_id
        self.frames = frames
        self.frames_per_second = frames_per_second
        self.sequence = sequence

    def sync_data(self, shot: Shot) -> None:
        shot.name = self.name
        shot.code = self.code
        shot.kitsu_id = self.kitsu_id
        shot.frames = self.frames
        shot.frames_per_second = self.frames_per_second
        self.sequence.sync_data(shot)


class KitsuConnector(Connector):
    PRODUCTION_KEYS = {'KITSU_PROJECT_ID'}

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.__jwt_access_token = ""
        self.__validate()
        self.__authorize()

    def __validate(self) -> None:
        self._preferences.kitsu._validate()
        if not self._production.config.get('KITSU_PROJECT_ID'):
            raise KitsuException(
                "KITSU_PROJECT_ID is not configured in config.py")

    def __authorize(self) -> None:
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

    def __api_get(self, api: str) -> typing.Any:
        kitsu_pref = self._preferences.kitsu
        backend = kitsu_pref.backend

        response = requests.get(url=f"{backend}{api}", headers={
            "Authorization": f"Bearer {self.__jwt_access_token}"
        })
        if response.status_code != 200:
            raise KitsuException(
                f"unable to call kitsu (api={api}, status code={response.status_code})")
        return response.json()

    def __get_production_data(self) -> KitsuProject:
        project_id = self._production.config['KITSU_PROJECT_ID']
        production = self.__api_get(f"data/projects/{project_id}")
        project = KitsuProject(typing.cast(
            typing.Dict[str, typing.Any], production))
        return project

    def get_name(self) -> str:
        production = self.__get_production_data()
        return production.get_name()

    def get_task_types(self) -> typing.List[TaskType]:
        task_types = self.__api_get(f"data/task_types/")
        import pprint
        pprint.pprint(task_types)
        return []

    def get_shots(self) -> typing.List[ShotRef]:
        project_id = self._production.config['KITSU_PROJECT_ID']
        kitsu_sequences = self.__api_get(f"data/projects/{project_id}/sequences")
        sequence_lookup = {sequence_data['id']: KitsuSequenceRef(
            kitsu_id=sequence_data['id'],
            name=sequence_data['name'],
            code=sequence_data['code'],
        ) for sequence_data in kitsu_sequences}

        kitsu_shots = self.__api_get(f"data/projects/{project_id}/shots")
        return [KitsuShotRef(
            kitsu_id=shot_data['id'],
            name=shot_data['name'],
            code=shot_data['code'],
            frames_per_second=24.0,
            frames=int(shot_data['nb_frames'] or 0),
            sequence=sequence_lookup[shot_data['parent_id']]) for shot_data in kitsu_shots]

    def get_assets_for_shot(self, shot: Shot) -> typing.List[AssetRef]:
        kitsu_assets = self.__api_get(
            f"data/shots/{shot.kitsu_id}/assets")
        return [AssetRef(name=asset_data['name'], code=asset_data['code'])
                for asset_data in kitsu_assets]

    def get_render_settings(self, shot: Shot) -> RenderSettings:
        """
        Retrieve the render settings for the given shot.
        """
        kitsu_project = self.__get_production_data()
        resolution = kitsu_project.get_resolution()
        frames_per_second = shot.frames_per_second
        return RenderSettings(width=resolution[0], height=resolution[1], frames_per_second=frames_per_second)
