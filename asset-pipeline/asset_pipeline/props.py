# ***** BEGIN GPL LICENSE BLOCK *****
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
# ***** END GPL LICENCE BLOCK *****
#
# (c) 2021, Blender Foundation - Paul Golter
import os
from typing import Optional, Dict, Any, List, Tuple

from pathlib import Path

import bpy

try:
    import blender_kitsu.cache

    kitsu_available = True
except:
    kitsu_available = False
from . import constants, builder, asset_files, lib_util
from .builder.metadata import MetadataAsset, MetadataTaskLayer
from .asset_files import AssetPublish

import logging

logger = logging.getLogger("BSP")


class FailedToGetAssetPublish(Exception):
    pass


class BSP_ASSET_asset_collection(bpy.types.PropertyGroup):
    """
    Collection Properties for Blender Studio Asset Collections
    """

    # Global is asset identifier.
    is_asset: bpy.props.BoolProperty(  # type: ignore
        name="Is Asset",
        default=False,
        description="Controls if this Collection is recognized as an official Asset",
    )

    # Asset identification properties.
    # We use entity_ prefix as blender uses .id as built in attribute already, which
    # might be confusing.
    entity_parent_id: bpy.props.StringProperty(name="Asset Type ID")  # type: ignore
    entity_parent_name: bpy.props.StringProperty(name="Asset Type")  # type: ignore
    entity_name: bpy.props.StringProperty(name="Asset Name")  # type: ignore
    entity_id: bpy.props.StringProperty(name="Asset ID")  # type: ignore
    project_id: bpy.props.StringProperty(name="Project ID")  # type: ignore

    # For Asset Publish.
    is_publish: bpy.props.BoolProperty(  # type: ignore
        name="Is Publish",
        description="Controls if this Collection is an Asset Publish to distinguish it from a 'working' Collection",
    )
    version: bpy.props.StringProperty(name="Asset Version")  # type: ignore
    publish_path: bpy.props.StringProperty(name="Asset Publish")  # type: ignore

    # Other properties, useful for external scripts.
    rig: bpy.props.PointerProperty(type=bpy.types.Armature, name="Rig")  # type: ignore

    # Metadata for Asset Builder.
    transfer_suffix: bpy.props.StringProperty(name="Transfer Suffix")  # type: ignore

    # Display properties that can't be set by User in UI.
    displ_entity_name: bpy.props.StringProperty(name="Asset Name", get=lambda self: self.entity_name)  # type: ignore
    displ_entity_id: bpy.props.StringProperty(name="Asset ID", get=lambda self: self.entity_id)  # type: ignore

    displ_is_publish: bpy.props.BoolProperty(name="Is Publish", get=lambda self: self.is_publish)  # type: ignore
    displ_version: bpy.props.StringProperty(name="Asset Version", get=lambda self: self.version)  # type: ignore
    displ_publish_path: bpy.props.StringProperty(name="Asset Path", get=lambda self: self.publish_path)  # type: ignore

    def clear(self) -> None:
        """
        Gets called when uninitializing an Asset Collection for example.
        """

        self.is_asset = False

        self.entity_parent_id = ""
        self.entity_parent_name = ""
        self.entity_name = ""
        self.entity_id = ""
        self.project_id = ""

        self.is_publish = False
        self.version = ""

        self.rig = None

        self.transfer_suffix = ""

    def gen_metadata_class(self) -> MetadataAsset:
        # These keys represent all mandatory arguments for the data class metadata.MetaAsset
        # The idea is, to be able to construct a MetaAsst from this dict.
        # Note: This function will most likely only be called when creating the first asset version
        # to get some data to start with.
        keys = [
            "entity_name",
            "entity_id",
            "entity_parent_id",
            "entity_parent_name",
            "project_id",
            "version",
        ]
        d = {}
        for key in keys:

            # MetaAsset tries to mirror Kitsu data structure as much as possible.
            # Remove entity_ prefix.
            if key.startswith("entity_"):
                d[key.replace("entity_", "")] = getattr(self, key)
            else:
                d[key] = getattr(self, key)

        # Set status to default asset status.
        d["status"] = constants.DEFAULT_ASSET_STATUS
        return MetadataAsset.from_dict(d)

    def update_props_by_asset_publish(self, asset_publish: AssetPublish) -> None:
        self.is_publish = True
        self.version = asset_publish.get_version()
        self.status = asset_publish.metadata.meta_asset.status.name

    def get_asset_publish(self) -> AssetPublish:
        if not self.is_publish:
            raise FailedToGetAssetPublish(
                f"The collection {self.id_data.name} is not an asset publish"
            )

        # Will throw error if item is not lib.
        lib = lib_util.get_item_lib(self.id_data)

        return AssetPublish(Path(os.path.abspath(bpy.path.abspath(lib.filepath))))


