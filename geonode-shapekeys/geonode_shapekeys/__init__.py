import bpy, os, importlib
from pathlib import Path
from bpy.utils import register_class, unregister_class
from bpy.types import AddonPreferences
from bpy.props import BoolProperty, StringProperty, EnumProperty
from typing import List

from . import operators, ui, props

bl_info = {
    'name': "GeoNode Shape Keys", 'author': "Demeter Dzadik", 
	'version': (0, 0, 1), 
	'blender': (3, 5, 0), 
	'description': "Shape keys in the modifier stack", 
	'location': "Properties->Mesh->Shape Keys->GeoNode ShapeKeys, only on overridden meshes", 
	'category': 'Animation'
}

modules = (
    operators,
    props,
    ui,
)


class GNSK_Preferences(AddonPreferences):
    bl_idname = __package__

    pablico_mode: BoolProperty(
        name="Pen Workaround",
        description="Add a button next to Influence sliders when multiple objects of the GeoNode ShapeKey are selected, to allow affecting all objects without having an Alt key"
    )
    node_import_type: EnumProperty(
        name = "Node Group Import Type",
        description = "Whether the GeometryNodes node tree should be linked or appended",
        items = [
            ('APPEND', 'Append', 'Append the node tree, making it local to the currently opened blend file'),
            ('LINK', 'Link', 'Link the node tree from an external blend file')
        ]
    )
    blend_path: StringProperty(
        name="Nodegroup File",
        description="Path to the file containing the GeoNode ShapeKey nodes",
        subtype='FILE_PATH'
    )

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True

        layout = layout.column(align=True)
        layout.prop(self, 'pablico_mode')
        layout.separator()

        layout.row().prop(self, 'node_import_type', expand=True)
        if self.node_import_type == 'LINK':
            layout.prop(self, 'blend_path')


def register_unregister_modules(modules: List, register: bool):
    """Recursively register or unregister modules by looking for either
    un/register() functions or lists named `registry` which should be a list of
    registerable classes.
    """
    register_func = register_class if register else unregister_class

    for m in modules:
        if register:
            importlib.reload(m)
        if hasattr(m, 'registry'):
            for c in m.registry:
                try:
                    register_func(c)
                except Exception as e:
                    un = 'un' if not register else ''
                    print(f"Warning: Failed to {un}register class: {c.__name__}")
                    print(e)

        if hasattr(m, 'modules'):
            register_unregister_modules(m.modules, register)

        if register and hasattr(m, 'register'):
            m.register()
        elif hasattr(m, 'unregister'):
            m.unregister()

@bpy.app.handlers.persistent
def autofill_node_blend_path(context, _dummy):
    if type(context) == str:
        context = bpy.context
    addon_prefs = context.preferences.addons[__package__].preferences
    current_path = addon_prefs.blend_path
    if not current_path:
        filedir = os.path.dirname(os.path.realpath(__file__))
        addon_prefs.blend_path = os.sep.join(filedir.split(os.sep) + ['geonodes.blend'])

def register():
    bpy.app.handlers.load_post.append(autofill_node_blend_path)
    register_class(GNSK_Preferences)
    register_unregister_modules(modules, True)

def unregister():
    bpy.app.handlers.load_post.remove(autofill_node_blend_path)
    unregister_class(GNSK_Preferences)
    register_unregister_modules(modules, False)

