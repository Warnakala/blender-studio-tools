from . import categories
from .categories import *
from . import utils
import bpy
from bpy.app.handlers import persistent
from pathlib import Path

@persistent
def init_on_load(dummy):

    if not bpy.data.is_saved:
        return

    context = bpy.context
    meta_settings = getattr(context.scene, 'LOR_Settings')
    if not meta_settings:
        return
    settings = utils.get_settings(meta_settings)

    filepath = Path(bpy.context.blend_data.filepath)
    sequence_name, shot_name, file_name = filepath.parts[-3:]

    meta_settings.sequence_settings.name = sequence_name
    meta_settings.shot_settings.name = shot_name

    if file_name.endswith('.lighting.blend'):
        meta_settings.enabled = True

    if not meta_settings.enabled:
        return

    if not meta_settings.execution_script:
        execution_script = bpy.data.texts.get('lighting_overrider_execution.py')
        if not execution_script:
            pass
        meta_settings.execution_script = execution_script

    if not bpy.context.blend_data.filepath:
        return

    sequence_settings_db, shot_settings_db = utils.find_settings(bpy.context)
    if not meta_settings.sequence_settings.text_datablock:
        meta_settings.sequence_settings.text_datablock = sequence_settings_db
    if not meta_settings.shot_settings.text_datablock:
        meta_settings.shot_settings.text_datablock = shot_settings_db

    #utils.reload_settings(context) #TODO: Fix loading settings on file load

    return

@persistent
def store_ref_on_save(dummy):
    meta_settings = getattr(bpy.context.scene, 'LOR_Settings')
    bpy.context.scene['LOR_sequence_settings'] = meta_settings.sequence_settings.text_datablock
    bpy.context.scene['LOR_shot_settings'] = meta_settings.shot_settings.text_datablock
    return

class LOR_OT_toggle_enabled(bpy.types.Operator):
    """
    """
    bl_idname = "lighting_overrider.toggle_enabled"
    bl_label = "Toggle Lighting Overrider Addon"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        meta_settings = context.scene.LOR_Settings
        meta_settings.enabled = not meta_settings.enabled
        return {'FINISHED'}

class LOR_OT_text_db_add(bpy.types.Operator):
    """
    """
    bl_idname = "lighting_overrider.text_db_add"
    bl_label = "Add Text Datablock"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        meta_settings = context.scene.LOR_Settings
        settings = utils.get_settings(meta_settings)

        name = f'{settings.name}.settings.json' if settings.name else f'{meta_settings.settings_toggle.lower()}_settings.json'
        text_db = bpy.data.texts.new(name)
        settings.text_datablock = text_db

        return {'FINISHED'}

