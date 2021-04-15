from typing import List, Any, Generator
import bpy


class CM_property_group_scene(bpy.types.PropertyGroup):
    # name: StringProperty() -> Instantiated by default
    coll_ptr: bpy.props.PointerProperty(name="Collection", type=bpy.types.Collection)


def get_cache_collections(
    context: bpy.types.Context,
) -> Generator[bpy.types.Collection, None, None]:
    for item in context.scene.cm_collections:
        yield item.coll_ptr


# ---------REGISTER ----------

classes: List[Any] = [CM_property_group_scene]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.cm_collections = bpy.props.CollectionProperty(
        type=CM_property_group_scene
    )
    bpy.types.Scene.cm_collections_index = bpy.props.IntProperty(
        name="Index", default=0
    )


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
