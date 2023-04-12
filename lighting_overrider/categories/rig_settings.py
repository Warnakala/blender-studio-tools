from .. import utils
from ..templates import *
import bpy

def settings_as_dict(settings):
    data = {}
    for setting in settings.rig_settings:
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

def get_properties_bone(ob, prefix='Properties_'):
    
    if not ob.type == 'ARMATURE':
        return None
    
    for bone in ob.pose.bones:
        if not bone.name.startswith(prefix):
            continue
        return bone
    return None

def apply_settings(data):
    if not data:
        return
    
    list_unique, list_all = utils.split_by_suffix(data.keys(), ':all')
    
    for ob in bpy.data.objects:
        # find properties bone (first posebone that starts with 'Properties_')
        if not ob.type == 'ARMATURE':
            continue
        bone_prop = get_properties_bone(ob)
        if not bone_prop:
            continue
        
        # group names
        for name_ob in list_all:
            if not ob.name.startswith(name_ob):
                continue
            for name_set in data[name_ob+':all']:
                if not name_set in bone_prop:
                    print(f'Warning: Property {name_set} on object {ob.name} not found.')
                    continue
                data_path = f'pose.bones["{bone_prop.name}"]["{name_set}"]'
                utils.mute_fcurve(ob, data_path)
                bone_prop[name_set] = data[name_ob+':all'][name_set][0]
                
        # unique names
        if ob.name in list_unique:
            for name_set in data[ob.name]:
                if name_set in bone_prop:
                    data_path = f'pose.bones["{bone_prop.name}"]["{name_set}"]'
                    utils.mute_fcurve(ob, data_path)
                    bone_prop[name_set] = data[ob.name][name_set][0]
                else:
                    print(f'Warning: Property {name_set} on object {ob.name} not found.')
    return

def load_settings(settings, data):
    while len(settings.rig_settings) > 0:
        settings.rig_settings.remove(0)
    
    for specifier in data.keys():
        subsettings_dict = data[specifier]
        new_setting = settings.rig_settings.add()
        new_setting.setting_expanded = False
        new_setting.specifier = specifier
        for name in subsettings_dict.keys():
            value = subsettings_dict[name]
            new_subsetting = new_setting.subsettings.add()
            new_subsetting.name = name
            new_subsetting.type = value[1]
            setattr(new_subsetting, value[1], value[0])
        
    settings.rig_settings_index = min(settings.rig_settings_index, len(settings.rig_settings)-1)
    return

class LOR_OT_rig_settings_apply(bpy.types.Operator):
    """
    """
    bl_idname = "lighting_overrider.rig_settings_apply"
    bl_label = "Apply Rig Settings"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        meta_settings = context.scene.LOR_Settings
        settings = utils.get_settings(meta_settings)
        
        apply_settings(settings_as_dict(settings))
        utils.kick_evaluation()
        
        return {'FINISHED'}

class LOR_rig_setting(LOR_setting):
    specifier: bpy.props.StringProperty(default='HLP-', update=utils.mark_dirty)
    

