from __future__ import annotations
from dataclasses import dataclass, asdict, field
from typing import Dict, Union, Union, Any, List, Optional
from .gazu import gazu
from .logger import ZLoggerFactory

logger = ZLoggerFactory.getLogger(__name__)

# TODO: @dataclass needs the init arguments to be known, what if gazu api changes?
# some properties are also only provided by gazu if they are initialized
class ZProductions:
    """
    Class to get object oriented representation of backend productions data structure.
    """

    def __init__(self):
        self._projects: List[ZProject] = []
        self._init_projects()

    @property
    def names(self) -> List[str]:
        _names = []
        for p in self._projects:
            _names.append(p.name)
        return _names

    @property
    def projects(self) -> List[ZProject]:
        return self._projects

    def _init_projects(self) -> None:
        for project in gazu.project.all_projects():
            self._projects.append(ZProject(**project))


@dataclass
class ZProject:
    """
    Class to get object oriented representation of backend project data structure.
    Can shortcut some functions from gazu api because active project is given through class instance.
    """

    id: str
    created_at: str = ""
    updated_at: str = ""
    name: str = ""
    code: Optional[str] = None
    description: str = ""
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
    def by_name(cls, project_name: str) -> Optional[ZProject]:
        # can return None if seq does not exist
        project_dict = gazu.project.get_project_by_name(project_name)
        if project_dict:
            return cls(**project_dict)
        return None

    @classmethod
    def by_id(cls, project_id: str) -> ZProject:
        project_dict = gazu.project.get_project(project_id)
        return cls(**project_dict)

    def get_sequence(self, seq_id: str) -> ZSequence:
        return ZSequence.by_id(seq_id)

    def get_sequence_by_name(
        self, seq_name: str, episode: Union[str, Dict[str, Any], None] = None
    ) -> Optional[ZSequence]:
        return ZSequence.by_name(self, seq_name, episode=episode)

    def get_sequences_all(self) -> List[ZSequence]:
        zsequences = [
            ZSequence(**s) for s in gazu.shot.all_sequences_for_project(asdict(self))
        ]
        return zsequences

    def get_shot(self, shot_id: str) -> ZShot:
        return ZShot.by_id(shot_id)

    def get_shot_by_name(self, zsequence: ZSequence, name: str) -> Optional[ZShot]:
        return ZShot.by_name(zsequence, name)

    def create_shot(
        self,
        shot_name: str,
        zsequence: ZSequence,
        frame_in: Optional[int] = None,
        frame_out: Optional[int] = None,
        data: Dict[str, Any] = {},
    ) -> ZShot:
        # this function returns a shot dict even if shot already exists, it does not override
        shot_dict = gazu.shot.new_shot(
            asdict(self),
            asdict(zsequence),
            shot_name,
            frame_in=frame_in,
            frame_out=frame_out,
            data=data,
        )
        return ZShot(**shot_dict)

    def create_sequence(self, sequence_name: str) -> ZSequence:
        # this function returns a seq dict even if seq already exists, it does not override
        seq_dict = gazu.shot.new_sequence(asdict(self), sequence_name, episode=None)
        return ZSequence(**seq_dict)

    def update_shot(self, zshot: ZShot) -> Dict[str, Any]:
        return gazu.shot.update_shot(asdict(zshot))


@dataclass
class ZSequence:
    id: str
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
    parent_id: Optional[str] = None
    source_id: Optional[str] = None
    preview_file_id: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    type: str = ""
    project_name: str = ""

    """
    Class to get object oriented representation of backend sequence data structure.
    Has multiple constructor functions (by_name, by_dict, init>by id)
    """

    @classmethod
    def by_name(
        cls,
        zproject: ZProject,
        seq_name: str,
        episode: Union[str, Dict[str, Any], None] = None,
    ) -> Optional[ZSequence]:
        # can return None if seq does not exist
        seq_dict = gazu.shot.get_sequence_by_name(
            asdict(zproject), seq_name, episode=episode
        )
        if seq_dict:
            return cls(**seq_dict)
        return None

    @classmethod
    def by_id(cls, seq_id: str) -> ZSequence:
        seq_dict = gazu.shot.get_sequence(seq_id)
        return cls(**seq_dict)

    def get_all_shots(self) -> List[ZShot]:
        shots = gazu.shot.all_shots_for_sequence(asdict(self))
        return [ZShot(**shot) for shot in shots]


@dataclass
class ZShot:
    """
    Class to get object oriented representation of backend shot data structure.
    Has multiple constructor functions (by_name, by_dict, init>by id)
    """

    id: str
    created_at: str = ""
    updated_at: str = ""
    name: str = ""
    canceled: bool = False
    code: Optional[str] = None
    description: str = ""
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
    def by_name(cls, zsequence: ZSequence, shot_name: str) -> Optional[ZShot]:
        # can return None if seq does not exist
        shot_dict = gazu.shot.get_shot_by_name(asdict(zsequence), shot_name)
        if shot_dict:
            return cls(**shot_dict)
        return None

    @classmethod
    def by_id(cls, shot_id: str) -> ZShot:
        shot_dict = gazu.shot.get_shot(shot_id)
        return cls(**shot_dict)
