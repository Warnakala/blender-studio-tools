from .. import utils
from ..templates import *
import bpy

def settings_as_dict(settings):
    data = {}
    for setting in settings.shader_settings:
        data_sub = {}
        for subsetting in setting.subsettings:
            if isinstance(getattr(subsetting, subsetting.type), str):
                data_sub[subsetting.name] = [getattr(subsetting, subsetting.type), subsetting.type]
            elif not subsetting.bl_rna.properties[subsetting.type].is_array:
                data_sub[subsetting.name] = [getattr(subsetting, subsetting.type), subsetting.type]
            else:
                data_sub[subsetting.name] = [getattr(subsetting, subsetting.type)[:], subsetting.type]
        data[setting.specifier] = data_sub
    return data

def apply_settings(data):
    
    if not data:
        return
    
    list_unique, list_all = utils.split_by_suffix(data.keys(), ':all')

    for ob in bpy.data.objects:
        # group names
        for name_ob in list_all:
            if not ob.name.startswith(name_ob):
                continue
            for name_set in data[name_ob+':all']:
                if not name_set in ob:
                    print(f'Warning: Property {name_set} on object {ob.name} not found.')
                    continue
                ob[name_set] = data[name_ob+':all'][name_set][0]
        # unique names
        if ob.name in list_unique:
            for name_set in data[ob.name]:
                if name_set in ob:
                    ob[name_set] = data[ob.name][name_set][0]
                else:
                    print(f'Warning: Property {name_set} on object {ob.name} not found.')
    return


def load_settings(settings, data):
    while len(settings.shader_settings) > 0:
        settings.shader_settings.remove(0)
    
    for specifier in data.keys():
        subsettings_dict = data[specifier]
        new_setting = settings.shader_settings.add()
        new_setting.setting_expanded = False
        new_setting.specifier = specifier
        for name in subsettings_dict.keys():
            value = subsettings_dict[name]
            new_subsetting = new_setting.subsettings.add()
            new_subsetting.name = name
            new_subsetting.type = value[1]
            setattr(new_subsetting, value[1], value[0])
        
    settings.shader_settings_index = min(settings.shader_settings_index, len(settings.shader_settings)-1)
    return

class LOR_OT_shader_settings_apply(bpy.types.Operator):
    """
    """
    bl_idname = "lighting_overrider.shader_settings_apply"
    bl_label = "Apply Shader Settings"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        meta_settings = context.scene.LOR_Settings
        settings = utils.get_settings(meta_settings)
        
        apply_settings(settings_as_dict(settings))
        utils.kick_evaluation()
        
        return {'FINISHED'}

class LOR_shader_setting(LOR_setting):
    specifier: bpy.props.StringProperty(default='HLP-', update=utils.mark_dirty)
    

class LOR_OT_shader_settings_initialize(bpy.types.Operator):
    """
    """
    bl_idname = "lighting_overrider.shader_settings_init"
    bl_label = "Initialize from Selection"
    bl_options = {"REGISTER", "UNDO"}
    
    @classmethod
    def poll(cls, context):
        return len(context.selected_objects) > 0
        
    def execute(self, context):
        meta_settings = context.scene.LOR_Settings
        settings = utils.get_settings(meta_settings)
        
        existing_specifiers = [setting.specifier for setting in settings.shader_settings]
        
        objects = context.selected_objects
        for ob in context.selected_objects:
            if not ob.type == 'ARMATURE':
                continue
            for child in ob.children:
                if not (child.name.startswith('HLP-') and 'settings' in child.name):
                    continue
                if child in objects:
                    continue
                objects += [child]
        
        for ob in objects:
            if ob.type == 'ARMATURE':
                continue
            if not ob.name in existing_specifiers:
                setting = settings.shader_settings.add()
                setting.specifier = ob.name
                existing_specifiers += [ob.name]
            else:
                setting = settings.shader_settings[existing_specifiers.index(ob.name)]
            
            existing_names = [subsetting.name for subsetting in setting.subsettings]
            
            for name in list(ob.keys()):
                try:
                    prop_props = ob.id_properties_ui(name)
                except:
                    continue
                
                if name in existing_names:
                    continue
                subsetting = setting.subsettings.add()
                subsetting.name = name
                value = ob[name]
                if 'subtype' in prop_props.as_dict().keys():
                    if prop_props.as_dict()['subtype'] == 'COLOR':
                        subsetting.type = 'COLOR'
                    if prop_props.as_dict()['subtype'] == 'FACTOR':
                        subsetting.type = 'FACTOR'
                elif '__len__' in dir(value):
                    if isinstance(value, str):
                        subsetting.type = 'STRING'
                    elif len(value)==3:
                        subsetting.type = 'VECTOR'
                    else:
                        continue
                setattr(subsetting, subsetting.type, value)
            settings.is_dirty = True
        
        settings.shader_settings_index = len(settings.shader_settings)-1
        
        return {'FINISHED'}
    

