import bpy 
from .z_auth import ZSession
from .bz_core import bz_prefs_clear_properties

class BZPreferences(bpy.types.AddonPreferences):
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

# ---------REGISTER ----------

classes = [
    BZPreferences
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    #additional setup
    bz_prefs_clear_properties(bpy.context)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)