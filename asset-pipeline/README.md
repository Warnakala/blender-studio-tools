# asset-pipeline
asset-pipeline is a Blender Add-on that manages the Asset Pipeline of the Blender Studio. It includes an Asset Builder and an Asset Updater.

## Table of Contents
- [Installation](#installation)
- [How to get started](#how-to-get-started)
- [Features](#features)
    - TODO
- [Troubleshoot](#troubleshoot)
- [Credits](#credits)
- [Development](#development)
    - [Getting Started as a Developer](#getting-started-as-a-developer)


## Installation
Download or clone this repository.
In the root project folder you will find the 'asset_pipeline' folder. Place this folder in your Blender addons directory or create a sym link to it.

> **_NOTE:_** This add-on depends on other add-ons that are in the [Blender Studio Tools](https://developer.blender.org/diffusion/BSTS/).

Make sure to also install:
- [**blender-kitsu**](https://developer.blender.org/diffusion/BSTS/browse/master/blender-kitsu/)


## How to get started

After installing you need to setup the addon preferences to fit your environment.

The asset-pipeline add-on can be configured with some config files. The idea is that for each project you can have a custom configuration.

In the add-on preferences you need to setup the `Production Config Directory`. In this folder the add-on expects to find a file called `task_layers.py`. What exactly you need to define in this file is something you will learn in the [Configuration](#configuration) section.

## Configuration
The add-on can be configured on a per project basis, by pointing the the `Production Config Directory` property in the add-on preferences to a folder that contains the config files.

The config files need to be named a certain way and contain certain content.

<!--  TODO: Add note about autocomplete extra path feature of VSCode -->

### task_layer.py
In this file you can define the Task Layers and TransferSettings for this project.
For an example config check out: `docs/production_config_example/task_layers.py`


---
**Defining Task Layers**

To define a Task Layer import:

```
from asset_pipeline.api import (
    AssetTransferMapping,
    TaskLayer,
)
```

And declare a TaskLayer class:

```
class RiggingTaskLayer(TaskLayer):
    name = "Rigging"
    order = 0

    @classmethod
    def transfer_data(
        cls,
        context: bpy.types.Context,
        transfer_mapping: AssetTransferMapping,
        transfer_settings: bpy.types.PropertyGroup,
    ) -> None:
        pass

```

The `class name` ("RiggingTaskLayer") will be the Identifier for that TaskLayer in the code. The `name` attribute will  be used for display purposes in the UI.
There can be no TaskLayers with the same class name.

The `order` attribute will be used to determine in which order the TaskLayers are processed. Processing a TaskLayer means calling the `transfer_data()` class method.

> **_NOTE:_** The TaskLayer with the lowest order is a special TaskLayer. In the code it will be considered as the **base** TaskLayer.

The `transfer_data()` function of the base TaskLayer will never be called as it provides the base for other task layers to transfer their data to.

When Users push one or multiple TaskLayers from an Asset Task to an Asset Publish or pull vice versa, we need a base on which we can transfer the data.

During the transfer process there will be 3 Asset Collections:
- The Asset Collection of the Asset Task
- The Asset Collection of the Asset Publish
- The Target Asset Collection

The Target Asset Collection is a duplicate of either the Task or Publish Asset Collection and is the base on which we transfer data to. The decision to duplicate the Publish or Task Collection depends if the **base** Task Layer (Task Layer with lowers order) was enabled or not before the push or the pull.

If we push from an Asset Task to an Asset Publish and the base TaskLayer is among the selection we take the Asset Collection from the Asset Task as a base. If it is not selected we take the Asset Collection od the Asset Publish as a base.

If we pull from an Asset Publish to an Asset Task and the base TaskLayer is among the selection we take the Asset Collection from the Asset Publish as base. If it is not selected we take the Asset Collection of the Asset Task as a base.

The `transfer_data()` function contains 3 parameters that are useful when writing the transfer instructions.

```
    @classmethod
    def transfer_data(
        cls,
        context: bpy.types.Context,
        transfer_mapping: AssetTransferMapping,
        transfer_settings: bpy.types.PropertyGroup,
    ) -> None:
        pass
```

- **context**: Regular bpy.context

- **transfer_mapping**: Will be an instance of type `AssetTransferMapping`. This is a mapping between source and target for: **objects**, **materials** and **collections**. The maps are just dictionaries where the key is the source and the value the target. Both key and target are actual Blender ID Datablocks.

```
transfer_mapping.object_map: Dict[bpy.types.Object, bpy.types.Object]

transfer_mapping.collection_map: Dict[bpy.types.Collection, bpy.types.Collection]

transfer_mapping.material_map: Dict[bpy.types.Material, bpy.types.Material]

```
This enables you to do things like this:
```
for obj_source, obj_target in transfer_mapping.object_map.items():
    pass

for mat_source, mat_target in transfer_mapping.material_map.items():
    pass

...
```
- **transfer_settings**: Is the `TransferSettings` PropertyGroup that was defined in the task_layer.py module. More to that in the next section. If the PropertyGroup was defined you can just query its values as you would regularily do it inside of Blender: `transfer_settings.my_value`
---
**Defining Transfer Settings**

Transfer Settings are settings that Users can adjust inside of the Blender UI which can be queried in the `tranfer_data()` function and control certain aspects of the transfer.

To define Transfer Setting you just have to add a class called `TranferSettings` that inherits from `bpy.props.PropertyGroup` in the task_layer.py file.

```
class TransferSettings(bpy.types.PropertyGroup):
    transfer_mat: bpy.props.BoolProperty(name="Materials", default=True)
    transfer_uvs: bpy.props.BoolProperty(name="UVs", default=True)
    transfer_type: bpy.props.EnumProperty(
        name="Transfer Type",
        items=[("VERTEX_ORDER", "Vertex Order", ""), ("PROXIMITY", "Proximity", "")],
    )
```
You can use every native Blender Property type. These properties are automatically exposed in the `Transfer Settings` tab UI in the Asset Pipeline Panel.

## Development
In the project root you will find a `pyproject.toml` and `peotry.lock` file.
With `poetry` you can easily generate a virtual env for the project which should get you setup quickly.
Basic Usage: https://python-poetry.org/docs/basic-usage/

Create a sym link in your blender addons directory to the asset_pipeline folder.

### Getting Started as a Developer
