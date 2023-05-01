import bpy
import re
import idprop
from . import utils
from .categories import rna_overrides

from rna_prop_ui import rna_idprop_ui_create


def struct_from_rna_path(rna_path):
    ''' Returns struct object for specified rna path.
    '''
    if not '.' in rna_path:
        return None
    elements = rna_path.rsplit('.', 1)
    if '][' in elements[1]:
        struct_path = f"{elements[0]}.{elements[1]}"
    else:
        struct_path = f"{elements[0]}.bl_rna.properties['{elements[1]}']"
    try:
        return eval(struct_path)
    except:
        return None


def stylize_name(path):
    ''' Splits words by '_', capitalizes them and separates them with ' '.
    '''
    custom_prop = utils.parse_rna_path_for_custom_property(path)
    if custom_prop:
        return f"{eval(custom_prop[0]+'.name')}: {custom_prop[1]}"
    
    path_elements = utils.parse_rna_path_to_elements(path)
    parent = '.'.join(path_elements[:-1])
    main = path_elements[-1]
    try:
        if main in ['default_value']:
            return eval(parent).name
        else:
            return f"{eval(parent).name}: {' '.join([word.capitalize() for word in main.split('_')])}"
    except:
        return ' '.join([word.capitalize() for word in main.split('_')])