class LOR_OT_rig_settings_initialize(bpy.types.Operator):
    """
    """
    bl_idname = "lighting_overrider.rig_settings_init"
    bl_label = "Initialize from Selection"
    bl_options = {"REGISTER", "UNDO"}
    
    @classmethod
    def poll(cls, context):
        return 'ARMATURE' in [ob.type for ob in context.selected_objects]
        
    def execute(self, context):
        meta_settings = context.scene.LOR_Settings
        settings = utils.get_settings(meta_settings)
        
        existing_specifiers = [setting.specifier for setting in settings.rig_settings]
        
        for ob in context.selected_objects:
            if not ob.type == 'ARMATURE':
                continue
            
            bone_prop = get_properties_bone(ob)
            if not bone_prop:
                continue
            
            if not ob.name in existing_specifiers:
                setting = settings.rig_settings.add()
                setting.specifier = ob.name
            else:
                setting = settings.rig_settings[existing_specifiers.index(ob.name)]
            
            existing_names = [subsetting.name for subsetting in setting.subsettings]
            
            for name in list(bone_prop.keys()): #TODO make type identification more fail-safe
                try:
                    prop_props = bone_prop.id_properties_ui(name)
                except:
                    continue
                
                if name in existing_names:
                    continue
                value = bone_prop[name]
                type = 'VALUE'
                if prop_props.as_dict()['subtype'] == 'COLOR':
                    type = 'COLOR'
                elif prop_props.as_dict()['subtype'] == 'FACTOR':
                    type = 'FACTOR'
                elif isinstance(bone_prop[name], int):
                    type = 'INTEGER'
                elif isinstance(value, str):
                    type = 'STRING'
                else:
                    try:
                        if len(value)==3 and not isinstance(value[0], str):
                            type = 'VECTOR'
                        else:
                            continue
                    except:
                        continue
                subsetting = setting.subsettings.add()
                subsetting.name = name
                subsetting.type = type
                setattr(subsetting, subsetting.type, value)#TODO pull in settings like min/max
            settings.is_dirty = True
        
        settings.rig_settings_index = len(settings.rig_settings)-1
        
        return {'FINISHED'}
    

class LOR_OT_rig_setting_add(bpy.types.Operator):
    """
    """
    bl_idname = "lighting_overrider.rig_setting_add"
    bl_label = "Add Rig Setting"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        meta_settings = context.scene.LOR_Settings
        settings = utils.get_settings(meta_settings)
        new_setting = settings.rig_settings.add()
        settings.is_dirty = True

        settings.rig_settings_index = len(settings.rig_settings)-1

        return {'FINISHED'}

class LOR_OT_rig_setting_remove(bpy.types.Operator):
    """
    """
    bl_idname = "lighting_overrider.rig_setting_remove"
    bl_label = "Remove Rig Setting"
    bl_options = {"REGISTER", "UNDO"}
    
    @classmethod
    def poll(cls, context):
        meta_settings = context.scene.LOR_Settings
        settings = utils.get_settings(meta_settings)
        return len(settings.rig_settings)>0
        
    def execute(self, context):
        meta_settings = context.scene.LOR_Settings
        settings = utils.get_settings(meta_settings)
        settings.rig_settings.remove(settings.rig_settings_index)
        settings.is_dirty = True
        
        if settings.rig_settings_index >= len(settings.rig_settings):
            settings.rig_settings_index = len(settings.rig_settings)-1
        return {'FINISHED'}

class LOR_OT_rig_setting_duplicate(bpy.types.Operator):
    """
    """
    bl_idname = "lighting_overrider.rig_setting_duplicate"
    bl_label = "Duplicate Rig Setting"
    bl_options = {"REGISTER", "UNDO"}
    
    @classmethod
    def poll(cls, context):
        meta_settings = context.scene.LOR_Settings
        settings = utils.get_settings(meta_settings)
        return len(settings.rig_settings)>0

    def execute(self, context):
        meta_settings = context.scene.LOR_Settings
        settings = utils.get_settings(meta_settings)
        
        prev_setting  = settings.rig_settings[settings.rig_settings_index]
        new_setting = settings.rig_settings.add()
        
        setattr(new_setting, 'specifier', getattr(prev_setting, 'specifier'))
        for i in range(len(prev_setting.subsettings)):
            new_setting.subsettings.add()
            enum_items = [item.identifier for item in prev_setting.subsettings[i].bl_rna.properties['type'].enum_items_static]
            for prop in ['name', 'type']+enum_items:
                setattr(new_setting.subsettings[i], prop, getattr(prev_setting.subsettings[i], prop))
        
        settings.rig_settings_index = len(settings.rig_settings)-1
        return {'FINISHED'}

