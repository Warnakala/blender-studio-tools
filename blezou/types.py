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
    Has multiple constructor functions (by_name, by_id, init>by_dict)
    """

    id: str
    created_at: str = ""
    updated_at: str = ""
    name: str = ""
    code: Optional[str] = None
    description: Optional[str] = ""
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

    # SEQUENCES
    # ---------------

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
        return sorted(zsequences, key=lambda x: x.name)

    def create_sequence(self, sequence_name: str) -> ZSequence:
        # this function returns a seq dict even if seq already exists, it does not override
        seq_dict = gazu.shot.new_sequence(asdict(self), sequence_name, episode=None)
        return ZSequence(**seq_dict)

    # SHOT
    # ---------------

    def get_shot(self, shot_id: str) -> ZShot:
        return ZShot.by_id(shot_id)

    def get_shots_all(self) -> List[ZShot]:
        shots = [ZShot(**s) for s in gazu.shot.all_shots_for_project(asdict(self))]
        return sorted(shots, key=lambda x: x.name)

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

    def update_shot(self, zshot: ZShot) -> Dict[str, Any]:
        return gazu.shot.update_shot(asdict(zshot))  # type: ignore

    # ASSET TYPES
    # ---------------

    def get_all_asset_types(self) -> List[ZAssetType]:
        zassettypes = [
            ZAssetType(**at)
            for at in gazu.asset.all_asset_types_for_project(asdict(self))
        ]
        return sorted(zassettypes, key=lambda x: x.name)

    def get_asset_type_by_name(self, asset_type_name: str) -> Optional[ZAssetType]:
        return ZAssetType.by_name(asset_type_name)

    # ASSETS
    # ---------------

    def get_all_assets(self) -> List[ZAsset]:
        zassets = [ZAsset(**a) for a in gazu.asset.all_assets_for_project(asdict(self))]
        return sorted(zassets, key=lambda x: x.name)

    def get_asset_by_name(self, asset_name: str) -> Optional[ZAsset]:
        return ZAsset.by_name(self, asset_name)

    def get_all_assets_for_type(self, zassettype: ZAssetType) -> List[ZAsset]:
        zassets = [
            ZAsset(**a)
            for a in gazu.asset.all_assets_for_project_and_type(
                asdict(self), asdict(zassettype)
            )
        ]
        return sorted(zassets, key=lambda x: x.name)


@dataclass
class ZSequence:
    """
    Class to get object oriented representation of backend sequence data structure.
    Has multiple constructor functions (by_name, by_id, init>by_dict)
    """

    id: str
    created_at: str = ""
    updated_at: str = ""
    name: str = ""
    code: Optional[str] = None
    description: Optional[str] = ""
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
        shots = [
            ZShot(**shot) for shot in gazu.shot.all_shots_for_sequence(asdict(self))
        ]
        return sorted(shots, key=lambda x: x.name)


@dataclass
class ZAssetType:
    """
    Class to get object oriented representation of backend sequence data structure.
    Has multiple constructor functions (by_name, by_id, init>by_dict)
    """

    id: str = ""
    created_at: str = ""
    updated_at: str = ""
    name: str = ""
    type: str = ""

    @classmethod
    def by_name(cls, asset_type_name: str) -> Optional[ZAssetType]:
        # can return None if seq does not exist
        tpye_dict = gazu.asset.get_asset_type_by_name(asset_type_name)
        if tpye_dict:
            return cls(**tpye_dict)
        return None

    @classmethod
    def by_id(cls, type_id: str) -> ZAssetType:
        tpye_dict = gazu.asset.get_asset_type(type_id)
        return cls(**tpye_dict)


@dataclass
class ZShot:
    """
    Class to get object oriented representation of backend shot data structure.
    Has multiple constructor functions (by_name, by_id, init>by_dict)
    """

    id: str
    created_at: str = ""
    updated_at: str = ""
    name: str = ""
    canceled: bool = False
    code: Optional[str] = None
    description: Optional[str] = ""
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


@dataclass
class ZAsset:
    """
    Class to get object oriented representation of backend sequence data structure.
    Has multiple constructor functions (by_name, by_id, init>by_dict)
    """

    id: str
    created_at: str = ""
    updated_at: str = ""
    name: str = ""
    code: Optional[str] = None
    description: Optional[str] = ""
    shotgun_id: Optional[str] = None
    canceled: bool = False
    project_id: str = ""
    entity_type_id: str = ""
    parent_id: Optional[str] = None
    preview_file_id: str = ""
    type: str = ""
    project_name: str = ""
    asset_type_id: str = ""
    source_id: str = ""
    asset_type_name: str = ""
    episode_id: str = ""
    nb_frames: Optional[int] = None
    data: Dict[str, Any] = field(default_factory=dict)
    entities_out: List[Any] = field(default_factory=list)
    instance_casting: List[Any] = field(default_factory=list)
    entities_in: List[str] = field(default_factory=list)
    tasks: List[Dict[str, Any]] = field(default_factory=list)

    @classmethod
    def by_name(
        cls,
        project: ZProject,
        asset_name: str,
        asset_type: Optional[ZAssetType] = None,
    ) -> Optional[ZAsset]:

        # convert args to dict for api call
        project_dict = asdict(project)
        asset_type_dict = asdict(asset_type) if asset_type else asset_type

        # can return None if seq does not exist
        asset_dict = gazu.asset.get_asset_by_name(
            project_dict, asset_name, asset_type=asset_type_dict
        )
        if asset_dict:
            return cls(**asset_dict)
        return None

    @classmethod
    def by_id(cls, asset_id: str) -> ZAsset:
        asset_dict = gazu.asset.get_asset(asset_id)
        return cls(**asset_dict)


@dataclass
class ZTaskType:
    """
    Class to get object oriented representation of backend sequence data structure.
    Has multiple constructor functions (by_name, by_id, init>by_dict)
    """

    pid: str = ""
    created_at: str = ""
    updated_at: str = ""
    name: str = ""
    short_name: str = ""
    color: str = ""
    priority: int = 0
    for_shots: Optional[bool] = None
    for_entity: str = ""
    allow_timelog: bool = True
    shotgun_id: Optional[str] = None
    department_id: str = ""
    type: str = ""

    @classmethod
    def by_name(
        cls,
        task_type_name: str = "main",
    ) -> Optional[ZTaskType]:
        # can return None if seq does not exist
        task_type_dict = gazu.task.get_task_type_by_name(task_type_name)

        if task_type_dict:
            return cls(**task_type_dict)
        return None

    @classmethod
    def by_id(cls, task_type_id: str) -> ZTaskType:
        task_type_dict = gazu.task.get_task_type(task_type_id)
        return cls(**task_type_dict)


@dataclass
class ZTask:
    """
    Class to get object oriented representation of backend sequence data structure.
    Has multiple constructor functions (by_name, by_id, init>by_dict)
    """

    id: str = ""
    created_at: str = ""
    updated_at: str = ""
    name: str = ""
    description: Optional[str] = ""
    priority: int = 0
    duration: int = 0
    estimation: int = 0
    completion_rate: int = 0
    retake_count: int = 0
    sort_order: int = 0
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    due_date: Optional[str] = None
    real_start_date: Optional[str] = None
    last_comment_date: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    shotgun_id: Optional[str] = None
    project_id: str = ""
    task_type_id: str = ""
    task_status_id: str = ""
    entity_id: str = ""
    assigner_id: str = ""
    type: str = ""
    assignees: List[Dict[str, Any]] = field(default_factory=list)
    entity: Dict[str, Any] = field(default_factory=dict)  # entitity dict
    task_type: Dict[str, Any] = field(default_factory=dict)  # tastk type dict
    task_status: Dict[str, Any] = field(default_factory=dict)  # tastk status dict
    project: Dict[str, Any] = field(default_factory=dict)  # project dict
    entity_type: Dict[str, Any] = field(default_factory=dict)  # entity type dict
    persons: Dict[str, Any] = field(default_factory=dict)  # persons dict
    assigner: Dict[str, Any] = field(default_factory=dict)  # assiger dict
    sequence: Dict[str, Any] = field(default_factory=dict)  # sequence dict

    @classmethod
    def by_name(
        cls,
        zasset_zshot: Union[ZAsset, ZShot],
        ztask_type: ZTaskType,
        name: str = "main",
    ) -> Optional[ZTask]:

        # convert args to dict for api call
        asset_shotdict = asdict(zasset_zshot)
        task_type_dict = asdict(ztask_type)

        # can return None if seq does not exist
        task_dict = gazu.task.get_task_by_name(asset_shotdict, task_type_dict, name)

        if task_dict:
            return cls(**task_dict)
        return None

    @classmethod
    def by_id(cls, task_id: str) -> ZTask:
        task_dict = gazu.task.get_task(task_id)
        return cls(**task_dict)
