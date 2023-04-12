import bpy
from . import utils

class LOR_filter_string(bpy.types.PropertyGroup):
    string: bpy.props.StringProperty(default='')

class LOR_subsetting(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(default='setting', update=utils.mark_dirty)
    VALUE: bpy.props.FloatProperty('', update=utils.mark_dirty)
    FACTOR: bpy.props.FloatProperty(subtype='FACTOR', soft_min=0, soft_max=1, update=utils.mark_dirty)
    INTEGER: bpy.props.IntProperty('', update=utils.mark_dirty)
    BOOL: bpy.props.BoolProperty('', update=utils.mark_dirty)
    VECTOR: bpy.props.FloatVectorProperty('', update=utils.mark_dirty)
    COLOR: bpy.props.FloatVectorProperty(size=4, subtype='COLOR', default=(.5,.5,.5,1), soft_min=0, soft_max=1, update=utils.mark_dirty)
    STRING: bpy.props.StringProperty('', update=utils.mark_dirty)
    type: bpy.props.EnumProperty(items=[('VALUE', 'Value', '', '', 0),
                                        ('FACTOR', 'Factor', '', '', 1),
                                        ('INTEGER', 'Integer', '', '', 2),
                                        ('BOOL', 'Boolean', '', '', 3),
                                        ('VECTOR', 'Vector', '', '', 4),
                                        ('COLOR', 'Color', '', '', 5),
                                        ('STRING', 'String', '', '', 6),]
                                , update=utils.mark_dirty)
    
class LOR_setting(bpy.types.PropertyGroup):
    specifier: bpy.props.StringProperty('', update=utils.mark_dirty)
    subsettings: bpy.props.CollectionProperty(type=LOR_subsetting)
    setting_expanded: bpy.props.BoolProperty(default=True)

class LOR_UL_settings_list(bpy.types.UIList):
    
    filter_strings: bpy.props.CollectionProperty(type=LOR_filter_string)
    
    def filter_items(self, context, data, propname):
        
        settings = getattr(data, propname)
        helper_funcs = bpy.types.UI_UL_list
        
        flt_flags = []
        flt_neworder = []
        
        while not len(self.filter_strings) == len(settings):
            if len(self.filter_strings) < len(settings):
                self.filter_strings.add()
            else:
                self.filter_strings.remove(0)
        
        if self.filter_name:
            for i, set in enumerate(settings):
                self.filter_strings[i].string = ' '.join([subset.name for subset in set.subsettings]).lower()
                self.filter_strings[i].string = ' '.join([set.specifier, self.filter_strings[i].string])
            flt_flags = helper_funcs.filter_items_by_name(self.filter_name.lower(), self.bitflag_filter_item, self.filter_strings, "string",
                                                            reverse=self.use_filter_invert)
        
        return flt_flags, flt_neworder


classes = (
    LOR_subsetting,
    LOR_setting,
    LOR_filter_string,
    LOR_UL_settings_list,
)

def register():
    for c in classes:
        bpy.utils.register_class(c)

def unregister():
    for c in classes:
        bpy.utils.unregister_class(c)