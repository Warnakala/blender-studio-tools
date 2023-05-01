from .. import utils
from ..templates import *
import bpy

def settings_as_dict(settings):
    data = {}
    for setting in settings.motion_blur_settings:
        data[setting.name] = []
    return data

def apply_settings(data):
    ''' Deactivates deformation motion blur for objects in selected collections.
    '''
    if not data:
        return
    
    list_unique, list_all = utils.split_by_suffix(data.keys(), ':all')
    
    if 'Master Collection' in data.keys() or 'Scene Collection' in data.keys():
        for ob in bpy.data.objects:
            if ob.type == 'CAMERA':
                continue
            ob.cycles.use_motion_blur = False
        return
        
    for col in bpy.data.collections:
        for name_col in list_all:
            if not col.name.startswith(name_col):
                continue
            for ob in col.all_objects:
                if ob.type == 'CAMERA':
                    continue
                ob.cycles.use_motion_blur = False
        # unique names
        if not col.name in list_unique:
            continue
        for ob in col.all_objects:
            if ob.type == 'CAMERA':
                continue
            ob.cycles.use_motion_blur = False
    return

def load_settings(settings, data):
    while len(settings.motion_blur_settings) > 0:
        settings.motion_blur_settings.remove(0)
    
    for name in data.keys():
        value = data[name]
        new_setting = settings.motion_blur_settings.add()
        new_setting.name = name
        
    settings.motion_blur_settings_index = min(settings.motion_blur_settings_index, len(settings.motion_blur_settings)-1)
    return

class LOR_OT_motion_blur_settings_apply(bpy.types.Operator):
    """
    """
    bl_idname = "lighting_overrider.motion_blur_settings_apply"
    bl_label = "Apply Motion Blur Settings"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        meta_settings = context.scene.LOR_Settings
        settings = utils.get_settings(meta_settings)
        
        apply_settings(settings_as_dict(settings))
        utils.kick_evaluation()
        
        return {'FINISHED'}

class LOR_motion_blur_setting(LOR_subsetting):
    name: bpy.props.StringProperty(default='Collection Name')
    pass

class LOR_OT_motion_blur_settings_initialize(bpy.types.Operator):
    """
    """
    bl_idname = "lighting_overrider.motion_blur_settings_init"
    bl_label = "Add Active Collection"
    bl_options = {"REGISTER", "UNDO"}
    
    @classmethod
    def poll(cls, context):
        return bool(context.collection)
        
    def execute(self, context):
        meta_settings = context.scene.LOR_Settings
        settings = utils.get_settings(meta_settings)
        
        existing_names = [setting.name for setting in settings.motion_blur_settings]
        
        active_name = context.collection.name
        
        if not active_name in existing_names:
            new_setting = settings.motion_blur_settings.add()
            new_setting.name = active_name
            settings.is_dirty = True
        
        settings.motion_blur_settings_index = len(settings.motion_blur_settings)-1
        
        return {'FINISHED'}
    

class LOR_OT_motion_blur_setting_add(bpy.types.Operator):
    """
    """
    bl_idname = "lighting_overrider.motion_blur_setting_add"
    bl_label = "Add Motion Blur Setting"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        meta_settings = context.scene.LOR_Settings
        settings = utils.get_settings(meta_settings)
        new_setting = settings.motion_blur_settings.add()
        settings.is_dirty = True

        settings.motion_blur_settings_index = len(settings.motion_blur_settings)-1

        return {'FINISHED'}

class LOR_OT_motion_blur_setting_remove(bpy.types.Operator):
    """
    """
    bl_idname = "lighting_overrider.motion_blur_setting_remove"
    bl_label = "Remove Motion Blur Setting"
    bl_options = {"REGISTER", "UNDO"}
    
    @classmethod
    def poll(cls, context):
        meta_settings = context.scene.LOR_Settings
        settings = utils.get_settings(meta_settings)
        return len(settings.motion_blur_settings)>0
        
    def execute(self, context):
        meta_settings = context.scene.LOR_Settings
        settings = utils.get_settings(meta_settings)
        settings.motion_blur_settings.remove(settings.motion_blur_settings_index)
        settings.is_dirty = True
        
        if settings.motion_blur_settings_index >= len(settings.motion_blur_settings):
            settings.motion_blur_settings_index = len(settings.motion_blur_settings)-1
        return {'FINISHED'}

