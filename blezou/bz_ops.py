import bpy 
from .z_types import ZProductions, ZProject, ZSequence
from .bz_util import zsession_auth, zprefs_get, zsession_get
from .bz_core import ui_redraw
from .logger import ZLoggerFactory

logger = ZLoggerFactory.getLogger(__name__)
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

        enum_list = [(s.id, s.name, s.description if s.description else '') for s in active_project.get_sequences_all()]
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

        z_prefs['sequence_active'] = ZSequence(self.enum_prop).zdict
        ui_redraw()
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.invoke_search_popup(self)
        return {'FINISHED'}

class BZ_OT_SQE_ScanTrackProps(bpy.types.Operator):
    """Select the tree context from the list"""
    bl_idname = 'blezou.sqe_scan_track_properties'
    bl_label = "SQE Scan Track Properties"
    bl_options = {'INTERNAL'}

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        z_prefs = zprefs_get(context) 

        #clear old prefs
        z_prefs['sqe_track_props'] = {}
        seq_dict = {}
        
        seq_editor = context.scene.sequence_editor
        
        for strip in seq_editor.sequences_all:
            strip_seq = strip.blezou.sequence
            strip_shot = strip.blezou.shot

            if strip_seq and strip_shot:
                #create seq if not exists 
                if strip_seq not in seq_dict: 
                    seq_dict[strip_seq] = {'shots':{}}

                shot_dict = {'sequence_name': strip_seq, 'frame_in': strip.frame_final_start, 'frame_out': strip.frame_final_end}

                #update seq dict with shot 
                seq_dict[strip_seq]['shots'][strip_shot] = shot_dict

                #TODO: order dictionary 

        z_prefs['sqe_track_props'] = seq_dict 
        logger.info(f'Result of scan: \n{seq_dict}')

        # ui_redraw()
        return {'FINISHED'}

class BZ_OT_SQE_SyncTrackProps(bpy.types.Operator):
    """Select the tree context from the list"""
    bl_idname = 'blezou.sqe_sync_track_properties'
    bl_label = "SQE Sync Track Properties"
    bl_options = {'INTERNAL'}

    @classmethod
    def poll(cls, context):
        z_prefs = zprefs_get(context)
        active_project = z_prefs['project_active']

        if zsession_auth(context):
            if active_project:
                return True 
        return False 

    def execute(self, context):
        z_prefs = zprefs_get(context) 
        active_project = ZProject(z_prefs['project_active']['name'])
        track_props = z_prefs['sqe_track_props']

        if not track_props: 
            logger.exception(f'No data to push to: {z_prefs.host}')
            return {'FINISHED'}

        logger.info(f'Pushing data to: {z_prefs.host}')
        #TODO: add popup confirmation dialog before syncin

        for seq_name in track_props:
            #check if seq already exists 
            existing_seq = active_project.get_sequence_by_name(seq_name) #returns None if not existent
            if existing_seq: 
                zsequence = existing_seq
                logger.info(f'Sequence already exists: {seq_name}. Skip.')
            else:
                #push new seq 
                zsequence = active_project.create_sequence(seq_name)
                logger.info(f'Pushed new sequence: {seq_name}')

            for shot_name in track_props[seq_name]['shots']:
                frame_in = track_props[seq_name]['shots'][shot_name]['frame_in']
                frame_out = track_props[seq_name]['shots'][shot_name]['frame_out']

                #update shot if already exists
                existing_shot = active_project.get_shot_by_name(zsequence, shot_name) #returns None if not existent
                if existing_shot: 
                    existing_shot.data['frame_in'] = frame_in
                    existing_shot.zdict['data']['frame_in'] = frame_in #TODO: resolve this in ZObject

                    existing_shot.data['frame_out'] = frame_out
                    existing_shot.zdict['data']['frame_out'] = frame_out #TODO: resolve this in ZObject

                    active_project.update_shot(existing_shot)
                    logger.info(f'Pushed update to shot: {shot_name}')
                else:
                    #push shot
                    active_project.create_shot(shot_name, zsequence, frame_in=frame_in, frame_out=frame_out, data={})
                    logger.info(f'Pushed new shot: {shot_name}')

        return {'FINISHED'}



# ---------REGISTER ----------

classes = [
    BZ_OT_SessionStart, 
    BZ_OT_SessionEnd, 
    BZ_OT_ProductionsLoad,
    BZ_OT_SequencesLoad,
    BZ_OT_SQE_ScanTrackProps,
    BZ_OT_SQE_SyncTrackProps
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)