class BSP_task_layer(bpy.types.PropertyGroup):

    """
    Property Group that can represent a minimal TaskLayer.
    Note: It misses properties compared to MetadataTaskLayer class, contains only the ones
    needed for internal use. Also contains 'use' attribute to avoid creating a new property group
    to mimic more the TaskLayer TaskLayerConfig setup.
    Is used in BSP_ASSET_scene_properties as collection property.
    """

    task_layer_id: bpy.props.StringProperty(  # type: ignore
        name="Task Layer ID",
        description="Unique Key that is used to query a Task Layer in TaskLayerAssembly.get_task_layer_config()",
    )
    task_layer_name: bpy.props.StringProperty(  # type: ignore
        name="Task Layer Name",
    )

    is_locked: bpy.props.BoolProperty(  # type: ignore
        name="Is Locked",
    )

    use: bpy.props.BoolProperty(  # type: ignore
        name="Use",
    )

    def as_dict(self) -> Dict[str, Any]:
        return {
            "use": self.use,
            "is_locked": self.is_locked,
            "task_layer_id": self.task_layer_id,
            "task_layer_name": self.task_layer_name,
        }


class BSP_asset_file(bpy.types.PropertyGroup):

    """
    Property Group that can represent a minimal version of an Asset File.
    """

    path_str: bpy.props.StringProperty(  # type: ignore
        name="Path",
    )
    task_layers: bpy.props.CollectionProperty(type=BSP_task_layer)  # type: ignore

    status: bpy.props.StringProperty(name="Status")  # type: ignore

    returncode_publish: bpy.props.IntProperty(
        name="Return Code",
        description=(
            "This code represents the return code of the subprocess that gets "
            "started when publishing. Is used to display a warning in UI if something went wrong"
        ),
        default=-1,
    )

    @property
    def path(self) -> Optional[Path]:
        if not self.path_str:
            return None
        return Path(self.path_str)

    def as_dict(self) -> Dict[str, Any]:
        return {"path": self.path}

    def add_task_layer_from_metaclass(self, metadata_task_layer: MetadataTaskLayer):
        item = self.task_layers.add()
        # TODO: could be made more procedural.
        item.task_layer_id = metadata_task_layer.id
        item.task_layer_name = metadata_task_layer.name
        item.is_locked = metadata_task_layer.is_locked

    def update_props_by_asset_publish(self, asset_publish: AssetPublish) -> None:
        self.name = asset_publish.path.name
        self.path_str = asset_publish.path.as_posix()
        self.status = asset_publish.metadata.meta_asset.status.name

        # Clear task layers.
        self.task_layers.clear()

        # Add task layers.
        for tl in asset_publish.metadata.meta_task_layers:
            self.add_task_layer_from_metaclass(tl)


class BSP_ASSET_imported_asset_collection(bpy.types.PropertyGroup):

    collection: bpy.props.PointerProperty(type=bpy.types.Collection)  # type: ignore

    asset_publishes: bpy.props.CollectionProperty(type=BSP_asset_file)  # type: ignore

    def get_asset_publishes_as_bl_enum(
        self, context: bpy.types.Context
    ) -> List[Tuple[str, str, str]]:
        return [
            (p.name, asset_files.get_file_version(p.path), "")
            for p in self.asset_publishes
        ]

    target_publish: bpy.props.EnumProperty(items=get_asset_publishes_as_bl_enum)  # type: ignore


class BSP_undo_context(bpy.types.PropertyGroup):

    """ """

    files_created: bpy.props.CollectionProperty(type=BSP_asset_file)  # type: ignore

    def add_step_asset_publish_create(self, asset_publish: AssetPublish) -> None:
        item = self.files_created.add()
        item.name = asset_publish.path.name
        item.path_str = asset_publish.path.as_posix()

    def clear(self):
        self.files_created.clear()


class BSP_task_layer_lock_plan(bpy.types.PropertyGroup):

    """
    Property Group that can represent a minimal version of a TaskLayerLockPlan.
    """

    path_str: bpy.props.StringProperty(  # type: ignore
        name="Path",
    )
    task_layers: bpy.props.CollectionProperty(type=BSP_task_layer)  # type: ignore

    @property
    def path(self) -> Optional[Path]:
        if not self.path_str:
            return None
        return Path(self.path_str)


