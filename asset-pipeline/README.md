# asset-pipeline
asset-pipeline is a Blender Add-on that manages the Asset Pipeline of the Blender Studio. It includes an Asset Builder and an Asset Updater.

## Table of Contents
- [Installation](#installation)
- [How to get started](#how-to-get-started)
- [Configuration](#configuration)
- [Features](#features)
    - TODO
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
import bpy

from asset_pipeline.api import (
    AssetTransferMapping,
    TaskLayer,
)
```

And declare a TaskLayer class that Inherits from TaskLayer:

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


### hooks.py
The Asset Pipeline supports post transfer hooks that can be defined in the `hooks.py` file. Post Transfer hooks are simple Python functions that get executed **after** the successful transfer of all TaskLayers.

> **_NOTE:_** Post Transfer Hooks are only executed on a push from Asset Task to Asset Publish. **Not** on a pull.

These hooks could do anything but the the intent of a post merge hook is to bring the asset in the correct publish state. These are usually repetitive steps that the task artist has to do to prepare data for publishing (and often revert it again for working).

For an example config check out: `docs/production_config_example/hooks.py`

Start by importing these classes.

```
import bpy

from asset_pipeline.api import hook, Wildcard, DoNotMatch

```

An example definition of a hook can look like this:

```
@hook(match_asset="Generic Sprite")
def my_hook(asset_collection: bpy.types.Collection, **kwargs) -> None:
    pass

```

You define a regular python function and decorate it with the **hook()** decorator.
Note: The decorator needs to be executed.

The hook decorator as well as the function itself can specify arguments.

Let's first have a look at the hook decorator.
The Idea is that you can use the hook decorator to

first: Let the asset-pipeline know that this is an actual hook it should register

second: to filter under which conditions the hook gets executed.

For filtering you can use these key word arguments inside of the hook decorator braces:
- `match_asset_type`
- `match_asset match_asset`
- `match_task_layers`

For each of these keys you can supply these values:
* `str`: would perform an exact string match.
* `Iterator[str]`: would perform an exact string match with any of the given strings.
* `Type[Wildcard]`: would match any type for this parameter. This would be used so a hook
  is called for any value.
* `Type[DoNotMatch]`: would ignore this hook when matching the hook parameter. This is the default
  value for the matching criteria and would normally not be set directly in a
  production configuration.

With that in mind let's look at some more example hooks:

```
@hook()
def test_hook_A(**kwargs) -> None:
    pass
```
This hook has no filtering parameters so it is considered to be a **global** hook that always gets executed.

```
@hook(match_asset_type="Character")
def test_hook_B(**kwargs) -> None:
    pass
```

This hook will only be executed if current Asset is of type "Character".


```
@hook(match_task_layers="ShadingTaskLayer")
def test_hook_C(**kwargs) -> None:
    pass
```

This hook will only be executed if the Task Layer: "ShadingTaskLayer" was amongst the Task Layers that were selected for this transfer operation.

```
@hook(match_asset="Ellie")
def test_hook_D(**kwargs) -> None:
    pass
```
This hook will only be executed if the asset "Ellie" is processed.

```
@hook(
    match_asset="Generic Sprite",
    match_task_layers=["RiggingTaskLayer", "ShadingTaskLayer],
)
def test_hook_E(**kwargs) -> None:
    pass
```
This hook will only be executed if the asset "Generic Sprite" is processed and the "RiggingTaskLayer" or
"ShadingTaskLayer" was amongst the Task Layers that were selected for this transfer operation.



It is important to note that the asset-pipeline follows a certain order to execute the hooks. And that is exactly the one of the examples hook described above:

1. Global hooks
2. Asset Type Hooks
3. Task Layer Hooks
4. Asset Hooks
5. Asset + TaskLayer specific Hooks

The function itself should always have **\*\*kwargs** as a parameter. The asset-pipeline automatically passes a couple of useful keyword arguments to the function:
- `asset_collection`: bpy.types.Collection
- `context`: bpy.types.Context
- `asset_task`: asset_pipeline.asset_files.AssetTask
- `asset_dir`: asset_pipeline.asset_files.AssetDir

By exposing these parameters in the hook function you can use them in your code:
```
@hook()
def test_hook_F(context: bpy.types.Context, asset_collection: bpy.types.Collection, **kwargs) -> None:
    print(asset_collection.name)
```

## Development
In the project root you will find a `pyproject.toml` and `peotry.lock` file.
With `poetry` you can easily generate a virtual env for the project which should get you setup quickly.
Basic Usage: https://python-poetry.org/docs/basic-usage/

Create a sym link in your blender addons directory to the asset_pipeline folder.

### Getting Started as a Developer
