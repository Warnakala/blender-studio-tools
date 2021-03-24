import bpy 
from .z_types import ZProductions, ZProject, ZSequence
from .bz_util import zsession_auth, zprefs_get, zsession_get
from .bz_core import ui_redraw

class BZ_OT_SessionStart(bpy.types.Operator):
    bl_idname = 'blezou.session_start'
    bl_label = 'Start Gazou Session'
    bl_options = {'INTERNAL'}

    @classmethod
    def poll(cls, context):
        return True 
        #TODO
        zsession = zsession_get(context)
        return zsession.valid_config()

    def execute(self, context):
        zsession = zsession_get(context)

        zsession.set_config(self.get_config(context))
        zsession.start() 
        return {'FINISHED'}

    def get_config(self, context):
        bz_prefs = zprefs_get(context)
        return {'email': bz_prefs.email, 'host': bz_prefs.host, 'passwd': bz_prefs.passwd}

class BZ_OT_SessionEnd(bpy.types.Operator):
    bl_idname = 'blezou.session_end'
    bl_label = 'End Gazou Session'
    bl_options = {'INTERNAL'}

    @classmethod
    def poll(cls, context):
        return zsession_auth(context)

    def execute(self, context):
        zsession = zsession_get(context)
        zsession.end() 
        return {'FINISHED'}

class BZ_OT_ProductionsLoad(bpy.types.Operator):
    """Select the tree context from the list"""
    bl_idname = 'blezou.productions_load'
    bl_label = "Productions Load"
    bl_options = {'INTERNAL'}
    bl_property = "enum_prop"

    def _get_productions(self, context):
        zproductions = ZProductions()
        enum_list = [(p.name.lower(), p.name, p.description if p.description else '') for p in zproductions.projects]
        return enum_list 

    enum_prop: bpy.props.EnumProperty(items=_get_productions)

    @classmethod
    def poll(cls, context):
        return zsession_auth(context)

    def execute(self, context):
        #update preferences 
        z_prefs = zprefs_get(context)
        z_prefs['project_active'] = ZProject(self.enum_prop).zdict
        ui_redraw()
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.invoke_search_popup(self)
        return {'FINISHED'}

class BZ_OT_SequencesLoad(bpy.types.Operator):
    """Select the tree context from the list"""
    bl_idname = 'blezou.sequences_load'
    bl_label = "Sequences Load"
    bl_options = {'INTERNAL'}
    bl_property = "enum_prop"

    def _get_sequences(self, context):
        z_prefs = zprefs_get(context)
        active_project = ZProject(z_prefs['project_active']['name'])

        enum_list = [(s.name.lower(), s.name, s.description if s.description else '') for s in active_project.get_sequences_all()]
        return enum_list 

    enum_prop: bpy.props.EnumProperty(items=_get_sequences)

    @classmethod
    def poll(cls, context):
        z_prefs = zprefs_get(context)
        active_project = z_prefs['project_active']

        if zsession_auth(context):
            if active_project:
                return True 
        return False 

    def execute(self, context):
        #update preferences 
        z_prefs = zprefs_get(context) 
        active_project = ZProject(z_prefs['project_active']['name'])

        #TODO: get sequence by id and set pref to 
        z_prefs['sequence_active'] = ZSequence(active_project, self.enum_prop).zdict
        ui_redraw()
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.invoke_search_popup(self)
        return {'FINISHED'}


# ---------REGISTER ----------

classes = [
    BZ_OT_SessionStart, 
    BZ_OT_SessionEnd, 
    BZ_OT_ProductionsLoad,
    BZ_OT_SequencesLoad
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)