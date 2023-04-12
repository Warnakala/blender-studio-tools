from .. import utils
from ..templates import *
import bpy

import inspect

def settings_as_dict(settings):
    data = {}
    for setting in settings.rna_overrides:
        if isinstance(getattr(setting, setting.type), str):
            data[setting.path] = [getattr(setting, setting.type), setting.type, setting.name]
        elif not setting.bl_rna.properties[setting.type].is_array:
            data[setting.path] = [getattr(setting, setting.type), setting.type, setting.name]
        else:
            data[setting.path] = [getattr(setting, setting.type)[:], setting.type, setting.name]
    return data


def apply_settings(data):
    ''' Applies custom overrides on specified rna data paths.
    '''
    if not data:
        return

    for path in data:
        try:
            if data[path][1] == 'STRING':
                exec(path+f" = '{data[path][0]}'")
            else:
                exec(path+f' = {data[path][0]}')
        except:
            print(f'Warning: Failed to assign property {data[path][2]} at {path}')


def load_settings(settings, data):
    while len(settings.rna_overrides) > 0:
        settings.rna_overrides.remove(0)

    for path in data.keys():
        value = data[path]
        new_setting = settings.rna_overrides.add()
        new_setting.name = value[2]
        new_setting.path = path
        new_setting.type = value[1]
        setattr(new_setting, value[1], value[0])

    settings.rna_overrides_index = min(settings.rna_overrides_index, len(settings.rna_overrides)-1)


class LOR_OT_rna_overrides_apply(bpy.types.Operator):
    """
    """
    bl_idname = "lighting_overrider.rna_overrides_apply"
    bl_label = "Apply RNA Overrides"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        meta_settings = context.scene.LOR_Settings
        settings = utils.get_settings(meta_settings)

        apply_settings(settings_as_dict(settings))
        utils.kick_evaluation()

        return {'FINISHED'}


class LOR_rna_override(LOR_subsetting):
    name: bpy.props.StringProperty(default='RNA Override')
    path: bpy.props.StringProperty(default='bpy.data.')

def add_rna_override(context, add_info = None):
    meta_settings = context.scene.LOR_Settings
    settings = utils.get_settings(meta_settings)

    new_setting = None
    if add_info:
        for rna_override in settings.rna_overrides:
            if rna_override.path == add_info[1]:
                new_setting = rna_override
                add_info[0] = new_setting.name
    if not new_setting:
        new_setting = settings.rna_overrides.add()
    settings.is_dirty = True

    if add_info:
        new_setting.name = add_info[0]
        new_setting.path = add_info[1]
        new_setting.type = add_info[3]
        setattr(new_setting, new_setting.type, add_info[2])

    settings.rna_overrides_index = len(settings.rna_overrides)-1


class LOR_OT_rna_override_add(bpy.types.Operator):
    """
    """
    bl_idname = "lighting_overrider.rna_override_add"
    bl_label = "Add Variable Setting"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        add_rna_override(context)
        return {'FINISHED'}


class LOR_OT_rna_override_remove(bpy.types.Operator):
    """
    """
    bl_idname = "lighting_overrider.rna_override_remove"
    bl_label = "Remove Variable Setting"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        meta_settings = context.scene.LOR_Settings
        settings = utils.get_settings(meta_settings)
        return len(settings.rna_overrides)>0

    def execute(self, context):
        meta_settings = context.scene.LOR_Settings
        settings = utils.get_settings(meta_settings)
        settings.rna_overrides.remove(settings.rna_overrides_index)
        settings.is_dirty = True

        if settings.rna_overrides_index >= len(settings.rna_overrides):
            settings.rna_overrides_index = len(settings.rna_overrides)-1
        return {'FINISHED'}


