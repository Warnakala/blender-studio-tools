from .. import utils
from ..templates import *
import bpy

def settings_as_dict(settings):
    data = {}
    for setting in settings.variable_settings:
        if isinstance(getattr(setting, setting.type), str):
            data[setting.name] = [getattr(setting, setting.type), setting.type]
        elif not setting.bl_rna.properties[setting.type].is_array:
            data[setting.name] = [getattr(setting, setting.type), setting.type]
        else:
            data[setting.name] = [getattr(setting, setting.type)[:], setting.type]
    return data

def apply_settings(data):
    ''' Applies settings to according nodes in the variables nodegroup.
    '''
    if not data:
        return
    
    for ng in bpy.data.node_groups:
        if not ng.name == 'VAR-settings':
            continue
        for name in data:
            node = ng.nodes.get(name)
            if node:
                node.outputs[0].default_value = data[name][0]
            else:
                print(f'Warning: Node {set} in variable settings nodegroup not found.')
    return


def load_settings(settings, data):
    while len(settings.variable_settings) > 0:
        settings.variable_settings.remove(0)
    
    for name in data.keys():
        value = data[name]
        new_setting = settings.variable_settings.add()
        new_setting.name = name
        new_setting.type = value[1]
        setattr(new_setting, value[1], value[0])
        
    settings.variable_settings_index = min(settings.variable_settings_index, len(settings.variable_settings)-1)
    return

class LOR_OT_variable_settings_apply(bpy.types.Operator):
    """
    """
    bl_idname = "lighting_overrider.variable_settings_apply"
    bl_label = "Apply Variable Settings"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        meta_settings = context.scene.LOR_Settings
        settings = utils.get_settings(meta_settings)
        
        apply_settings(settings_as_dict(settings))
        utils.kick_evaluation()
        
        return {'FINISHED'}

class LOR_variable_setting(LOR_subsetting):
    pass
    

class LOR_OT_variable_settings_initialize(bpy.types.Operator):
    """
    """
    bl_idname = "lighting_overrider.variable_settings_init"
    bl_label = "Initialize from Selection"
    bl_options = {"REGISTER", "UNDO"}
    
    @classmethod
    def poll(cls, context):
        return bool(bpy.data.node_groups.get('VAR-settings'))
        
    def execute(self, context):
        meta_settings = context.scene.LOR_Settings
        settings = utils.get_settings(meta_settings)
        
        existing_names = [setting.name for setting in settings.variable_settings]
        
        ng = bpy.data.node_groups.get('VAR-settings')
        if not ng:
            return {'CANCELLED'}
        
        for node in ng.nodes:
            if node.name in ['Group Input', 'Group Output', 'Math', 'Map Range']+existing_names:
                continue
            new_setting = settings.variable_settings.add()
            new_setting.name = node.name
            value = node.outputs[0].default_value
            if '__len__' in dir(value):
                new_setting.type = 'COLOR'
                setattr(new_setting, new_setting.type, value[:])
            else:
                new_setting.type = 'VALUE'
                setattr(new_setting, new_setting.type, value)
            settings.is_dirty = True
        
        settings.variable_settings_index = len(settings.variable_settings)-1
        
        return {'FINISHED'}
    

class LOR_OT_variable_setting_add(bpy.types.Operator):
    """
    """
    bl_idname = "lighting_overrider.variable_setting_add"
    bl_label = "Add Variable Setting"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        meta_settings = context.scene.LOR_Settings
        settings = utils.get_settings(meta_settings)
        new_setting = settings.variable_settings.add()
        settings.is_dirty = True

        settings.variable_settings_index = len(settings.variable_settings)-1

        return {'FINISHED'}

class LOR_OT_variable_setting_remove(bpy.types.Operator):
    """
    """
    bl_idname = "lighting_overrider.variable_setting_remove"
    bl_label = "Remove Variable Setting"
    bl_options = {"REGISTER", "UNDO"}
    
    @classmethod
    def poll(cls, context):
        meta_settings = context.scene.LOR_Settings
        settings = utils.get_settings(meta_settings)
        return len(settings.variable_settings)>0
        
    def execute(self, context):
        meta_settings = context.scene.LOR_Settings
        settings = utils.get_settings(meta_settings)
        settings.variable_settings.remove(settings.variable_settings_index)
        settings.is_dirty = True
        
        if settings.variable_settings_index >= len(settings.variable_settings):
            settings.variable_settings_index = len(settings.variable_settings)-1
        return {'FINISHED'}

class LOR_UL_variable_settings_list(LOR_UL_settings_list):
    
    def draw_item(
        self, context, layout, data, item, icon, active_data, active_propname, index):
        
        meta_settings = context.scene.LOR_Settings
        settings = utils.get_settings(meta_settings)
        
        row = layout.row()
        col = row.column()
        row = col.row(align=True)
        row.prop(item, "name", text='', icon='DOT', emboss=False)
        row.prop(item, item.type, text='')
        row.prop(item, 'type', text='', icon='THREE_DOTS', icon_only=True, emboss=False)
        
        col = row.column()
        if index == settings.variable_settings_index:
            col.operator("lighting_overrider.variable_setting_remove", icon='X', text="", emboss=False)
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

class LOR_PT_variable_settings_panel(bpy.types.Panel):
    bl_parent_id = "LOR_PT_lighting_overrider_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_label = "Variable Settings"
    bl_category = 'Overrides'
    bl_options = {"DEFAULT_CLOSED"}
    
    def draw_header(self, context):
        layout = self.layout
        layout.label(text='', icon='LIGHT_SUN')
        return
        
    def draw_header_preset(self, context):
        layout = self.layout
        col = layout.column()
        
        meta_settings = context.scene.LOR_Settings
        settings = utils.get_settings(meta_settings)
        
        col.enabled = False
        col.label(text=str(len(settings.variable_settings)))
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
        row.operator("lighting_overrider.variable_settings_init", icon='SHADERFX')
        
        col = row.column()
        row = col.row(align=True)
        row.operator("lighting_overrider.variable_setting_add", icon='ADD', text="")
        row.operator("lighting_overrider.variable_setting_remove", icon='REMOVE', text="")
        
        row = col_top.row(align=True)
        col = row.column()
        col.template_list(
            "LOR_UL_variable_settings_list",
            "",
            settings,
            "variable_settings",
            settings,
            "variable_settings_index",
            rows=2,
        )
        col.operator('lighting_overrider.variable_settings_apply', icon='PLAY')
        return

panel_class = LOR_PT_variable_settings_panel

classes = (
    LOR_variable_setting,
    LOR_UL_variable_settings_list,
    LOR_OT_variable_setting_add,
    LOR_OT_variable_setting_remove,
    LOR_OT_variable_settings_initialize,
    LOR_OT_variable_settings_apply,
    )

def register():
    for c in classes:
        bpy.utils.register_class(c)

def unregister():
    for c in classes:
        bpy.utils.unregister_class(c)