class LOR_OT_rig_subsetting_add(bpy.types.Operator):
    """
    """
    bl_idname = "lighting_overrider.rig_subsetting_add"
    bl_label = "Add Rig Subsetting"
    bl_options = {"REGISTER", "UNDO"}
    
    def execute(self, context):
        meta_settings = context.scene.LOR_Settings
        settings = utils.get_settings(meta_settings)
        rig_setting = settings.rig_settings[settings.rig_settings_index]
        new_subsetting = rig_setting.subsettings.add()
        settings.is_dirty = True
        
        return {'FINISHED'}

class LOR_OT_rig_subsetting_remove(bpy.types.Operator):
    """
    """
    bl_idname = "lighting_overrider.rig_subsetting_remove"
    bl_label = "Remove Rig Subsetting"
    bl_options = {"REGISTER", "UNDO"}
    
    index: bpy.props.IntProperty(default=-1)
    
    def execute(self, context):
        meta_settings = context.scene.LOR_Settings
        settings = utils.get_settings(meta_settings)
        rig_setting = settings.rig_settings[settings.rig_settings_index]
        rig_setting.subsettings.remove(self.index)
        settings.is_dirty = True
        
        return {'FINISHED'}

class LOR_UL_rig_settings_list(LOR_UL_settings_list):
    
    def draw_item(
        self, context, layout, data, item, icon, active_data, active_propname, index):
        
        meta_settings = context.scene.LOR_Settings
        settings = utils.get_settings(meta_settings)
        
        row = layout.row()
        col_top = row.column()
        row = col_top.row()
        if len(item.subsettings) == 0 and not index == settings.rig_settings_index:
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
        if index == settings.rig_settings_index:
            col.operator("lighting_overrider.rig_setting_remove", icon='X', text="", emboss=False)
        else:
            col.label(text='', icon='BLANK1')
        
        if toggle:
            if index == settings.rig_settings_index:
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
                if index == settings.rig_settings_index:
                    row_sub.operator("lighting_overrider.rig_subsetting_remove", icon='REMOVE', text="", emboss=False).index = i
                
            if index == settings.rig_settings_index:
                col_top.operator("lighting_overrider.rig_subsetting_add", icon='ADD', text="")

class LOR_PT_rig_settings_panel(bpy.types.Panel):
    bl_parent_id = "LOR_PT_lighting_overrider_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_label = "Rig Settings"
    bl_category = 'Overrides'
    bl_options = {"DEFAULT_CLOSED"}
    
    def draw_header(self, context):
        self.layout.label(text='', icon='ARMATURE_DATA')
        return
        
    def draw_header_preset(self, context):
        layout = self.layout
        col = layout.column()
        
        meta_settings = context.scene.LOR_Settings
        settings = utils.get_settings(meta_settings)
        
        col.enabled = False
        col.label(text=str(len(settings.rig_settings)))
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
        row.operator("lighting_overrider.rig_settings_init", icon='SHADERFX')
        
        col = row.column()
        row = col.row(align=True)
        row.operator("lighting_overrider.rig_setting_add", icon='ADD', text="")
        row.operator("lighting_overrider.rig_setting_remove", icon='REMOVE', text="")
        row.operator("lighting_overrider.rig_setting_duplicate", icon='DUPLICATE', text="")
        
        row = col_top.row(align=True)
        col = row.column()
        col.template_list(
            "LOR_UL_rig_settings_list",
            "",
            settings,
            "rig_settings",
            settings,
            "rig_settings_index",
            rows=2,
        )
        col.operator('lighting_overrider.rig_settings_apply', icon='PLAY')
        return

panel_class = LOR_PT_rig_settings_panel

classes = (
    LOR_rig_setting,
    LOR_UL_rig_settings_list,
    LOR_OT_rig_setting_add,
    LOR_OT_rig_setting_remove,
    LOR_OT_rig_setting_duplicate,
    LOR_OT_rig_settings_initialize,
    LOR_OT_rig_subsetting_add,
    LOR_OT_rig_subsetting_remove,
    LOR_OT_rig_settings_apply,
    )

def register():
    for c in classes:
        bpy.utils.register_class(c)

def unregister():
    for c in classes:
        bpy.utils.unregister_class(c)