class LOR_OT_override_picker(bpy.types.Operator):
    """Adds an operator on button mouse hover"""
    bl_idname = "lighting_overrider.override_picker"
    bl_label = "Add RNA Override"
    bl_options = {'UNDO'}

    rna_path: bpy.props.StringProperty(name="Data path to override", default="")
    override_float: bpy.props.FloatProperty(name="Override", default=0)
    batch_override: bpy.props.BoolProperty(name="Batch Override", default=False, options={'SKIP_SAVE'})

    init_val = None
    property = None
    override = None

    name_string = 'RNA Override'
    type = 'VALUE'

    _array_path_re = re.compile(r'^(.*)\[[0-9]+\]$')

    @classmethod
    def poll(cls, context):
        #print(f'poll: {bpy.ops.ui.copy_data_path_button.poll()}')
        return True

    def draw(self, context):
        layout = self.layout
        property = self.property

        if property is None:
            return

        col = layout.column()
        col.scale_y = 1.8
        col.scale_x = 1.5

        if self.type == 'COLOR':
            col.template_color_picker(context.scene, 'override', value_slider=True)

        col = layout.column()
        col.prop(context.scene, 'override')
        self.override = context.scene['override']

        if self.batch_override:
            row = layout.row()
            row.alert = True
            row.label(text=f'Batch Overriding {len(context.selected_objects)} Objects', icon='DOCUMENTS')


    def invoke(self, context, event):

        if not bpy.ops.ui.copy_data_path_button.poll():
            return {'PASS_THROUGH'}

        clip = context.window_manager.clipboard
        bpy.ops.ui.copy_data_path_button(full_path=True)
        rna_path = context.window_manager.clipboard
        context.window_manager.clipboard = clip

        if rna_path.endswith('name'):
            print("Warning: Don't override datablock names.")
            return {'CANCELLED'}

        if not rna_path.startswith('bpy.data.objects'):
            self.batch_override = False

        # Strip off array indices (f.e. 'a.b.location[0]' -> 'a.b.location')
        m = self._array_path_re.match(rna_path)
        if m:
            rna_path = m.group(1)

        self.rna_path = rna_path

        self.property = struct_from_rna_path(rna_path)
        
        if self.property is None:
            print("Warning: No struct was found for given RNA path.")
            return {'CANCELLED'}

        self.name_string = stylize_name(self.rna_path)
        
        if 'type' in dir(self.property):
            # Gather UI data
            keys = ['description', 'default', 'min', 'max', 'soft_min', 'soft_max', 'step', 'precision', 'subtype']

            vars = {}
            for key in keys:
                try:
                    vars[key] = eval(f'self.property.{key}')
                except:
                    print(f'{key} not in property')

            if self.property.type == 'FLOAT':
                vars['unit'] = self.property.unit
                if not self.property.is_array:
                    bpy.types.Scene.override = bpy.props.FloatProperty(name = self.name_string, **vars)
                else:
                    vars['size'] = self.property.array_length
                    vars['default'] = self.property.default_array[:]
                    if vars['subtype'] == 'COLOR':
                        self.type = 'COLOR'
                    else:
                        self.type = 'VECTOR'
                    bpy.types.Scene.override = bpy.props.FloatVectorProperty(name = self.name_string, **vars)
            elif self.property.type == 'STRING':
                bpy.types.Scene.override = bpy.props.StringProperty(name = self.name_string, **vars)
                self.type = 'STRING'
            elif self.property.type == 'BOOLEAN':
                bpy.types.Scene.override = bpy.props.BoolProperty(name = self.name_string, **vars)
                self.type = 'BOOL'
            elif self.property.type == 'INT':
                bpy.types.Scene.override = bpy.props.IntProperty(name = self.name_string, **vars)
                self.type = 'INTEGER'
            elif self.property.type == 'ENUM':
                self.type = 'STRING'
                items = [(item.identifier, item.name, item.description, item.icon, i) for i, item in enumerate(self.property.enum_items)]
                vars.pop('subtype', None)
                bpy.types.Scene.override = bpy.props.EnumProperty(items = items, name = self.name_string, **vars)
        else:
            vars = {}
            custom_prop = utils.parse_rna_path_for_custom_property(self.rna_path)
            if custom_prop:
                data_block = eval(custom_prop[0])
                property_name = custom_prop[1]
                vars = data_block.id_properties_ui(property_name).as_dict()

            if type(self.property) is float:
                bpy.types.Scene.override = bpy.props.FloatProperty(name = self.name_string, **vars)
            elif type(self.property) is idprop.types.IDPropertyArray:
                bpy.types.Scene.override = bpy.props.FloatVectorProperty(name = self.name_string, size=len(self.property), **vars)
                if vars['subtype'] in ['COLOR', 'COLOR_GAMMA']:
                    self.type = 'COLOR'
                else:
                    self.type = 'VECTOR'
            elif type(self.property) is str:
                bpy.types.Scene.override = bpy.props.StringProperty(name = self.name_string, **vars)
                self.type = 'STRING'
            elif type(self.property) is int:
                bpy.types.Scene.override = bpy.props.IntProperty(name = self.name_string, **vars)
                self.type = 'INTEGER'
            elif type(self.property) == bool:
                bpy.types.Scene.override = bpy.props.BoolProperty(name = self.name_string, **vars)
                self.type = 'BOOL'
        
        # check for custom property

        context.scene.override = eval(rna_path)

        self.override = context.scene.override

        self.init_val = eval(rna_path)

        wm = context.window_manager
        state = wm.invoke_props_dialog(self)
        if state in {'FINISHED', 'CANCELLED'}:
            del context.scene['override']
            return state
        else:
            return state

    def execute(self, context):
        meta_settings = context.scene.LOR_Settings
        settings = utils.get_settings(meta_settings)

        path_elements = utils.parse_rna_path_to_elements(self.rna_path)

        if context.scene.override==self.init_val:
            del context.scene['override']
            return {'CANCELLED'}

        exec(self.rna_path+f' = context.scene.override')

        add_info=[self.name_string, self.rna_path, context.scene.override, self.type]
        rna_overrides.add_rna_override(context, add_info)

        if path_elements[2].startswith('objects'):
            exec('.'.join(path_elements[:3])+'.update_tag()')

        if not self.batch_override:
            del context.scene['override']
            return {'FINISHED'}

        for ob in context.selected_objects:
            subpath = '.'.join(path_elements[3:])
            if ob.library:
                rna_path = f'bpy.data.objects["{ob.name}", "{ob.library.filepath}"].{subpath}'
            else:
                rna_path = f'bpy.data.objects["{ob.name}"].{subpath}'

            try:
                eval(rna_path)
            except:
                continue

            exec(rna_path+f' = context.scene.override')
            name_string = stylize_name(rna_path)
            add_info = [name_string, rna_path, context.scene.override, self.type]
            rna_overrides.add_rna_override(context, add_info)
        utils.kick_evaluation(list(context.selected_objects))

        del context.scene['override']
        utils.kick_evaluation()
        return {'FINISHED'}

    def cancel(self, context):
        del context.scene['override']
        return


classes = [
    LOR_OT_override_picker,
    ]

def register():
    for c in classes:
        bpy.utils.register_class(c)

    wm = bpy.context.window_manager
    if wm.keyconfigs.addon is not None:
        km = wm.keyconfigs.addon.keymaps.new(name="User Interface")
        kmi = km.keymap_items.new("lighting_overrider.override_picker","O", "PRESS",shift=False, ctrl=False)
        kmi.properties.batch_override = False
        kmi = km.keymap_items.new("lighting_overrider.override_picker","O", "PRESS",shift=False, ctrl=False, alt=True)
        kmi.properties.batch_override = True

def unregister():
    for c in classes:
        bpy.utils.unregister_class(c)


if __name__ == "__main__":
    register()