class LOR_OT_shader_setting_add(bpy.types.Operator):
    """
    """
    bl_idname = "lighting_overrider.shader_setting_add"
    bl_label = "Add Shader Setting"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        meta_settings = context.scene.LOR_Settings
        settings = utils.get_settings(meta_settings)
        new_setting = settings.shader_settings.add()
        settings.is_dirty = True

        settings.shader_settings_index = len(settings.shader_settings)-1

        return {'FINISHED'}

class LOR_OT_shader_setting_remove(bpy.types.Operator):
    """
    """
    bl_idname = "lighting_overrider.shader_setting_remove"
    bl_label = "Remove Shader Setting"
    bl_options = {"REGISTER", "UNDO"}
    
    @classmethod
    def poll(cls, context):
        meta_settings = context.scene.LOR_Settings
        settings = utils.get_settings(meta_settings)
        return len(settings.shader_settings)>0
        
    def execute(self, context):
        meta_settings = context.scene.LOR_Settings
        settings = utils.get_settings(meta_settings)
        settings.shader_settings.remove(settings.shader_settings_index)
        settings.is_dirty = True
        
        if settings.shader_settings_index >= len(settings.shader_settings):
            settings.shader_settings_index = len(settings.shader_settings)-1
        return {'FINISHED'}

class LOR_OT_shader_setting_duplicate(bpy.types.Operator):
    """
    """
    bl_idname = "lighting_overrider.shader_setting_duplicate"
    bl_label = "Duplicate Shader Setting"
    bl_options = {"REGISTER", "UNDO"}
    
    @classmethod
    def poll(cls, context):
        meta_settings = context.scene.LOR_Settings
        settings = utils.get_settings(meta_settings)
        return len(settings.shader_settings)>0

    def execute(self, context):
        meta_settings = context.scene.LOR_Settings
        settings = utils.get_settings(meta_settings)
        
        prev_setting  = settings.shader_settings[settings.shader_settings_index]
        new_setting = settings.shader_settings.add()
        
        setattr(new_setting, 'specifier', getattr(prev_setting, 'specifier'))
        for i in range(len(prev_setting.subsettings)):
            new_setting.subsettings.add()
            enum_items = [item.identifier for item in prev_setting.subsettings[i].bl_rna.properties['type'].enum_items_static]
            for prop in ['name', 'type']+enum_items:
                setattr(new_setting.subsettings[i], prop, getattr(prev_setting.subsettings[i], prop))
        
        settings.shader_settings_index = len(settings.shader_settings)-1
        return {'FINISHED'}

class LOR_OT_shader_subsetting_add(bpy.types.Operator):
    """
    """
    bl_idname = "lighting_overrider.shader_subsetting_add"
    bl_label = "Add Shader Subsetting"
    bl_options = {"REGISTER", "UNDO"}
    
    def execute(self, context):
        meta_settings = context.scene.LOR_Settings
        settings = utils.get_settings(meta_settings)
        shader_setting = settings.shader_settings[settings.shader_settings_index]
        new_subsetting = shader_setting.subsettings.add()
        settings.is_dirty = True
        
        return {'FINISHED'}

class LOR_OT_shader_subsetting_remove(bpy.types.Operator):
    """
    """
    bl_idname = "lighting_overrider.shader_subsetting_remove"
    bl_label = "Remove Shader Subsetting"
    bl_options = {"REGISTER", "UNDO"}
    
    index: bpy.props.IntProperty(default=-1)
    
    def execute(self, context):
        meta_settings = context.scene.LOR_Settings
        settings = utils.get_settings(meta_settings)
        shader_setting = settings.shader_settings[settings.shader_settings_index]
        shader_setting.subsettings.remove(self.index)
        settings.is_dirty = True
        
        return {'FINISHED'}

