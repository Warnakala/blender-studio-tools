from __future__ import annotations
import requests

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Union

from .log import LoggerFactory

logger = LoggerFactory.getLogger()


class KitsuException(Exception):
    pass


class KitsuConnector:
    def __init__(self, preferences: "AS_AddonPreferences"):
        self._preferences = preferences
        self.__access_token = ""
        self.__validate()
        self.__authorize()

    def __validate(self) -> None:
        self._preferences.kitsu._validate()

    def __authorize(self) -> None:
        kitsu_pref = self._preferences.kitsu
        backend = kitsu_pref.backend
        email = kitsu_pref.email
        password = kitsu_pref.password

        logger.info(f"authorize {email} against {backend}")
        response = requests.post(
            url=f"{backend}/auth/login", data={"email": email, "password": password}
        )
        if response.status_code != 200:
            self.__access_token = ""
            raise KitsuException(
                f"unable to authorize (status code={response.status_code})"
            )
        json_response = response.json()
        self.__access_token = json_response["access_token"]

    def api_get(self, api: str) -> Any:
        kitsu_pref = self._preferences.kitsu
        backend = kitsu_pref.backend

        response = requests.get(
            url=f"{backend}{api}",
            headers={"Authorization": f"Bearer {self.__access_token}"},
        )
        if response.status_code != 200:
            raise KitsuException(
                f"unable to call kitsu (api={api}, status code={response.status_code})"
            )
        return response.json()

    @classmethod
    def fetch_first(
        cls, json_response: Dict[str, Any], filter: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:

        if not isinstance(json_response, list):
            raise ValueError(
                f"Failed to fetch one, excpected list object: {json_response}"
            )

        for item in json_response:
            matches = 0
            for f in filter:
                if f in item and item[f] == filter[f]:
                    matches += 1

            if matches == len(filter):
                return item

        logger.error("Filter had no match %s on json response.", str(filter))
        return None

    @classmethod
    def fetch_all(
        cls, json_response: Dict[str, Any], filter: Dict[str, Any]
    ) -> List[Dict[str, Any]]:

        if not isinstance(json_response, list):
            raise ValueError(
                f"Failed to fetch all, excpected list object: {json_response}"
            )

        valid_items: List[Dict[str, Any]] = []

        for item in json_response:
            matches = 0
            for f in filter:
                if f in item and item[f] == filter[f]:
                    matches += 1

            if matches == len(filter):
                valid_items.append(item)

        return valid_items


class ProjectList(KitsuConnector):
    """
    Class to get object oriented representation of backend productions data structure.
    """

    def __init__(self):
        self._projects: List[Project] = []
        self._init_projects()

    @property
    def names(self) -> List[str]:
        return [p.name for p in self._projects]

    @property
    def projects(self) -> List[Project]:
        return self._projects

    def _init_projects(self) -> None:
        api_url = "data/projects"

        for project in self.api_get(api_url):
            self._projects.append(Project(**project))


@dataclass
class Project(KitsuConnector):
    """
    Class to get object oriented representation of backend project data structure.
    Can shortcut some functions from gazu api because active project is given through class instance.
    Has multiple constructor functions (by_name, by_id, init>by_dict)
    """

    id: str = ""
    created_at: str = ""
    updated_at: str = ""
    name: str = ""
    code: Optional[str] = None
    description: Optional[str] = None
    shotgun_id: Optional[str] = None
    data: None = None
    has_avatar: bool = False
    fps: Optional[str] = None
    ratio: Optional[str] = None
    resolution: Optional[str] = None
    production_type: str = ""
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    man_days: Optional[str] = None
    nb_episodes: int = 0
    episode_span: int = 0
    project_status_id: str = ""
    type: str = ""
    project_status_name: str = ""
    file_tree: Dict[str, Any] = field(default_factory=dict)
    team: List[Any] = field(default_factory=list)
    asset_types: List[Any] = field(default_factory=list)
    task_types: List[Any] = field(default_factory=list)
    task_statuses: List[Any] = field(default_factory=list)

    @classmethod
    def by_id(cls, connector: KitsuConnector, project_id: str) -> Project:
        api_url = f"data/projects/{project_id}"
        project_dict = connector.api_get(api_url)
        return cls(**project_dict)

    # SEQUENCES
    # ---------------

    def get_sequence(self, connector: KitsuConnector, seq_id: str) -> Sequence:
        return Sequence.by_id(connector, seq_id)

    def get_sequence_by_name(
        self, connector: KitsuConnector, seq_name: str
    ) -> Optional[Sequence]:
        return Sequence.by_name(connector, self, seq_name)

    def get_sequences_all(self, connector: KitsuConnector) -> List[Sequence]:
        api_url = f"data/projects/{self.id}/sequences"
        seq_dicts = connector.api_get(api_url)

        sequences = [Sequence(**s) for s in seq_dicts]
        return sorted(sequences, key=lambda x: x.name)

    # SHOT
    # ---------------

    def get_shot(self, connector: KitsuConnector, shot_id: str) -> Shot:
        return Shot.by_id(connector, shot_id)

    def get_shots_all(self, connector: KitsuConnector) -> List[Shot]:
        api_url = f"data/projects/{self.id}/shots"
        shot_dicts = connector.api_get(api_url)

        shots = [Shot(**s) for s in shot_dicts]
        return sorted(shots, key=lambda x: x.name)

    def get_shot_by_name(
        self, connector: KitsuConnector, sequence: Sequence, name: str
    ) -> Optional[Shot]:
        all_shots = self.get_shots_all(connector)
        return Shot.by_name(connector, sequence, name)

    def __bool__(self):
        return bool(self.id)


@dataclass
class Sequence(KitsuConnector):
    """
    Class to get object oriented representation of backend sequence data structure.
    Has multiple constructor functions (by_name, by_id, init>by_dict)
    """

    id: str = ""
    created_at: str = ""
    updated_at: str = ""
    name: str = ""
    code: Optional[str] = None
    description: Optional[str] = None
    shotgun_id: Optional[str] = None
    canceled: bool = False
    nb_frames: Optional[int] = None
    project_id: str = ""
    entity_type_id: str = ""
    parent_id: str = ""
    source_id: Optional[str] = None
    preview_file_id: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    type: str = ""
    project_name: str = ""

    @classmethod
    def by_id(cls, connector: KitsuConnector, seq_id: str) -> Sequence:
        api_url = f"data/sequences/{seq_id}"
        seq_dict = connector.api_get(seq_id)
        return cls(**seq_dict)

    @classmethod
    def by_name(
        cls, connector: KitsuConnector, project: Project, seq_name: str
    ) -> Optional[Sequence]:
        api_url = f"data/projects/{project.id}/sequences"
        seq_dicts = connector.api_get(api_url)
        seq_dict = connector.fetch_first(seq_dicts, {"name": seq_name})

        # Can be None if name not found.
        if not seq_dict:
            return None

        return cls(**seq_dict)

    def __bool__(self):
        return bool(self.id)


@dataclass
class Shot(KitsuConnector):
    """
    Class to get object oriented representation of backend shot data structure.
    Has multiple constructor functions (by_name, by_id, init>by_dict
    """

    id: str = ""
    created_at: str = ""
    updated_at: str = ""
    name: str = ""
    canceled: bool = False
    code: Optional[str] = None
    description: Optional[str] = None
    entity_type_id: str = ""
    episode_id: Optional[str] = None
    episode_name: str = ""
    fps: str = ""
    frame_in: str = ""
    frame_out: str = ""
    nb_frames: int = 0
    parent_id: str = ""
    preview_file_id: Optional[str] = None
    project_id: str = ""
    project_name: str = ""
    sequence_id: str = ""
    sequence_name: str = ""
    source_id: Optional[str] = None
    shotgun_id: Optional[str] = None
    type: str = ""
    data: Dict[str, Any] = field(default_factory=dict)
    tasks: List[Dict[str, Any]] = field(default_factory=list)

    @classmethod
    def by_id(cls, connector: KitsuConnector, shot_id: str) -> Shot:
        api_url = f"data/shots/{shot_id}"
        shot_dict = connector.api_get(shot_id)
        return cls(**shot_dict)

    @classmethod
    def by_name(
        cls, connector: KitsuConnector, sequence: Sequence, shot_name: str
    ) -> Optional[Shot]:
        api_url = f"data/projects/{sequence.project_id}/shots"
        shot_dicts = connector.api_get(api_url)
        shot_dict = connector.fetch_first(
            shot_dicts, {"parent_id": sequence.id, "name": shot_name}
        )

        # Can be None if name not found.
        if not shot_dict:
            return None

        return cls(**shot_dict)

    def __bool__(self):
        return bool(self.id)
