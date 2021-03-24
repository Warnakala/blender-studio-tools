import bpy
from .bz_util import zprefs_get, zsession_get, zsession_auth

class BZ_PT_vi3d_auth(bpy.types.Panel):
    bl_idname = 'panel.bz_auth'
    bl_category = "Blezou"
    bl_label = "Kitsu Login"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_order = 10

    def draw(self, context): 
        bz_prefs = context.preferences.addons['blezou'].preferences
        zsession = bz_prefs.session

        layout = self.layout

        box = layout.box()
        # box.row().prop(bz_prefs, 'host')
        box.row().prop(bz_prefs, 'email')
        box.row().prop(bz_prefs, 'passwd')

        row = layout.row(align=True)
        if not zsession.is_auth():
            row.operator('blezou.session_start', text='Login')
        else:
            row.operator('blezou.session_end', text='Logout')

class BZ_PT_vi3d_context(bpy.types.Panel):
    bl_idname = 'panel.bz_vi3d_context'
    bl_category = "Blezou"
    bl_label = "Context"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_options = {'DEFAULT_CLOSED'}
    bl_order = 20

    @classmethod
    def poll(cls, context):
        return zsession_auth(context)

    def draw(self, context): 
        bz_prefs = zprefs_get(context)
        layout = self.layout

        # Production
        if not bz_prefs['project_active']:
            prod_load_text = 'Select Production'
        else:
            prod_load_text = bz_prefs['project_active']['name']

        box = layout.box()
        row = box.row(align=True)
        row.operator('blezou.productions_load', text=prod_load_text, icon='DOWNARROW_HLT')

        # Category
        row = box.row(align=True)
        if not bz_prefs['project_active']:
            row.enabled = False
        row.prop(bz_prefs,'category', expand=True)

        #Sequence
        row = box.row(align=True)
        seq_load_text = 'Select Sequence'
        if not bz_prefs['project_active']:
            row.enabled = False
        elif bz_prefs['sequence_active']:
            seq_load_text = bz_prefs['sequence_active']['name'] 
            # seq_load_text = 'Select Sequence'
        row.operator('blezou.sequences_load', text=seq_load_text, icon='DOWNARROW_HLT')

class BZ_PT_SQE_context(bpy.types.Panel):
    bl_idname = 'panel.bz_sqe_context'
    bl_category = "Blezou"
    bl_label = "Context"
    bl_space_type = 'SEQUENCE_EDITOR'
    bl_region_type = 'UI'
    bl_order = 10

    @classmethod
    def poll(cls, context):
        return zsession_auth(context)

    def draw(self, context): 
        bz_prefs = zprefs_get(context)
        layout = self.layout

        # Production
        if not bz_prefs['project_active']:
            prod_load_text = 'Select Production'
        else:
            prod_load_text = bz_prefs['project_active']['name']

        box = layout.box()
        row = box.row(align=True)
        row.operator('blezou.productions_load', text=prod_load_text, icon='DOWNARROW_HLT')

class BZ_PT_SQE_shot(bpy.types.Panel):
    bl_idname = 'panel.bz_sqe_shot'
    bl_category = "Blezou"
    bl_label = "Shot"
    bl_space_type = 'SEQUENCE_EDITOR'
    bl_region_type = 'UI'
    bl_order = 20

    @classmethod
    def poll(cls, context):
        return True 

    def draw(self, context):
        active_strip = context.scene.sequence_editor.active_strip.blezou
        
        layout = self.layout
        box = layout.box()
        row = box.row(align=True)
        row.prop(active_strip, 'sequence')
        row = box.row(align=True)
        row.prop(active_strip, 'shot')

class BZ_PT_SQE_sync(bpy.types.Panel):
    bl_idname = 'panel.bz_sqe_sync'
    bl_category = "Blezou"
    bl_label = "Sync"
    bl_space_type = 'SEQUENCE_EDITOR'
    bl_region_type = 'UI'
    bl_order = 30

    @classmethod
    def poll(cls, context):
        return zsession_auth(context)

    def draw(self, context):
        bz_prefs = zprefs_get(context)

        layout = self.layout
        row = layout.row(align=True)
        row.operator('blezou.sqe_scan_track_properties', text='Scan Sequence Editor')

        '''
        box = layout.box()
        row = box.row(align=True)
        row.prop(bz_prefs, 'sqe_track_props') #TODO: Dosn"t work blender complaints it does not exist, manualli in script editr i can retrieve it
        '''
# ---------REGISTER ----------

classes = [
    BZ_PT_vi3d_auth,
    BZ_PT_vi3d_context,
    BZ_PT_SQE_context,
    BZ_PT_SQE_shot,
    BZ_PT_SQE_sync
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)