class LOR_SettingsGroup(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty()
    text_datablock: bpy.props.PointerProperty(
        type = bpy.types.Text,
        name = "Settings JSON",
        description = "Text datablock that contains the full settings information"
    )
    is_dirty: bpy.props.BoolProperty(default=False)

    variable_settings: bpy.props.CollectionProperty(type=variable_settings.LOR_variable_setting)
    variable_settings_index: bpy.props.IntProperty()
    motion_blur_settings: bpy.props.CollectionProperty(type=variable_settings.LOR_variable_setting)
    motion_blur_settings_index: bpy.props.IntProperty()
    shader_settings: bpy.props.CollectionProperty(type=shader_settings.LOR_shader_setting)
    shader_settings_index: bpy.props.IntProperty()
    rig_settings: bpy.props.CollectionProperty(type=rig_settings.LOR_rig_setting)
    rig_settings_index: bpy.props.IntProperty()
    rna_overrides: bpy.props.CollectionProperty(type=rna_overrides.LOR_rna_override)
    rna_overrides_index: bpy.props.IntProperty()

class LOR_MetaSettings(bpy.types.PropertyGroup):
    enabled: bpy.props.BoolProperty(default=False)
    shot_settings: bpy.props.PointerProperty(type=LOR_SettingsGroup)
    sequence_settings: bpy.props.PointerProperty(type=LOR_SettingsGroup)
    settings_toggle: bpy.props.EnumProperty(default='SHOT',
        items= [('SEQUENCE', 'Sequence Settings', 'Manage override settings for the current sequence', '', 0),
                ('SHOT', 'Shot Settings', 'Manage override settings for the current shot', '', 1),]
    )
    execution_script: bpy.props.PointerProperty(
        type = bpy.types.Text,
        name = "Execution Script",
        description = "Text datablock with script that automatically applies the saved settings on file-load"
    )
    execution_script_source: bpy.props.StringProperty(default='//../../../lib/scripts/load_settings.blend')#TODO expose in addon settings

class LOR_PT_lighting_overrider_panel(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_label = "Lighting Overrider"
    bl_category = 'Overrides'

    def draw_header(self, context):
        self.layout.label(text='', icon='LIBRARY_DATA_OVERRIDE')
        return

    def draw(self, context):
        layout = self.layout

        meta_settings = context.scene.LOR_Settings
        settings = utils.get_settings(meta_settings)

        enabled = meta_settings.enabled

        text = 'Lighting Overrider Active' if enabled else 'Lighting Overrider Inactive'
        icon = 'CHECKBOX_HLT' if enabled else 'CHECKBOX_DEHLT'
        layout.operator('lighting_overrider.toggle_enabled', text=text, icon=icon, depress=enabled)

        col_main = layout.column()
        if not meta_settings.enabled:
            col_main.enabled = False

        col = col_main.column()

        box = col.box()
        row = box.row(align=True)
        row.prop(meta_settings, 'execution_script')
        if not meta_settings.execution_script:
            if utils.executions_script_source_exists(context):
                row.operator('lighting_overrider.link_execution_script', icon='LINKED', text='')
            else:
                row.operator('lighting_overrider.generate_execution_script', icon='FILE_CACHE', text='')
        #row.operator('lighting_overrider.reload_libraries', icon='FILE_REFRESH', text='')#TODO reload libraries accurately (bug?)
        row.operator('lighting_overrider.run_execution_script', icon='PLAY', text='')
        #row = box.row()
        #row.operator('lighting_overrider.reload_run_execution_script', icon='CHECKMARK')
        if not meta_settings.execution_script:
            col_warn = box.column()
            col_warn.alert = True
            row = col_warn.row()
            row.label(text=f'No execution script referenced!', icon='ERROR')
            row = col_warn.row()
            row.label(text=f'Without the execution script overrides will not be applied on file-load!', icon='BLANK1')

        col.separator(factor=2.0)


        row = col.row()
        row.prop(meta_settings, 'settings_toggle', expand=True)
        col.alignment = 'CENTER'
        col.label(text=f"{meta_settings.settings_toggle.capitalize()} Name: {settings.name if settings.name else 'UNKNOWN'}")

        col = col_main.column()
        col.label(text=settings.bl_rna.properties['text_datablock'].name)
        row = col.row(align=True)
        try:
            linked_settings = context.scene[f'LOR_{meta_settings.settings_toggle.lower()}_settings']
        except:
            linked_settings = None
        if settings.text_datablock not in [linked_settings, None]:
            row.alert = True
        row.prop(settings, 'text_datablock', text='', expand=True)
        if not settings.text_datablock or row.alert:
            row.operator('lighting_overrider.find_settings', text='', icon='VIEWZOOM')
        if not settings.text_datablock:
            row.operator('lighting_overrider.text_db_add', text='', icon='FILE_NEW')
        else:
            # mark whether JSON file is internal or external
            row.label(text='', icon = 'FILE_ARCHIVE' if settings.text_datablock.is_in_memory else 'FILE')

        row = col.row(align=True)
        flag1 = False
        flag2 = False
        if settings.text_datablock:
            if settings.text_datablock.is_dirty:
                flag1 = True
            if settings.text_datablock.is_modified:
                flag2 = True
        flag = (flag1 or flag2) and not settings.text_datablock.is_in_memory
        row.alert = flag or settings.is_dirty
        icon = 'FILE_TICK'if flag else 'IMPORT'
        text = 'Write and Save JSON' if flag else 'Write JSON'
        row.operator('lighting_overrider.write_settings', icon=icon, text=text)
        icon = 'FILE_REFRESH'if flag else 'EXPORT'
        text = 'Reload and Read JSON' if flag else 'Read JSON'
        row.operator('lighting_overrider.read_settings', icon=icon, text=text)

        row = col.row(align=True)
        row.alert = settings.is_dirty
        operator = 'lighting_overrider.write_apply_json' if settings.is_dirty else 'lighting_overrider.apply_json'
        icon = 'TEMP' if settings.is_dirty else 'PLAY'
        row.operator(operator, icon=icon)

        return

classes = [
    LOR_SettingsGroup,
    LOR_MetaSettings,
    LOR_OT_text_db_add,
    LOR_OT_toggle_enabled,
    LOR_PT_lighting_overrider_panel,
]

category_modules = [globals()[mod] for mod in categories.__all__]
for cat in category_modules:
    classes += [cat.panel_class]

def register():
    for c in classes:
        bpy.utils.register_class(c)
    bpy.types.Scene.LOR_Settings = bpy.props.PointerProperty(type=LOR_MetaSettings)
    bpy.app.handlers.load_post.append(init_on_load)
    bpy.app.handlers.save_pre.append(store_ref_on_save)

def unregister():
    for c in classes:
        bpy.utils.unregister_class(c)
    del bpy.types.Scene.LOR_Settings
    bpy.app.handlers.load_post.remove(init_on_load)
    bpy.app.handlers.save_pre.remove(store_ref_on_save)

#if __name__ == "__main__":
#    register()
