import os

from typing import List, Any, Generator, Optional
from pathlib import Path

import bpy

from . import propsdata


class CM_collection_property(bpy.types.PropertyGroup):
    # name: StringProperty() -> Instantiated by default
    coll_ptr: bpy.props.PointerProperty(name="Collection", type=bpy.types.Collection)


class CM_property_group_collection(bpy.types.PropertyGroup):
    cachefile: bpy.props.StringProperty(
        name="Cachefile",
        default="",
        subtype="FILE_PATH",
        options={"LIBRARY_EDITABLE"},
        override={"LIBRARY_OVERRIDABLE"},
    )
    is_cache_loaded: bpy.props.BoolProperty(
        name="Cache Loaded",
        default=False,
        options={"LIBRARY_EDITABLE"},
        override={"LIBRARY_OVERRIDABLE"},
    )
    is_cache_hidden: bpy.props.BoolProperty(
        name="Cache Hidden",
        default=False,
        options={"LIBRARY_EDITABLE"},
        override={"LIBRARY_OVERRIDABLE"},
    )


class CM_property_group_scene(bpy.types.PropertyGroup):

    category: bpy.props.EnumProperty(  # type: ignore
        items=(
            ("EXPORT", "Export", "Import Cache Collections", "EXPORT", 0),
            ("IMPORT", "Import", "Export Cache Collections", "IMPORT", 1),
        ),
        default="EXPORT",
        update=propsdata.category_upate_version_model,
    )

    colls_export_index: bpy.props.IntProperty(name="Index", default=0)

    colls_import_index: bpy.props.IntProperty(name="Index", default=0)

    cache_version: bpy.props.StringProperty(name="Version", default="v001")

    colls_export: bpy.props.CollectionProperty(type=CM_collection_property)

    colls_import: bpy.props.CollectionProperty(type=CM_collection_property)

    cacheconfig: bpy.props.StringProperty(
        name="Cacheconfig File", get=propsdata.gen_cacheconfig_path_str
    )

    cachedir: bpy.props.StringProperty(
        name="Cachedir", get=propsdata.gen_cachedir_path_str
    )
    cache_version_dir: bpy.props.StringProperty(
        name="Cache version dir", get=propsdata.get_cache_version_dir_path_str
    )

    use_cacheconfig_custom: bpy.props.BoolProperty(
        name="Custom Cacheconfig", default=False
    )
    cacheconfig_custom: bpy.props.StringProperty(
        name="Cacheconfig File",
        default="",
        subtype="FILE_PATH",
    )

    @property
    def cachedir_path(self) -> Optional[Path]:
        if not self.is_cachedir_valid:
            return None

        return Path(os.path.abspath(bpy.path.abspath(self.cachedir)))

    @property
    def is_cachedir_valid(self) -> bool:
        # check if file is saved
        if not self.cachedir:
            return False

        if not bpy.data.filepath and self.cachedir.startswith("//"):
            return False

        return True

    @property
    def cache_version_dir_path(self) -> Optional[Path]:
        if not self.is_cache_version_dir_valid:
            return None

        return Path(os.path.abspath(bpy.path.abspath(self.cache_version_dir)))

    @property
    def is_cache_version_dir_valid(self) -> bool:
        # check if file is saved
        if not self.cache_version_dir:
            return False

        if not bpy.data.filepath and self.cache_version_dir.startswith("//"):
            return False

        return True

    @property
    def is_cacheconfig_valid(self) -> bool:
        # check if file is saved
        if not self.cacheconfig:
            return False

        if not bpy.data.filepath and self.cacheconfig.startswith("//"):
            return False

        return True

    @property
    def is_cacheconfig_custom_valid(self) -> bool:
        # check if file is saved
        if not self.cacheconfig_custom:
            return False

        if not bpy.data.filepath and self.cacheconfig_custom.startswith("//"):
            return False

        return True

    @property
    def cacheconfig_path(self) -> Optional[Path]:
        if not self.is_cacheconfig_valid:
            return None
        return Path(os.path.abspath(bpy.path.abspath(self.cacheconfig)))

    @property
    def cacheconfig_custom_path(self) -> Optional[Path]:
        if not self.is_cacheconfig_custom_valid:
            return None
        return Path(os.path.abspath(bpy.path.abspath(self.cacheconfig_custom)))


def get_cache_collections_import(
    context: bpy.types.Context,
) -> Generator[bpy.types.Collection, None, None]:
    for item in context.scene.cm.colls_import:
        yield item.coll_ptr


def get_cache_collections_export(
    context: bpy.types.Context,
) -> Generator[bpy.types.Collection, None, None]:
    for item in context.scene.cm.colls_export:
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
    bpy.types.Scene.cm = bpy.props.PointerProperty(type=CM_property_group_scene)

    # Collection Properties
    bpy.types.Collection.cm = bpy.props.PointerProperty(
        name="Cache Manager",
        type=CM_property_group_collection,
        description="Metadata that is required for the cache manager",
        override={"LIBRARY_OVERRIDABLE"},
    )


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
