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
from blender_kitsu.shot_builder import vars
from blender_kitsu.shot_builder.shot import Shot, ShotRef
from blender_kitsu.shot_builder.asset import Asset, AssetRef
from blender_kitsu.shot_builder.task_type import TaskType
from blender_kitsu.shot_builder.render_settings import RenderSettings
from blender_kitsu.shot_builder.connectors.connector import Connector
import requests
from blender_kitsu import cache
from blender_kitsu.gazu.asset import all_assets_for_shot
from blender_kitsu.gazu.shot import all_shots_for_project, all_sequences_for_project

import typing
import logging

logger = logging.getLogger(__name__)


class KitsuException(Exception):
    pass


class KitsuPreferences(bpy.types.PropertyGroup):
    backend: bpy.props.StringProperty(  # type: ignore
        name="Server URL",
        description="Kitsu server address",
        default="https://kitsu.blender.cloud/api",
    )

    username: bpy.props.StringProperty(  # type: ignore
        name="Username",
        description="Username to connect to Kitsu",
    )

    password: bpy.props.StringProperty(  # type: ignore
        name="Password",
        description="Password to connect to Kitsu",
        subtype='PASSWORD',
    )

    def draw(self, layout: bpy.types.UILayout, context: bpy.types.Context) -> None:
        layout.label(text="Kitsu")
        layout.prop(self, "backend")
        layout.prop(self, "username")
        layout.prop(self, "password")

    def _validate(self):
        if not (self.backend and self.username and self.password):
            raise KitsuException(
                "Kitsu connector has not been configured in the add-on preferences"
            )


class KitsuDataContainer:
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
    def __init__(
        self,
        kitsu_id: str,
        name: str,
        code: str,
        frame_start: int,
        frames: int,
        frame_end: int,
        frames_per_second: float,
        sequence: KitsuSequenceRef,
    ):
        super().__init__(name=name, code=code)
        self.kitsu_id = kitsu_id
        self.frame_start = frame_start
        self.frames = frames
        self.frame_end = frame_end
        self.frames_per_second = frames_per_second
        self.sequence = sequence

    def sync_data(self, shot: Shot) -> None:
        shot.name = self.name
        shot.code = self.code
        shot.kitsu_id = self.kitsu_id
        shot.frame_start = self.frame_start
        shot.frames = self.frames
        shot.frame_end = self.frame_end
        shot.frames_per_second = self.frames_per_second
        self.sequence.sync_data(shot)


class KitsuConnector(Connector):
    PRODUCTION_KEYS = {'KITSU_PROJECT_ID'}

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def __get_production_data(self) -> KitsuProject:
        production = cache.project_active_get()
        project = KitsuProject(typing.cast(typing.Dict[str, typing.Any], production))
        return project

    def get_name(self) -> str:
        production = self.__get_production_data()
        return production.get_name()

    def get_task_types(self) -> typing.List[TaskType]:
        project = cache.project_active_get()
        task_types = project.task_types
        import pprint

        pprint.pprint(task_types)
        return []

    def get_shots(self) -> typing.List[ShotRef]:
        project = cache.project_active_get()
        kitsu_sequences = all_sequences_for_project(project.id)

        sequence_lookup = {
            sequence_data['id']: KitsuSequenceRef(
                kitsu_id=sequence_data['id'],
                name=sequence_data['name'],
                code=sequence_data['code'],
            )
            for sequence_data in kitsu_sequences
        }

        kitsu_shots = all_shots_for_project(project.id)
        shots: typing.List[ShotRef] = []

        for shot_data in kitsu_shots:
            # Initialize default values
            frame_start = vars.DEFAULT_FRAME_START
            frame_end = 0

            #  shot_data['data'] can be None
            if shot_data['data']:
                # If 3d_start key not found use default start frame.
                frame_start = int(
                    shot_data['data'].get('3d_start', vars.DEFAULT_FRAME_START)
                )
                frame_end = (
                    int(shot_data['data'].get('3d_start', vars.DEFAULT_FRAME_START))
                    + shot_data['nb_frames']
                    - 1
                )

            # If 3d_start and 3d_out available use that to calculate frames.
            # If not try shot_data['nb_frames'] or 0 -> invalid.
            frames = int(
                (frame_end - frame_start + 1)
                if frame_end
                else shot_data['nb_frames'] or 0
            )
            if frames < 0:
                logger.error(
                    "%s duration is negative: %i. Check frame range information on Kitsu",
                    shot_data['name'],
                    frames,
                )
                frames = 0

            shots.append(
                KitsuShotRef(
                    kitsu_id=shot_data['id'],
                    name=shot_data['name'],
                    code=shot_data['code'],
                    frame_start=frame_start,
                    frames=frames,
                    frame_end=frame_end,
                    frames_per_second=24.0,
                    sequence=sequence_lookup[shot_data['parent_id']],
                )
            )

        return shots

    def get_assets_for_shot(self, shot: Shot) -> typing.List[AssetRef]:
        kitsu_assets = all_assets_for_shot(shot.kitsu_id)

        return [
            AssetRef(name=asset_data['name'], code=asset_data['code'])
            for asset_data in kitsu_assets
        ]

    def get_render_settings(self, shot: Shot) -> RenderSettings:
        """
        Retrieve the render settings for the given shot.
        """
        project = cache.project_active_get()
        return RenderSettings(
            width=int(project.resolution.split('x')[0]),
            height=int(project.resolution.split('x')[1]),
            frames_per_second=project.fps,
        )
