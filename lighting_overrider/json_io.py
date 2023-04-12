import bpy
import json
from . import categories
from .categories import *
from . import utils

class LOR_OT_find_settings(bpy.types.Operator):
    """
    """
    bl_idname = "lighting_overrider.find_settings"
    bl_label = "Find JSON"
    bl_description = "Find settings datablock for the current sequence or shot as it is referenced in the scene properties"
    bl_options = {"REGISTER", "UNDO"}
    
    def execute(self, context):
        meta_settings = context.scene.LOR_Settings
        settings = utils.get_settings(meta_settings)
        
        sequence_settings_db, shot_settings_db = utils.find_settings(bpy.context)
        
        if meta_settings.settings_toggle == 'SEQUENCE':
            meta_settings.sequence_settings.text_datablock = sequence_settings_db
        elif meta_settings.settings_toggle == 'SHOT':
            meta_settings.shot_settings.text_datablock = shot_settings_db
        
        return {'FINISHED'}
        
class LOR_OT_read_settings(bpy.types.Operator):
    """
    """
    bl_idname = "lighting_overrider.read_settings"
    bl_label = "Read JSON"
    bl_description = "Read settings from specified text datablock"
    bl_options = {"REGISTER", "UNDO"}
    
    @classmethod
    def poll(cls, context):
        meta_settings = context.scene.LOR_Settings
        settings = utils.get_settings(meta_settings)
        return bool(settings.text_datablock)
    
    def execute(self, context):
        meta_settings = context.scene.LOR_Settings
        settings = utils.get_settings(meta_settings)
        
        text = settings.text_datablock
        
        if not text.is_in_memory:
            override = context.copy()
            area_type = override['area'].type
            override['area'].type = 'TEXT_EDITOR'
            override['edit_text'] = text
            bpy.ops.text.reload(override)
            override['area'].type = area_type
        
        data = read_data_from_json(text)
        
        unpack_settings_data(settings, data)
        settings.is_dirty = False
        
        return {'FINISHED'}

class LOR_OT_write_settings(bpy.types.Operator):
    """
    """
    bl_idname = "lighting_overrider.write_settings"
    bl_label = "Write JSON"
    bl_description = "Write settings to specified text datablock"
    bl_options = {"REGISTER", "UNDO"}
    
    @classmethod
    def poll(cls, context):
        meta_settings = context.scene.LOR_Settings
        settings = utils.get_settings(meta_settings)
        return bool(settings.text_datablock)
    
    def execute(self, context):
        meta_settings = context.scene.LOR_Settings
        settings = utils.get_settings(meta_settings)
        
        text = settings.text_datablock
    
        data = pack_settings_data(settings)
        
        write_data_to_json( text, data)
        
        if not text.is_in_memory:
            override = context.copy()
            area_type = override['area'].type
            override['area'].type = 'TEXT_EDITOR'
            override['edit_text'] = text
            bpy.ops.text.save(override)
            override['area'].type = area_type
        settings.is_dirty = False
        
        return {'FINISHED'}

def pack_settings_data(settings) -> dict:
    
    data = {}
    
    category_modules = [globals()[mod] for mod in categories.__all__]
    
    for cat, cat_name in zip(category_modules, categories.__all__):
        data[cat_name] = cat.settings_as_dict(settings)
    
    return data

def unpack_settings_data(settings, data):
    
    category_modules = [globals()[mod] for mod in categories.__all__]
    
    for cat, cat_name in zip(category_modules, categories.__all__):
        if not cat_name in data.keys():
            continue
        cat.load_settings(settings, data[cat_name])
    
    return

def cleanup_json(string):
    
    counter = 0
    open_brackets = 0
    remove = []
    for i, char in enumerate(string):
        #if char == '{':
        #    counter += 1
        #    continue
        #if counter < 3:
        #    continue
        if char == '[':
            open_brackets += 1
        elif char == ']':
            open_brackets -= 1
        if open_brackets:
            if char == '\n':
                remove += [i]
            elif char == ' ' and string[i+1] == ' ':
                remove += [i]
    counter = 0
    for i in remove:
        i -= counter
        string = string[:i] + string[i+1:]
        counter += 1
    
    return string

def write_data_to_json(text: bpy.types.Text, data: dict, partial=None):
    text.clear()
    text.write(cleanup_json(json.dumps(data, separators=(',', ':'), indent=4)))
    return

def read_data_from_json(text: bpy.types.Text):
    return json.loads(text.as_string())


classes = (
    LOR_OT_find_settings,
    LOR_OT_read_settings,
    LOR_OT_write_settings,
)

def register():
    for c in classes:
        bpy.utils.register_class(c)

def unregister():
    for c in classes:
        bpy.utils.unregister_class(c)