class LOR_OT_rna_override_cleanup(bpy.types.Operator):
    """ Removes outdated RNA overrides from the list
    """
    bl_idname = "lighting_overrider.rna_override_cleanup"
    bl_label = "Cleanup RNA Overrides"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        meta_settings = context.scene.LOR_Settings
        settings = utils.get_settings(meta_settings)
        return len(settings.rna_overrides)>0

    def execute(self, context):
        meta_settings = context.scene.LOR_Settings
        settings = utils.get_settings(meta_settings)

        remove_list = []
        for i, setting in enumerate(settings.rna_overrides):
            try:
                eval(setting.path)
            except:
                remove_list += [i]
                continue
        if remove_list:
            settings.is_dirty = True
            for j, i in enumerate(remove_list):
                settings.rna_overrides.remove(i-j)
        return {'FINISHED'}


class LOR_UL_rna_overrides_list(LOR_UL_settings_list):

    def draw_item(
        self, context, layout, data, item, icon, active_data, active_propname, index):

        meta_settings = context.scene.LOR_Settings
        settings = utils.get_settings(meta_settings)

        row = layout.row()
        col_top = row.column()
        row = col_top.row(align=True)
        row.prop(item, "name", text='', icon='DOT', emboss=False)

        col = row.column()
        if index == settings.rna_overrides_index:
            col.operator("lighting_overrider.rna_override_remove", icon='X', text="", emboss=False)
        else:
            col.label(text='', icon='BLANK1')

        row = col_top.row(align=True)
        split = row.split(factor=.7, align=True)
        split.prop(item, "path", text='')
        split.prop(item, item.type, text='')
        row.prop(item, 'type', text='', icon='THREE_DOTS', icon_only=True, emboss=False)
        if index >= len(settings.rna_overrides)-1:
            col_top.operator("lighting_overrider.rna_override_add", icon='ADD', text="", emboss=False)

    def filter_items(self, context, data, propname):

        settings = getattr(data, propname)
        helper_funcs = bpy.types.UI_UL_list

        flt_flags = []
        flt_neworder = []

        if self.filter_name:
            flt_flags = helper_funcs.filter_items_by_name(self.filter_name, self.bitflag_filter_item, settings, "name",
                                                            reverse=self.use_filter_invert)

        return flt_flags, flt_neworder


class LOR_PT_rna_overrides_panel(bpy.types.Panel):
    bl_parent_id = "LOR_PT_lighting_overrider_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_label = "RNA Overrides"
    bl_category = 'Overrides'
    bl_options = {"DEFAULT_CLOSED"}

    def draw_header(self, context):
        self.layout.label(text='', icon='RNA')
        return

    def draw_header_preset(self, context):
        layout = self.layout
        col = layout.column()

        meta_settings = context.scene.LOR_Settings
        settings = utils.get_settings(meta_settings)

        col.enabled = False
        col.label(text=str(len(settings.rna_overrides)))
        return

    def draw(self, context):
        layout = self.layout

        meta_settings = context.scene.LOR_Settings
        settings = utils.get_settings(meta_settings)

        col_top = layout.column()
        if not meta_settings.enabled:
            col_top.enabled = False
        row = col_top.row(align=True)
        row.operator("lighting_overrider.rna_override_add", icon='ADD', text="")
        row.operator("lighting_overrider.rna_override_remove", icon='REMOVE', text="")
        row.operator("lighting_overrider.rna_override_cleanup", icon='BRUSH_DATA', text="Clean Up")

        row = col_top.row(align=True)
        col = row.column()
        col.template_list(
            "LOR_UL_rna_overrides_list",
            "",
            settings,
            "rna_overrides",
            settings,
            "rna_overrides_index",
            rows=2,
        )
        col.operator('lighting_overrider.rna_overrides_apply', icon='PLAY')
        return

panel_class = LOR_PT_rna_overrides_panel

classes = (
    LOR_rna_override,
    LOR_UL_rna_overrides_list,
    LOR_OT_rna_override_add,
    LOR_OT_rna_override_remove,
    LOR_OT_rna_overrides_apply,
    LOR_OT_rna_override_cleanup,
    )

def register():
    for c in classes:
        bpy.utils.register_class(c)

def unregister():
    for c in classes:
        bpy.utils.unregister_class(c)
