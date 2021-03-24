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
    def __init__(self, name):
        self._zdict = gazu.project.get_project_by_name(name)
        self._init_from_dict(self._zdict)
    
    def get_sequences_all(self):
        zsequences = [ZSequence(self, s['name']) for s in gazu.shot.all_sequences_for_project(self.zdict)]
        return zsequences

    def get_sequence(self, name='', seq_id=''):
        if not name and not seq_id:
            raise ValueError('Please provide either a name or a seq_id')
        if seq_id:
            gazu.shot.get_sequence(seq_id)
            return None 
            # return ZSequence(seq_id)
        
class ZSequence(ZObject):
    def __init__(self, zproject, name, episode=None):
        self._zdict = gazu.shot.get_sequence_by_name(zproject.zdict, name, episode=episode)
        self._init_from_dict(self._zdict)

    '''
    @classmethod
    def fromid(cls, seq_id):
        return 
    '''

