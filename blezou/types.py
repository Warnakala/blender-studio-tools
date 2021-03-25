from dataclasses import dataclass, asdict, field
from typing import Dict

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
        self._projects = []
        self._init_projects()

    @property
    def names(self):
        _names = []
        for p in self._projects:
            _names.append(p.name)
        return _names

    @property
    def projects(self):
        return self._projects

    def _init_projects(self):
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
    code: None = None
    description: str = ""
    shotgun_id: None = None
    data: None = None
    has_avatar: bool = False
    fps: None = None
    ratio: None = None
    resolution: None = None
    production_type: str = ""
    start_date: None = None
    end_date: None = None
    man_days: None = None
    nb_episodes: int = 0
    episode_span: int = 0
    project_status_id: str = ""
    type: str = ""
    project_status_name: str = ""
    file_tree: dict = field(default_factory=dict)
    team: list = field(default_factory=list)
    asset_types: list = field(default_factory=list)
    task_types: list = field(default_factory=list)
    task_statuses: list = field(default_factory=list)

    @classmethod
    def by_name(cls, project_name):
        # can return None if seq does not exist
        project_dict = gazu.project.get_project_by_name(project_name)
        if project_dict:
            return cls(**project_dict)

    @classmethod
    def by_id(cls, project_id):
        project_dict = gazu.project.get_project(project_id)
        return cls(**project_dict)

    def get_sequence(self, seq_id):
        return ZSequence.by_id(seq_id)

    def get_sequence_by_name(self, seq_name, episode=None):
        return ZSequence.by_name(self, seq_name, episode=episode)

    def get_sequences_all(self):
        zsequences = [
            ZSequence(**s) for s in gazu.shot.all_sequences_for_project(asdict(self))
        ]
        return zsequences

    def get_shot(self, shot_id):
        return ZShot.by_id(shot_id)

    def get_shot_by_name(self, zsequence, name):
        return ZShot.by_name(zsequence, name)

    def create_shot(
        self,
        shot_name: str,
        zsequence,
        frame_in: int = None,
        frame_out: int = None,
        data: dict = {},
    ):
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

    def create_sequence(self, sequence_name: str):
        # this function returns a seq dict even if seq already exists, it does not override
        seq_dict = gazu.shot.new_sequence(asdict(self), sequence_name, episode=None)
        return ZSequence(**seq_dict)

    def update_shot(self, zshot):
        return gazu.shot.update_shot(asdict(zshot))


@dataclass
class ZSequence:
    id: str
    created_at: str = ""
    updated_at: str = ""
    name: str = ""
    code: None = None
    description: None = None
    shotgun_id: None = None
    canceled: bool = False
    nb_frames: None = None
    project_id: str = ""
    entity_type_id: str = ""
    parent_id: None = None
    source_id: None = None
    preview_file_id: None = None
    data: None = None
    type: str = ""
    project_name: str = ""

    """
    Class to get object oriented representation of backend sequence data structure.
    Has multiple constructor functions (by_name, by_dict, init>by id)
    """

    @classmethod
    def by_name(cls, zproject, seq_name, episode=None):
        # can return None if seq does not exist
        seq_dict = gazu.shot.get_sequence_by_name(
            asdict(zproject), seq_name, episode=episode
        )
        if seq_dict:
            return cls(**seq_dict)

    @classmethod
    def by_id(cls, seq_id):
        seq_dict = gazu.shot.get_sequence(seq_id)
        return cls(**seq_dict)

    def get_all_shots(self):
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
    code: None = None
    description: str = ""
    entity_type_id: str = ""
    episode_id: None = None
    episode_name: str = ""
    fps: str = ""
    frame_in: str = ""
    frame_out: str = ""
    nb_frames: int = 0
    parent_id: str = ""
    preview_file_id: None = None
    project_id: str = ""
    project_name: str = ""
    sequence_id: str = ""
    sequence_name: str = ""
    source_id: None = None
    shotgun_id: None = None
    type: str = ""
    data: dict = field(default_factory=dict)
    tasks: list = field(default_factory=list)

    @classmethod
    def by_name(cls, zsequence, shot_name):
        # can return None if seq does not exist
        shot_dict = gazu.shot.get_shot_by_name(asdict(zsequence), shot_name)
        if shot_dict:
            return cls(**shot_dict)

    @classmethod
    def by_id(cls, shot_id):
        shot_dict = gazu.shot.get_shot(shot_id)
        return cls(**shot_dict)
