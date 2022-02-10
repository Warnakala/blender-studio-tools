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
from pathlib import Path

import bpy


class BSP_ASSET_asset_collection(bpy.types.PropertyGroup):
    """
    Collection Properties for Blender Studio Asset Collections
    """

    is_asset: bpy.props.BoolProperty(
        name="Is Asset",
        default=False,
        description="Controls if this Collection is recognized as an official Asset",
    )

    entity_name: bpy.props.StringProperty(name="Asset Name")  # type: ignore
    entity_id: bpy.props.StringProperty(name="Asset ID")  # type: ignore

    version: bpy.props.StringProperty(name="Asset Version")  # type: ignore
    project_id: bpy.props.StringProperty(name="Project ID")  # type: ignore

    rig: bpy.props.PointerProperty(type=bpy.types.Armature, name="Rig")  # type: ignore

    # Display properties that can't be set by User in UI.
    displ_entity_name: bpy.props.StringProperty(name="Asset Name", get=lambda self: self.entity_name)  # type: ignore
    displ_entity_id: bpy.props.StringProperty(name="Asset ID", get=lambda self: self.entity_id)  # type: ignore

    def clear(self) -> None:
        self.is_asset = False
        self.entity_name = ""
        self.entity_id = ""
        self.version = ""
        self.project_id = ""
        self.rig = None


class BSP_task_layer(bpy.types.PropertyGroup):

    """
    Property Group that can represent a minimal version of a Task Layer.
    Is used in BSP_ASSET_scene_properties as collection property.
    """

    task_layer_id: bpy.props.StringProperty(
        name="Task Layer ID",
        description="Unique Key that is used to query a Task Layer in TaskLayerAssembly.get_task_layer_config(.",
    )
    task_layer_name: bpy.props.StringProperty(
        name="Task Layer Name",
    )

    use: bpy.props.BoolProperty(
        name="Use",
        default=False,
        options={"LIBRARY_EDITABLE"},
        override={"LIBRARY_OVERRIDABLE"},
    )

    def reset_properties(self):
        self.use = False

    def as_dict(self):
        return {
            "use": self.use,
            "task_layer_id": self.task_layer_id,
            "task_layer_name": self.task_layer_name,
        }


class BSP_ASSET_scene_properties(bpy.types.PropertyGroup):
    """
    Scene Properties for Asset Pipeline
    """

    # Gets set by BSP_ASSET_init_asset_collection
    asset_collection: bpy.props.PointerProperty(type=bpy.types.Collection)  # type: ignore

    # Display properties that can't be set by User in UI.
    displ_asset_collection: bpy.props.StringProperty(name="Asset Collection", get=lambda self: self.asset_collection.name)  # type: ignore

    # There should only be one asset_collection per working task.
    # We don't want that the User can directly set the tasks Asset Collection.
    # The tmp_asset_collection property is used for the
    # BSP_ASSET_init_asset_collection operator to know what Collection it should initialize as Asset Collection.
    # This logic prevents having multiple Asset Collection per scene and forces user to clear the Asset Collection
    # before initializing another one.
    tmp_asset_collection: bpy.props.PointerProperty(type=bpy.types.Collection)  # type: ignore

    is_publish_in_progress: bpy.props.BoolProperty()  # type: ignore

    task_layers: bpy.props.CollectionProperty(type=BSP_task_layer)  # type: ignore

    task_layers_index: bpy.props.IntProperty(name="Task Layers Index", min=0)


# ----------------REGISTER--------------.

classes = [BSP_task_layer, BSP_ASSET_asset_collection, BSP_ASSET_scene_properties]


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


def unregister() -> None:
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
