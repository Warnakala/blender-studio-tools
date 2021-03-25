import bpy 
from .z_auth import ZSession
from .bz_util import zprefs_get
class BZPreferences(bpy.types.AddonPreferences):
    '''
    Addon preferences to blezou. Holds variables that are important for authentification. 
    During runtime new attributes are created that get initialized in: bz_prefs_init_properties()
    '''
    bl_idname = __package__

    host: bpy.props.StringProperty(
        name='host',
        default='',
        options={'HIDDEN', 'SKIP_SAVE'}
    )
    
    email: bpy.props.StringProperty(
        name='email',
        default='',
        options={'HIDDEN', 'SKIP_SAVE'}
    )

    passwd: bpy.props.StringProperty(
        name='passwd',
        default='',
        options={'HIDDEN', 'SKIP_SAVE'},
        subtype='PASSWORD'
    )
    category: bpy.props.EnumProperty(
        items=(
            ('ASSETS', "Assets", "Asset related tasks", 'FILE_3D', 0),
            ('SHOTS', "Shots", "Shot related tasks", 'FILE_MOVIE', 1),
            ),
        default='SHOTS')
    session: ZSession = ZSession() 

    def draw(self, context):
        layout = self.layout
        layout.label(text='Preferences for Blezou Addon')
        box = layout.box()
        box.row().prop(self, 'host')
        box.row().prop(self, 'email')
        box.row().prop(self, 'passwd')

def bz_prefs_init_properties(context):
    zprefs = zprefs_get(context)

    #TODO: is this the correct way to initialize dynamic properties? 
    # we need properties that can hold dicts/nested dicts as value

    #id properties
    zprefs['project_active'] = {}
    zprefs['sequence_active'] = {}
    zprefs['shot_active'] = {}
    zprefs['sqe_track_props'] = {}
    print('Bzpref Clear ran!')

# ---------REGISTER ----------

classes = [
    BZPreferences
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    #additional setup
    bz_prefs_init_properties(bpy.context)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)