class LOR_UL_shader_settings_list(LOR_UL_settings_list):
    
    def draw_item(
        self, context, layout, data, item, icon, active_data, active_propname, index):
        
        meta_settings = context.scene.LOR_Settings
        settings = utils.get_settings(meta_settings)
        
        row = layout.row()
        col_top = row.column()
        row = col_top.row()
        if len(item.subsettings) == 0 and not index == settings.shader_settings_index:
            toggle = False
        else:
            toggle = item.setting_expanded
        if len(item.subsettings) == 0:
            row.label(text='', icon='LAYER_USED')
        else:
            row.prop(item, 'setting_expanded',
                icon="TRIA_DOWN" if toggle else "TRIA_RIGHT",
                icon_only=True, emboss=False
            )
        icon = 'WORLD' if item.specifier.endswith(':all') else 'MESH_CIRCLE'
        row.prop(item, "specifier", text='', icon=icon, emboss=False)
        
        col = row.column()
        col.alignment = 'RIGHT'
        col.enabled = False
        col.label(text=str(len(item.subsettings)))
        
        col = row.column()
        if index == settings.shader_settings_index:
            col.operator("lighting_overrider.shader_setting_remove", icon='X', text="", emboss=False)
        else:
            col.label(text='', icon='BLANK1')
        
        if toggle:
            if index == settings.shader_settings_index:
                col_top = col_top.box()
            row = col_top.row()
            col = row.column()
            
            for i in range(len(item.subsettings)):
                subsetting = item.subsettings[i]
                row_sub = col.row()
                col_sub = row_sub.column()
                row_sub2 = col_sub.row(align=True)
                row_sub2.prop(subsetting, "name", text='')
                row_sub2.prop(subsetting, subsetting.type, text='')
                col_sub = row_sub.column()
                row_sub2 = col_sub.row(align=True)
                row_sub2.prop(subsetting, 'type', text='', icon='THREE_DOTS', icon_only=True, emboss=False)
                if index == settings.shader_settings_index:
                    row_sub.operator("lighting_overrider.shader_subsetting_remove", icon='REMOVE', text="", emboss=False).index = i
                
            if index == settings.shader_settings_index:
                col_top.operator("lighting_overrider.shader_subsetting_add", icon='ADD', text="")

class LOR_PT_shader_settings_panel(bpy.types.Panel):
    bl_parent_id = "LOR_PT_lighting_overrider_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_label = "Shader Settings"
    bl_category = 'Overrides'
    bl_options = {"DEFAULT_CLOSED"}
    
    def draw_header(self, context):
        layout = self.layout
        layout.label(text='', icon='NODE_MATERIAL')
        return
        
    def draw_header_preset(self, context):
        layout = self.layout
            
        col = layout.column()
        
        meta_settings = context.scene.LOR_Settings
        settings = utils.get_settings(meta_settings)
        
        col.enabled = False
        col.label(text=str(len(settings.shader_settings)))
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
        row.operator("lighting_overrider.shader_settings_init", icon='SHADERFX')
        
        col = row.column()
        row = col.row(align=True)
        row.operator("lighting_overrider.shader_setting_add", icon='ADD', text="")
        row.operator("lighting_overrider.shader_setting_remove", icon='REMOVE', text="")
        row.operator("lighting_overrider.shader_setting_duplicate", icon='DUPLICATE', text="")
        
        row = col_top.row(align=True)
        col = row.column()
        col.template_list(
            "LOR_UL_shader_settings_list",
            "",
            settings,
            "shader_settings",
            settings,
            "shader_settings_index",
            rows=2,
        )
        col.operator('lighting_overrider.shader_settings_apply', icon='PLAY')
        return

panel_class = LOR_PT_shader_settings_panel

classes = (
    LOR_shader_setting,
    LOR_UL_shader_settings_list,
    LOR_OT_shader_setting_add,
    LOR_OT_shader_setting_remove,
    LOR_OT_shader_setting_duplicate,
    LOR_OT_shader_settings_initialize,
    LOR_OT_shader_subsetting_add,
    LOR_OT_shader_subsetting_remove,
    LOR_OT_shader_settings_apply,
    )

def register():
    for c in classes:
        bpy.utils.register_class(c)

def unregister():
    for c in classes:
        bpy.utils.unregister_class(c)
