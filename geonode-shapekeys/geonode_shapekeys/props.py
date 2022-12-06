import bpy
from bpy.props import StringProperty, CollectionProperty, IntProperty, PointerProperty
from .operators import geomod_get_identifier

class GeoNodeShapeKey(bpy.types.PropertyGroup):
    name: StringProperty(
        description="Name of the modifier, storage object, etc", override={'LIBRARY_OVERRIDABLE'}
    )

    # On overridden objects, this stores the local object for sculpting.
    # Used for deletion and back and forth switching.
    storage_object: PointerProperty(
        name = "Storage Object",
        type = bpy.types.Object, override={'LIBRARY_OVERRIDABLE'}
    )

    @property
    def ob_name(self) -> str:
        return self.id_data.name + "." + self.name

    @property
    def modifier(self) -> bpy.types.Modifier:
        for m in self.id_data.modifiers:
            if m.type == 'NODES':
                identifier = geomod_get_identifier(m, 'Sculpt')
                if not identifier:
                    continue
                sculpt_ob = m[identifier]
                if not sculpt_ob:
                    continue
                if sculpt_ob == self.storage_object:
                    return m

registry = [
    GeoNodeShapeKey
]

def register():
    bpy.types.Object.geonode_shapekeys = CollectionProperty(
        type = GeoNodeShapeKey,
        override = {'LIBRARY_OVERRIDABLE', 'USE_INSERTION'}
    )
    bpy.types.Object.geonode_shapekey_index = IntProperty(options={'LIBRARY_EDITABLE'}, override={'LIBRARY_OVERRIDABLE'})
    
    # On local objects for sculpting, this stores the overridden object.
    # Used for swapping back and forth between the two objects.
    bpy.types.Object.geonode_shapekey_target = PointerProperty(
        name = "Target Object",
        type = bpy.types.Object,
    )