class LOR_UL_motion_blur_settings_list(LOR_UL_settings_list):
    
    def draw_item(
        self, context, layout, data, item, icon, active_data, active_propname, index):
        
        meta_settings = context.scene.LOR_Settings
        settings = utils.get_settings(meta_settings)
        
        row = layout.row()
        col = row.column()
        row = col.row(align=True)
        row.label(text='', icon='OUTLINER_COLLECTION')
        icon = 'WORLD' if item.name.endswith(':all') else 'MESH_CIRCLE'
        if item.name in ['Master Collection', 'Scene Collection']:
            icon = 'SHADING_SOLID'
        row.prop(item, "name", text='', icon=icon, emboss=False)
        
        col = row.column()
        if index == settings.motion_blur_settings_index:
            col.operator("lighting_overrider.motion_blur_setting_remove", icon='X', text="", emboss=False)
        else:
            col.label(text='', icon='BLANK1')
            
    def filter_items(self, context, data, propname):
        settings = getattr(data, propname)
        helper_funcs = bpy.types.UI_UL_list
        
        flt_flags = []
        flt_neworder = []
        
        if self.filter_name:
            flt_flags = helper_funcs.filter_items_by_name(self.filter_name, self.bitflag_filter_item, settings, "name",
                                                            reverse=self.use_filter_invert)
        
        return flt_flags, flt_neworder

class LOR_PT_motion_blur_settings_panel(bpy.types.Panel):
    bl_parent_id = "LOR_PT_lighting_overrider_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_label = "Motion Blur Settings"
    bl_category = 'Overrides'
    bl_options = {"DEFAULT_CLOSED"}
    
    def draw_header(self, context):
        self.layout.label(text='', icon='ONIONSKIN_ON')
        return
        
    def draw_header_preset(self, context):
        layout = self.layout
        col = layout.column()
        
        meta_settings = context.scene.LOR_Settings
        settings = utils.get_settings(meta_settings)
        
        col.enabled = False
        col.label(text=str(len(settings.motion_blur_settings)))
        return
    
    def draw(self, context):
        layout = self.layout
        
        meta_settings = context.scene.LOR_Settings
        settings = utils.get_settings(meta_settings)
        
        col_top = layout.column()
        if not meta_settings.enabled:
            col_top.enabled = False
        row = col_top.row()
        col = row.column()
        row = col.row()
        row.operator("lighting_overrider.motion_blur_settings_init", icon='SHADERFX')
        
        col = row.column()
        row = col.row(align=True)
        row.operator("lighting_overrider.motion_blur_setting_add", icon='ADD', text="")
        row.operator("lighting_overrider.motion_blur_setting_remove", icon='REMOVE', text="")
        
        row = col_top.row(align=True)
        col = row.column()
        col.template_list(
            "LOR_UL_motion_blur_settings_list",
            "",
            settings,
            "motion_blur_settings",
            settings,
            "motion_blur_settings_index",
            rows=2,
        )
        col.operator('lighting_overrider.motion_blur_settings_apply', icon='PLAY')
        return

panel_class = LOR_PT_motion_blur_settings_panel

classes = (
    LOR_motion_blur_setting,
    LOR_UL_motion_blur_settings_list,
    LOR_OT_motion_blur_setting_add,
    LOR_OT_motion_blur_setting_remove,
    LOR_OT_motion_blur_settings_initialize,
    LOR_OT_motion_blur_settings_apply,
    )

def register():
    for c in classes:
        bpy.utils.register_class(c)

def unregister():
    for c in classes:
        bpy.utils.unregister_class(c)
