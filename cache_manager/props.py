import os

from typing import List, Any, Generator, Optional
from pathlib import Path

import bpy

from . import propsdata


class CM_collection_property(bpy.types.PropertyGroup):
    # name: StringProperty() -> Instantiated by default
    coll_ptr: bpy.props.PointerProperty(name="Collection", type=bpy.types.Collection)


class CM_property_group_collection(bpy.types.PropertyGroup):

    is_cache_coll: bpy.props.BoolProperty(
        name="Cache Collection",
        default=False,
        options={"LIBRARY_EDITABLE"},
        override={"LIBRARY_OVERRIDABLE"},
    )

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

    def reset_properties(self):
        self.is_cache_coll = False
        self.cachefile = ""
        self.is_cache_loaded = False
        self.is_cache_hidden = False


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

    xsamples: bpy.props.IntProperty(
        name="Transform Samples",
        description="Sets the xsamples argument of bpy.ops.wm.alembic_export to the specified value",
        default=3,
        min=1,
        max=128,
        step=1,
    )
    gsamples: bpy.props.IntProperty(
        name="Geometry Samples",
        description="Sets the gsamples argument of bpy.ops.wm.alembic_export to the specified value",
        default=3,
        min=1,
        max=128,
        step=1,
    )
    sh_open: bpy.props.FloatProperty(
        name="Shutter Open",
        description="Sets the sh_open argument of bpy.ops.wm.alembic_export to the specified value",
        default=0,
        min=-1.0,
        max=1.0,
        step=0.1,
    )
    sh_close: bpy.props.FloatProperty(
        name="Shutter Close",
        description="Sets the sh_close argument of bpy.ops.wm.alembic_export to the specified value",
        default=1,
        min=-1.0,
        max=1.0,
        step=0.1,
    )

    frame_handles_left: bpy.props.IntProperty(
        name="Frame Handles Left",
        description="Caching starts at the frame in of the scene minus the specified amount of frame handles.",
        default=10,
        min=0,
        step=1,
    )
    frame_handles_right: bpy.props.IntProperty(
        name="Frame Handles Right",
        description="Caching stops at the frame out of the scene plus the specified amount of frame handles.",
        default=10,
        min=0,
        step=1,
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
        if item.coll_ptr:
            yield item.coll_ptr


def get_cache_collections_export(
    context: bpy.types.Context,
) -> Generator[bpy.types.Collection, None, None]:
    for item in context.scene.cm.colls_export:
        if item.coll_ptr:
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
