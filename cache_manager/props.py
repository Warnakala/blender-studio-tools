from typing import List, Any, Generator
import bpy


class CM_collection_property(bpy.types.PropertyGroup):
    # name: StringProperty() -> Instantiated by default
    coll_ptr: bpy.props.PointerProperty(name="Collection", type=bpy.types.Collection)


class CM_property_group_collection(bpy.types.PropertyGroup):
    cachefile: bpy.props.StringProperty(name="Cachefile", subtype="FILE_PATH")
    is_cache_loaded: bpy.props.BoolProperty(name="Cache Loaded", default=False)
    is_cache_hidden: bpy.props.BoolProperty(name="Cache Hidden", default=False)


class CM_property_group_scene(bpy.types.PropertyGroup):

    category: bpy.props.EnumProperty(  # type: ignore
        items=(
            ("EXPORT", "Export", "Import Cache Collections", "EXPORT", 0),
            ("IMPORT", "Import", "Export Cache Collections", "IMPORT", 1),
        ),
        default="EXPORT",
    )

    colls_export_index: bpy.props.IntProperty(name="Index", default=0)

    colls_import_index: bpy.props.IntProperty(name="Index", default=0)

    cache_version: bpy.props.StringProperty(name="Version", default="")


def get_cache_collections_import(
    context: bpy.types.Context,
) -> Generator[bpy.types.Collection, None, None]:
    for item in context.scene.cm_collections_import:
        yield item.coll_ptr


def get_cache_collections_export(
    context: bpy.types.Context,
) -> Generator[bpy.types.Collection, None, None]:
    for item in context.scene.cm_collections_export:
        yield item.coll_ptr


# ---------REGISTER ----------

classes: List[Any] = [
    CM_collection_property,
    CM_property_group_collection,
    CM_property_group_scene,
]


def register():

    for cls in classes:
        bpy.utils.register_class(cls)

    # Scene Properties
    bpy.types.Scene.cm_collections_export = bpy.props.CollectionProperty(
        type=CM_collection_property
    )

    bpy.types.Scene.cm_collections_import = bpy.props.CollectionProperty(
        type=CM_collection_property
    )

    bpy.types.Scene.cm = bpy.props.PointerProperty(type=CM_property_group_scene)

    # Collection Properties
    bpy.types.Collection.cm = bpy.props.PointerProperty(
        name="Cache Manager",
        type=CM_property_group_collection,
        description="Metadata that is required for the cache manager",
    )


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