class BSP_ASSET_scene_properties(bpy.types.PropertyGroup):
    """Scene Properties for Asset Pipeline"""

    def update_asset_collection(self, context):
        """There should only be one asset collection per file, so before
        initializing another asset collection, wipe any asset collection
        data in the entire file.
        """

        for coll in bpy.data.collections:
            # Clear Asset Collection attributes.
            coll.bsp_asset.clear()

        if not self.asset_collection:
            return

        # Unitialize Asset Context.
        builder.ASSET_CONTEXT = None
        builder.opsdata.clear_task_layers(context)

        if kitsu_available:
            # Get active asset.
            asset = blender_kitsu.cache.asset_active_get()
            asset_type = blender_kitsu.cache.asset_type_active_get()

            if asset:
                # Set Asset Collection attributes.
                self.is_asset = True
                self.entity_id = asset.id
                self.entity_name = asset.name
                self.project_id = asset.project_id
                self.entity_parent_id = asset_type.id
                self.entity_parent_name = asset_type.name

            logger.info(
                f"Initiated Collection: {self.asset_collection.name} as Kitsu Asset: {asset.name}"
            )

        logger.info(f"Initiated Collection: {self.asset_collection.name}")

        # Init Asset Context.
        if bpy.ops.bsp_asset.create_asset_context.poll():
            bpy.ops.bsp_asset.create_asset_context()

    asset_collection: bpy.props.PointerProperty(
        type=bpy.types.Collection,
        name="Asset Collection",
        update=update_asset_collection,
    )  # type: ignore

    is_publish_in_progress: bpy.props.BoolProperty()  # type: ignore
    are_task_layers_pushed: bpy.props.BoolProperty()  # type: ignore

    task_layers_push: bpy.props.CollectionProperty(type=BSP_task_layer)  # type: ignore
    task_layers_pull: bpy.props.CollectionProperty(type=BSP_task_layer)  # type: ignore

    def task_layers(self, context):
        return (
            [(tl.name, tl.name, tl.name) for tl in builder.PROD_CONTEXT.task_layers]
            if builder.PROD_CONTEXT
            else []
        )

    asset_publishes: bpy.props.CollectionProperty(type=BSP_asset_file)  # type: ignore

    task_layers_push_index: bpy.props.IntProperty(name="Task Layers Owned Index", min=0)  # type: ignore
    task_layers_pull_index: bpy.props.IntProperty(name="Task Layers Pull Index", min=0)  # type: ignore
    asset_publishes_index: bpy.props.IntProperty(name="Asset Publishes Index", min=0)  # type: ignore
    task_layer_lock_plans_index: bpy.props.IntProperty(name="Task Layer Lock Plans Index", min=0)  # type: ignore

    undo_context: bpy.props.PointerProperty(type=BSP_undo_context)  # type: ignore

    task_layer_lock_plans: bpy.props.CollectionProperty(type=BSP_task_layer_lock_plan)  # type: ignore

    imported_asset_collections: bpy.props.CollectionProperty(type=BSP_ASSET_imported_asset_collection)  # type: ignore
    imported_asset_collections_index: bpy.props.IntProperty(min=0)  # type: ignore


def get_asset_publish_source_path(context: bpy.types.Context) -> str:
    if not builder.ASSET_CONTEXT:
        return ""

    if not builder.ASSET_CONTEXT.asset_publishes:
        return ""

    return builder.ASSET_CONTEXT.asset_publishes[-1].path.name


class BSP_ASSET_tmp_properties(bpy.types.PropertyGroup):

    # Asset publish source
    asset_publish_source_path: bpy.props.StringProperty(  # type: ignore
        name="Source", get=get_asset_publish_source_path
    )

    new_asset_version: bpy.props.BoolProperty(  # type: ignore
        name="New Version",
        description="Controls if new Version should be created when starting the publish",
    )


# ----------------REGISTER--------------.

classes = [
    BSP_task_layer,
    BSP_asset_file,
    BSP_undo_context,
    BSP_ASSET_asset_collection,
    BSP_task_layer_lock_plan,
    BSP_ASSET_imported_asset_collection,
    BSP_ASSET_scene_properties,
    BSP_ASSET_tmp_properties,
]


def register() -> None:
    for cls in classes:
        bpy.utils.register_class(cls)

    # Collection Asset Pipeline Properties.
    bpy.types.Collection.bsp_asset = bpy.props.PointerProperty(
        type=BSP_ASSET_asset_collection
    )

    # Scene Asset Pipeline Properties.
    bpy.types.Scene.bsp_asset = bpy.props.PointerProperty(
        type=BSP_ASSET_scene_properties
    )

    # Window Manager Properties.
    bpy.types.WindowManager.bsp_asset = bpy.props.PointerProperty(
        type=BSP_ASSET_tmp_properties
    )


def unregister() -> None:
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
