from . import categories
from .categories import *
from . import utils
from .import json_io
import bpy
import inspect
from bpy.app.handlers import persistent

from . import lighting_overrider_execution

@persistent
def write_execution_script_on_save(dummy):
    meta_settings = getattr(bpy.context.scene, 'LOR_Settings')
    if not meta_settings.enabled:
        return
    if utils.link_execution_script_from_source(bpy.context):
        return
    bpy.ops.lighting_overrider.generate_execution_script()
    return

def load_settings(context, name, path=None):
    ''' Return text datablock of the settings specified with a name. If a filepath is specified (re)load from disk.
    '''
    meta_settings = getattr(bpy.context.scene, 'LOR_Settings')
    if not meta_settings:
        return None
    settings = utils.get_settings(meta_settings)
    
    if path:
        path += f'/{name}.settings.json'
    
    settings_db = bpy.data.texts.get(f'{name}.settings.json')
    
    if settings_db:
        force_reload_external(context, settings_db)
        return settings_from_datablock(settings_db)
    
    if path:
        if not os.path.isfile(path):
            open(path, 'a').close()
        bpy.ops.text.open(filepath=bpy.path.relpath(path))
        settings_db = bpy.data.texts.get(f'{name}.settings.json')
    else:
        settings_db = bpy.data.texts.new(f'{name}.settings.json')
    return settings_from_datablock(settings_db)

def apply_settings(data):
    
    category_modules = [globals()[mod] for mod in categories.__all__]
    
    for cat, cat_name in zip(category_modules, categories.__all__):
        cat.apply_settings(data[cat_name])
    return

def generate_execution_script() -> str:
    
    script = inspect.getsource(lighting_overrider_execution)
    
    return script

class LOR_OT_link_execution_script(bpy.types.Operator):
    """
    """
    bl_idname = "lighting_overrider.link_execution_script"
    bl_label = "Link Execution Script"
    bl_description = "Link execution script from specified source file"
    bl_options = {"REGISTER", "UNDO"}
    
    def execute(self, context):
        utils.link_execution_script_from_source(context)
        return {'FINISHED'}
    
class LOR_OT_generate_execution_script(bpy.types.Operator):
    """
    """
    bl_idname = "lighting_overrider.generate_execution_script"
    bl_label = "Generate Execution Script"
    bl_description = "Generate script for automatic execution of the overrides based on the JSON settings"
    bl_options = {"REGISTER", "UNDO"}
    
    def execute(self, context):
        meta_settings = context.scene.LOR_Settings
        settings = utils.get_settings(meta_settings)
        
        if not meta_settings.execution_script:
            text = bpy.data.texts.new('lighting_overrider_execution.py')
            meta_settings.execution_script = text
        else:
            text = meta_settings.execution_script
        text.from_string(generate_execution_script())
        text.use_module = True
        
        return {'FINISHED'}

def run_execution_script(context):
    meta_settings = context.scene.LOR_Settings
    settings = utils.get_settings(meta_settings)
    
    if not meta_settings.execution_script:
        return False
    script = meta_settings.execution_script
    exec(script.as_string(), globals())
    
    return True

class LOR_OT_run_execution_script(bpy.types.Operator):
    """
    """
    bl_idname = "lighting_overrider.run_execution_script"
    bl_label = "Run Execution Script"
    bl_description = "Run script for automatic execution of the overrides based on the JSON settings"
    bl_options = {"REGISTER", "UNDO"}
    
    @classmethod
    def poll(cls, context):
        meta_settings = context.scene.LOR_Settings
        settings = utils.get_settings(meta_settings)
        return bool(meta_settings.execution_script)
    
    def execute(self, context):
        if not run_execution_script(context):
            return {'CANCELLED'}
        return {'FINISHED'}

class LOR_OT_reload_libraries(bpy.types.Operator):
    """ Reloads all libraries to show the fresh file without overrides
    """
    bl_idname = "lighting_overrider.reload_libraries"
    bl_label = "Reload Libraries"
    bl_description = "Reload all libraries"
    bl_options = {"REGISTER", "UNDO"}
    
    def execute(self, context):
        utils.reload_libraries()        
        return {'FINISHED'}

class LOR_OT_reload_run_execution_script(bpy.types.Operator):
    """ Reloads all libraries and runs the override script to show how the file will look after load
    """
    bl_idname = "lighting_overrider.reload_run_execution_script"
    bl_label = "Reload Libraries and Run Execution Script"
    bl_description = "Reload all libraries and run script for automatic execution of the overrides based on the JSON settings"
    bl_options = {"REGISTER", "UNDO"}
    
    @classmethod
    def poll(cls, context):
        meta_settings = context.scene.LOR_Settings
        return bool(meta_settings.execution_script)
    
    def execute(self, context):
        utils.reload_libraries()
        if not run_execution_script(context):
            return {'CANCELLED'}
        
        return {'FINISHED'}

class LOR_OT_apply_JSON(bpy.types.Operator):
    """
    """
    bl_idname = "lighting_overrider.apply_json"
    bl_label = "Apply JSON"
    bl_description = "Apply settings from specified JSON text datablock"
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
        data = json_io.read_data_from_json(text)
        
        apply_settings(data)
        utils.kick_evaluation()
        
        return {'FINISHED'}

class LOR_OT_write_apply_JSON(bpy.types.Operator):
    """
    """
    bl_idname = "lighting_overrider.write_apply_json"
    bl_label = "Write and Apply JSON"
    bl_description = "Write and apply settings in specified JSON text datablock"
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
        data = json_io.pack_settings_data(settings)
        
        json_io.write_data_to_json( text, data)
        settings.is_dirty = False
        
        apply_settings(data)
        utils.kick_evaluation()
        
        return {'FINISHED'}



classes = (
    LOR_OT_apply_JSON,
    LOR_OT_write_apply_JSON,
    LOR_OT_link_execution_script,
    LOR_OT_generate_execution_script,
    LOR_OT_reload_libraries,
    LOR_OT_run_execution_script,
    LOR_OT_reload_run_execution_script,
    )

def register():
    for c in classes:
        bpy.utils.register_class(c)
    bpy.app.handlers.save_pre.append(write_execution_script_on_save)

def unregister():
    for c in classes:
        bpy.utils.unregister_class(c)