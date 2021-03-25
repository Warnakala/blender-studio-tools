from .gazu import gazu 

from .logger import ZLoggerFactory
logger=ZLoggerFactory.getLogger(__name__)

class ZObject():
    '''Mix in Class that provides basic attributes and functions'''
    id: str
    name: str 
    created_at: str
    updatet_at: str 
    _zdict: dict

    def _init_from_dict(self, dictionary) -> bool:
        #TODO: big issue i just realized if we update an attribute lets say: object.name = 'test' 
        # it's not reflected in object.zdict, how to solve this programmatically? 
        if not isinstance(dictionary, dict):
            logger.exception(f'Failed to init {self} from dict. Input is of type: {type(dictionary)}')
            return False

        for key in dictionary:
            setattr(self, key, dictionary[key])
        return True 

    @property
    def zdict(self):
        return self._zdict

class ZProductions(ZObject):
    '''
    Class to get object oriented representation of backend productions data structure. 
    '''
    def __init__(self):
        self._projects = []
        self._zdict = gazu.project.all_projects()
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
        for p in self._zdict:
            self._projects.append(ZProject(p['name']))

class ZProject(ZObject):
    '''
    Class to get object oriented representation of backend project data structure. 
    Can shortcut some functions from gazu api because active project is given through class instance. 
    '''
    def __init__(self, name):
        self._zdict = gazu.project.get_project_by_name(name)
        self._init_from_dict(self._zdict)

    def get_sequence(self, seq_id):
        return ZSequence(seq_id)
    
    def get_sequence_by_name(self, seq_name, episode=None):
        return ZSequence.by_name(self, seq_name, episode=episode)

    def get_sequences_all(self):
        zsequences = [ZSequence.by_dict(s) for s in gazu.shot.all_sequences_for_project(self.zdict)]
        return zsequences

    def get_shot(self, shot_id):
        return ZShot(shot_id)

    def get_shot_by_name(self, zsequence, name):
        return ZShot.by_name(zsequence, name)

    def create_shot(self, shot_name: str, zsequence, frame_in: int = None, frame_out: int = None, data: dict = {}):
        # this function returns a shot dict even if shot already exists, it does not override 
        shot_dict = gazu.shot.new_shot(
            self.zdict, 
            zsequence.zdict, 
            shot_name, 
            frame_in=frame_in, 
            frame_out=frame_out, 
            data=data
        )
        return ZShot.by_dict(shot_dict)

    def create_sequence(self, sequence_name: str):
        # this function returns a seq dict even if seq already exists, it does not override 
        seq_dict = gazu.shot.new_sequence(self.zdict, sequence_name, episode=None)
        return ZSequence.by_dict(seq_dict)
        
    def update_shot(self, zshot):
        return gazu.shot.update_shot(zshot.zdict)

class ZSequence(ZObject):
    '''
    Class to get object oriented representation of backend sequence data structure. 
    Has multiple constructor functions (by_name, by_dict, init>by id)
    '''

    def __init__(self, seq_id, zdict={}):
        #TODO: what happens on invalid id 
        if zdict: 
            self._zdict = zdict
            self._init_from_dict(self._zdict)
        else:
            self._zdict = gazu.shot.get_sequence(seq_id)
            self._init_from_dict(self._zdict)

    @classmethod
    def by_name(cls, zproject, name, episode=None):
        #returns None if not existent 
        seq_dict = gazu.shot.get_sequence_by_name(zproject.zdict, name, episode=episode)
        if not seq_dict: 
            return None 
        return cls(seq_dict['id'])

    @classmethod
    def by_dict(cls, seq_dict):
        return cls(seq_dict['id'], zdict=seq_dict)

    def get_all_shots(self):
        # [ZShot]
        shots = gazu.shot.all_shots_for_sequence(self.zdict)

class ZShot(ZObject):
    '''
    Class to get object oriented representation of backend shot data structure. 
    Has multiple constructor functions (by_name, by_dict, init>by id)
    '''
    def __init__(self, shot_id, zdict={}):
        #TODO: what happens on invalid id 
        if zdict: 
            self._zdict = zdict
            self._init_from_dict(self._zdict)
        else:
            self._zdict = gazu.shot.get_shot(shot_id)
            self._init_from_dict(self._zdict)

    @classmethod
    def by_name(cls, zsequence, name):
        #returns None if not existent 
        shot_dict = gazu.shot.get_shot_by_name(zsequence.zdict, name)
        if not shot_dict: 
            return None 
        return cls(shot_dict['id'])

    @classmethod
    def by_dict(cls, shot_dict):
        return cls(shot_dict['id'], zdict=shot_dict)
    


