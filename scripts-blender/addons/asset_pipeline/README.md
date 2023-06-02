# Asset Pipeline
asset-pipeline is a Blender Add-on that manages the Asset Pipeline of the Blender Studio. It includes an Asset Builder and an Asset Updater. 

[Asset Pipeline Presentation](https://youtu.be/IBTEBhAouKc?t=527)

## Table of Contents
- [Installation](#installation)
- [How to get started](#how-to-get-started)
- [Configuration](#configuration)
    - [Task Layers](#task_layers.py)
    - [Hooks](#hooks.py)
- [Getting Started as a Developer](#getting-started-as-a-developer)
    - [Context](#context)
    - [UI](#ui)
    - [Asset Collection](#asset-collection)
    - [Asset Files](#asset-files)
    - [Metadata](#metadata)
    - [Asset Importer](#asset-importer)
    - [Asset Mapping](#asset-mapping)
    - [Asset Builder](#asset-builder)
    - [Asset Updater](#asset-updater)


## Installation
1. Download [latest release](../addons/overview) 
2. Launch Blender, navigate to `Edit > Preferences` select `Addons` and then `Install`, 
3. Navigate to the downloaded add-on and select `Install Add-on` 

> **_NOTE:_** This add-on depends on other add-ons that are in the [Blender Studio Tools](https://projects.blender.org/studio/blender-studio-pipeline).

Make sure to also install:
- [**blender-kitsu**](/addons/blender_kitsu)


## How to get started

After installing you need to setup the addon preferences to fit your environment.

The asset-pipeline add-on can be configured with some config files. The idea is that for each project you can have a custom configuration.

In the add-on preferences you need to setup the `Production Config Directory`. In this folder the add-on expects to find a file called `task_layers.py`. What exactly you need to define in this file is something you will learn in the [Configuration](#configuration) section.

To understand the underlying concepts of the Asset Pipeline it is recommended to read [this](https://studio.blender.org/blog/asset-pipeline-update-2022/) article.

## Configuration
The add-on can be configured on a per project basis, by pointing the the `Production Config Directory` property in the add-on preferences to a folder that contains the config files.

The config files need to be named a certain way and contain certain content.

<!--  TODO: Add note about autocomplete extra path feature of VSCode -->

### task_layers.py
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
        build_context: BuildContext,
        transfer_mapping: AssetTransferMapping,
        transfer_settings: bpy.types.PropertyGroup,
    ) -> None:
        pass

```

The `class name` ("RiggingTaskLayer") will be the Identifier for that TaskLayer in the code. The `name` attribute will  be used for display purposes in the UI.
There can be no TaskLayers with the same class name.

The `order` attribute will be used to determine in which order the TaskLayers are processed. Processing a TaskLayer means calling the `transfer_data()` class method.

> **_NOTE:_** The TaskLayer with the lowest order is a special TaskLayer. In the code it will be considered as the **base** TaskLayer.

The `transfer_data()` function of the base TaskLayer should be empty as it provides the base for other task layers to transfer their data to. But it will still be called as there are cases where Users might need that functionality.

When Users push one or multiple TaskLayers from an Asset Task to an Asset Publish or pull vice versa, we need a base on which we can transfer the data.

During the transfer process there will be 3 Asset Collections:
- The Asset Collection of the Asset Task
- The Asset Collection of the Asset Publish
- The Target Asset Collection

The Target Asset Collection is a duplicate of either the Task or Publish Asset Collection and is the base on which we transfer data to. The decision to duplicate the Publish or Task Collection depends on if the **base** Task Layer (Task Layer with lowers order) was enabled or not before the push or the pull.

If we push from an Asset Task to an Asset Publish and the base TaskLayer is among the selection we take the Asset Collection from the Asset Task as a base. If it is not selected we take the Asset Collection od the Asset Publish as a base.

If we pull from an Asset Publish to an Asset Task and the base TaskLayer is among the selection we take the Asset Collection from the Asset Publish as base. If it is not selected we take the Asset Collection of the Asset Task as a base.

The `transfer_data()` function contains 4 parameters that are useful when writing the transfer instructions.

```
    @classmethod
    def transfer_data(
        cls,
        context: bpy.types.Context,
        build_context: BuildContext,
        transfer_mapping: AssetTransferMapping,
        transfer_settings: bpy.types.PropertyGroup,
    ) -> None:
        pass
```

- **context**: Regular bpy.context

- **build_context**: Is an instance of type `asset_pipeline.builder.context.BuildContext`. It contains all information that the Asset Builder needs to process the transfer. You can for example query the selected TaskLayers with `build_context.asset_context.task_layer_assembly.get_used_task_layers()`. Or find out if the current operation was a `push` or a `pull` with `build_context.is_push`.

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
You can also access the root Asset source and Target Collection:
```
transfer_mapping.source_coll: bpy.types.Collection
transfer_mapping.target_coll: bpy.types.Collection
```

Further than that you can access to objects which had no match.
```
transfer_mapping.no_match_target_objs: Set[bpy.types.Object] (all Objects that exist in target but not in source)
transfer_mapping.no_match_source_objs: Set[bpy.types.Object] (vice versa)
```
- **transfer_settings**: Is the `TransferSettings` PropertyGroup that was defined in the task_layer.py module. More to that in the next section. If the PropertyGroup was defined you can just query its values as you would regularly do it inside of Blender: `transfer_settings.my_value`

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



## Getting Started as a Developer

The asset-pipeline contains two main packages.

1. **builder**: The Asset Builder which contains most of the core definitions and logic of Task Layers, Asset publishing, pulling, the import process for that and metadata handling.

2. **updater**: The Asset Updater is quite light weight. It handles detecting imported asset collections and fetching available asset publishes. It also handles the logic of the actual updating.

Both packages share a couple of modules that you can find on the top level.

Let's have a closer look at the **builder** package.

The Pipeline of **publishing** an Asset looks roughly like the following:

- Loading a .blend file
- Creating a Production Context
- Creating an Asset Context
- Selecting TaskLayers to publish
- Start publish: Create Build Context
- Fetch all asset publishes and their metadata
- Apply changes: Pushes the selected TaskLayer to the affected asset publishes, updates metadata (In separate Blender instances)
- Publish: Finalizes the publish process, commits changes to svn.

The Pipeline of **pulling** TaskLayers from the latest asset publish goes down roughly like this:
- Loading a .blend file
- Creating a Production Context
- Creating an Asset Context
- Creating Build Context
- Selecting TaskLayers to pull
- Pull: Pulls the selected TaskLayers from the latest Asset Publish in to the current Asset Task and updates metadata.

---

### Context

The asset-pipeline strongly works with Context objects, that get populated with
information and are used by the AssetBuilder to perform the actual logic of
building an Asset.

There are 3 types of contexts:

- **ProductionContext**: Global production level context, gets loaded on startup,
processes all the config files. This context collects all the TaskLayers and
registers TransferSettings that are defined in the `task_layers.py` config file.
It also searches for the `hooks.py` file and collects all valid hooks.

- **AssetContext**: Local Asset Context, gets loaded on each scene load. Stores
settings and information for active Asset. It holds all information that are
related to the current Asset. This includes the current Asset Collection, Asset
Task, available Asset Publishes, the Asset Directory, the configuration of Task
Layers (which ones are enabled and disabled) and the Transfer Settings values.

- **BuildContext**: Gets loaded when starting a publish or a pull. Contains both the
ProductionContext and AssetContext as well as some other data. Is the actual
context that gets processed by the AssetBuilder.

A key feature is that we need to be able to 'exchange' this information with
another blend file. As the 'push' or publish process requires to:

Open another blend file -> load the build context there -> process it -> close it again.

This can be achieved by using the
[pickle](https://docs.python.org/3/library/pickle.html) library and pickle the
Contexts. All the contexts are pickle-able. The **\_\_setstate\_\_**,
**\_\_getstate\_\_** functions ensure that.


### UI

All of this information that hides in these Context Objects needs to be partially visible for
Users in the UI. In the `props.py` module there are a whole lot of PropertyGroups that can store this
information with native Blender Properties to display it in the UI.

This requires some sort of sync process between the Context and the PropertyGroups.
This sync process happens in a couple of places:

- On startup
- On scene load
- On start publish
- After push task layers
- After abort publish
- After pull task layers
- After publish
- After updating statuses (metadata)

Which PropertyGroups get updated depends a little bit on the operations. In general the asset-pipeline
only tries to update the parts that were altered and are therefore outdated.

Not only are PropertyGroups updated by the Context objects, sometimes it also goes the other way.
For example: The last selected TaskLayers are saved on Scene level. On load this selection is restored,
which also updates the AssetContext.

### Asset Collection

Per task file there is only **one** Asset Collection. The Asset Collection and all its children and
dependencies is the final data that is being worked with in the Asset Builder.

An Asset Collection needs to be initialized which fills out a whole lot of properties that get fetched from Kitsu.

The properties are saved on the Collection at:

`collection.bsp_asset`

as a PropertyGroup. Some properties you can access via Python Scripts are:

```
entity_parent_id: bpy.props.StringProperty(name="Asset Type ID")
entity_parent_name: bpy.props.StringProperty(name="Asset Type")
entity_name: bpy.props.StringProperty(name="Asset Name")
entity_id: bpy.props.StringProperty(name="Asset ID")
project_id: bpy.props.StringProperty(name="Project ID")
is_publish: bpy.props.BoolProperty(
    name="Is Publish",
    description="Controls if this Collection is an Asset Publish to distinguish it from a 'working' Collection",
)
version: bpy.props.StringProperty(name="Asset Version")
publish_path: bpy.props.StringProperty(name="Asset Publish")
rig: bpy.props.PointerProperty(type=bpy.types.Armature, name="Rig")
```

### Asset Files

Often we have to interact with files on disk and do the same operations over and
over again.  For this consider using the: **asset_file.py** module. It contains
the **AssetTask**, **AssetPublish** and
**AssetDir** classes that are very useful and an important part of the System.

In fact every interaction with asset files happens via these classes as they automatically load
metadata, which is in integral part of the pipeline.


### Metadata

An asset file is always paired with a metadata file. The metadata file contains various information
about that particular asset file. It saves all the TaskLayers that are contained in this file and where
they came from. It also holds all kinds of information that make the Asset clearly identifiable.

The AssetFile Classes automatically load this metadata on creation.

The file format of this metadata is `xmp`. For that the asset-pipeline uses the `xml.etree` library.
In the `metadata.py` file are Schemas that represent the different Metadata blocks.

The idea here is to have Schemas in the form of Python `dataclasses` that can be converted to their equivalent as XML Element. That way we have a clear definition of what kind of field are expected and available.
Schemas can have nested Data Classes. The conversion from Data Class to XML Element happens in the `ElementMetadata` class and is automated.
Metadata Classes can also be generated from ElementClasses. This conversion is happening in the `from_element()` function.

The code base should only work with Data Classes as they are much easier to handle.
That means it is forbidden to import `Element[]` classes from `metadata.py`.
The conversion from and to Data Classes is only handled in this module.

That results in this logic:
A: Saving Metadata to file:
   -> MetadataClass -> ElementClass -> XML File on Disk
B: Loading Metadata from file:
   -> XML File on Disk -> ElementClass -> MetadataClass

### Asset Importer

The `AssetImporter` is responsible for importing the right collections from the right source file
so the data transfer can happen as expected.
The output is a `TransferCollectionTriplet` which holds a reference to the collection from the AssetTask, collection from the AssetPublish and the actual target Collection on which the data is transferred.

The target Collection is either a duplicate of the the AssetTask Collection or the AssetPublish Collection.
Which it is depends on a number of factors. Is it pull or a push and which Task Layers are selected. The exact logic is described in the [configuration](#configuration) section.

The important takeaway here is that during a transfer we always have these 3 Collections present and each TaskLayer is either transferred from the AssetTask or the AssetPublish Collection to the Target.

The logic of figuring out what needs to be target is happening in the AssetImporter. To avoid naming collisions the AssetImporter uses a suffix system. Each of the collections, all their children (including materials and node trees) receive a suffix during import.

### Asset Mapping

To transfer data we need a source and a target. Users can describe what should happen during this transfer for each Task Layer in the:

```
@classmethod
def transfer_data(
    cls,
    context: bpy.types.Context,
    build_context: BuildContext,
    transfer_mapping: AssetTransferMapping,
    transfer_settings: bpy.types.PropertyGroup,
) -> None:
```

method. Users can have access to this `source` and `target` via the `transfer_mapping`. The TransferMapping is a class that has a couple of properties, which hold dictionaries.

In these dictionaries the key is the source and the value the target.
Both key and target are actual Blender ID Datablocks.
This makes it easy to write Merge Instructions.
With it you can do access things like:

```
transfer_mapping.object_map: Dict[bpy.types.Object, bpy.types.Object]
transfer_mapping.collection_map: Dict[bpy.types.Collection, bpy.types.Collection]
transfer_mapping.material_map: Dict[bpy.types.Material, bpy.types.Material]
```

This TransferMapping is created in the AssetBuilder in the `pull_from_task` and `pull_from_publish` functions. We always create **2** mappings:

- asset_task -> target
- asset_publish -> target

And when we finally loop through all the TaskLayers we decide for each TaskLayer which mapping to use (which will decide if we either transfer from the AssetTask Collection to the target Collection or AssetPublish Collection to target Collection).
And that is the mapping we pass to `TaskLayer.transfer_data()`.

> **_NOTE:_** If Users are adjusting the Mapping in a `transfer_data()` function they have to be aware that they are working with **2** mappings.

### Asset Builder

The AssetBuilder class contains the actual logic that can process the BuildContext.

That means that this ist the final place where we call the AssetImporter to import all the Collections and create the TransferCollectionTriplet. We also create the AssetTransferMappings here, we make sure that all objects are visible, we load the metadata, we loop through all the TaskLayers and call their `transfer_data()` functions and finally update the metadata.


The Asset Builder contains 3 functions:

- `push`
- `pull_from_publish`
- `pull_from_task`

You might wonder why we have one push function and two pulls?
This is because the push process requires us to start another Blender Instance that opens a .blend file. This Blender Instance then actually performs a pull, a `pull_from_task`.

The `push` function prepares everything so the `pull_from_task` can be called in the new Blender Instance.
It  does a couple of things:

- pickles the `BuildContext` to disk
- starts a new Blender Instance with a Python script as `-P` argument

(It does this for all the affected publishes)

This Python script is inside of the repository: `asset_pipeline/builder/scripts/push.py`

The scripts basically just restores the BuildContext and calls the `pull_from_task` function.


### Asset Updater

The Asset Updater is very light weight compared to the Asset Builder.

The main process how the Asset Updater collects its data goes like this:

1. Scanning Scene for found Assets
2. For each Asset check the Asset Publish Directory for all versions (Ignore Assets Publishes in Review State)

The most trickiest part here is to save this information nicely in native Blender Properties. Checkout the `props.py` module if you want to have a look.

The update process itself is very straightforward:
Calling the `bpy.ops.wm.lib_relocate()` operator.



