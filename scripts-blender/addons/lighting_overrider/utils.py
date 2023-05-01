import os
import bpy
from pathlib import Path

def executions_script_source_exists(context):
    meta_settings = context.scene.LOR_Settings
    path = meta_settings.execution_script_source
    path = bpy.path.abspath(path)
    return os.path.isfile(path)

def link_execution_script_from_source(context):
    meta_settings = context.scene.LOR_Settings
    if not executions_script_source_exists:
        print(f'Warning: Execution script source file not found')
        return False
    with bpy.data.libraries.load(meta_settings.execution_script_source, link=True, relative=True) as (data_from, data_to):
        data_to.texts = ["lighting_overrider_execution.py"]
    meta_settings.execution_script = bpy.data.texts["lighting_overrider_execution.py", meta_settings.execution_script_source]
    return

def find_settings(context):
    meta_settings = getattr(context.scene, 'LOR_Settings')
    if meta_settings:
        sequence_name = meta_settings.sequence_settings.name
        shot_name = meta_settings.shot_settings.name

        try:
            sequence_settings_db = context.scene['LOR_sequence_settings']
        except:
            sequence_settings_db = None

        try:
            shot_settings_db = context.scene['LOR_shot_settings']
        except:
            shot_settings_db = None

        if not sequence_settings_db:
            sequence_settings_db = bpy.data.texts.get(f'{sequence_name}.settings.json')
        if not shot_settings_db:
            shot_settings_db = bpy.data.texts.get(f'{shot_name}.settings.json')

        if not sequence_settings_db:
            filepath = Path(bpy.context.blend_data.filepath)
            path = filepath.parents[1].as_posix()+f'/{sequence_name}.settings.json'
            if not os.path.isfile(path):
                open(path, 'a').close()
            bpy.ops.text.open(filepath=bpy.path.relpath(path))
        if not shot_settings_db:
            shot_settings_db = bpy.data.texts.new(f'{shot_name}.settings.json')

    return sequence_settings_db, shot_settings_db

def get_settings(meta_settings):
    ''' Returns the currently active settings group.
    '''
    if meta_settings.settings_toggle == 'SHOT':
        settings = meta_settings.shot_settings
    elif meta_settings.settings_toggle == 'SEQUENCE':
        settings = meta_settings.sequence_settings
    return settings

def mark_dirty(self, context):
    meta_settings = context.scene.LOR_Settings
    settings = get_settings(meta_settings)

    if settings.is_dirty:
        return
    settings.is_dirty = True
    return

def mute_fcurve(ob, path):
    if not ob.animation_data:
        return
    if not ob.animation_data.action:
        return
    fcurve = ob.animation_data.action.fcurves.find(path)
    if fcurve:
        fcurve.mute = True
    return

def reload_libraries():
    for lib in bpy.data.libraries:
        lib.reload()
    return

def reload_settings(context):#TODO find a way to run this on load_post handler
    meta_settings = context.scene.LOR_Settings
    for settings in [meta_settings.sequence_settings, meta_settings.shot_settings]:
        if not settings.text_datablock:
            continue
        if settings.text_datablock.is_in_memory:
            continue
        override = context.copy()
        if not override['area']:
            return
        area_type = override['area'].type
        override['area'].type = 'TEXT_EDITOR'
        override['edit_text'] = settings.text_datablock
        bpy.ops.text.reload(override)
        override['area'].type = area_type
    return

def get_instances_across_all_libraries(name, path) -> list:#TODO


    return

def kick_evaluation(objects=None):
    if not objects:
        objects = bpy.data.objects
    for ob in objects:
        ob.update_tag()
    return

def split_by_suffix(list, sfx):
    with_suffix = [name[:-len(sfx)] for name in list if name.endswith(sfx)]
    without_suffix = [name for name in list if not name.endswith(sfx)]
    return without_suffix, with_suffix

def parse_rna_path_to_elements(rna_path, delimiter='.'):
    ''' Returns the element strings of an RNA path split by '.' delimiter, disregarding any delimiter in a string within the path.
    '''
    if not delimiter in rna_path:
        return [rna_path]
    
    parse = rna_path
    
    # replace escape chars with whitespaces
    parse_elements = parse.split(r'\\')
    parse = '  '.join(parse_elements)
        
    parse_elements = parse.split('\\')
    parse = parse_elements[0]
    for el in parse_elements[1:]:
        parse += '  '
        parse += el[1:]
    
    # replace strings within path with whitespaces
    parse_elements = parse.split('"')
    parse = parse_elements[0]
    for el1, el2 in zip(parse_elements[1::2], parse_elements[2::2]):
        parse += '"'+' '*len(el1)+'"'
        parse += el2
    
    parse_elements = parse.split(delimiter)
    
    elements = []
    for el in parse_elements:
        elements += [rna_path[:len(el)]]
        rna_path = rna_path[len(el)+len(delimiter):]
    
    return elements

def parse_rna_path_for_custom_property(rna_path):
    ''' Returns the rna path of the datablock and the name of the custom property for an rna path that describes a custom property. 
    '''
    if not '][' in rna_path:
        return False
    parse_elements = parse_rna_path_to_elements(rna_path, delimiter='][')
    return parse_elements[0]+']', '"'.join(parse_elements[1].split('"')[1:-1])