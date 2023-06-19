# Project Description (DRAFT)

Shot Builder is an Add-on that helps studios to work with task specific
Blend-files. The shot builder is part of the shot-tools repository. The main functionalities are

* Build blend files for a specific task and shot.
* Sync data back from work files to places like kitsu, or `edit.blend`.

## Design Principles

The main design principles are:

* The core-tool can be installed as an add-on, but the (production specific)
  configuration should be part of the production repository.
* The configuration files are a collection of python files. The API between
  the configuration files and the add-on should be easy to use as pipeline
  TDs working on the production should be able to work with it.
* TDs/artists should be able to handle issues during building without looking
  at how the add-on is structured.
* The tool contains connectors that can be configured to read/write data
  from the system/file that is the main location of the data. For example
  The start and end time of a shot could be stored in an external production tracking application.

## Connectors

Connectors are components that can be used to read or write to files or
systems. The connectors will add flexibility to the add-on so it could be used
in multiple productions or studios.

In the configuration files the TD can setup the connectors that are used for
the production. Possible connectors would be:

* Connector for text based config files (json/yaml).
* Connector for kitsu (https://www.cg-wire.com/en/kitsu.html).
* Connector for blend files.

## Layering & Hooks

The configuration of the tool is layered. When building a work file for a sequence
there are multiple ways to change the configuration.

* Configuration for the production.
* Configuration for the asset that is needed.
* Configuration for the asset type of the loaded asset.
* Configuration for the sequence.
* Configuration for the shot.
* Configuration for the task type.

For any combination of these configurations hooks can be defined.

```
@shot_tools.hook(match_asset_name='Spring', match_shot_code='02_020A')
def hook_Spring_02_020A(asset: shot_tools.Asset, shot: shot_tools.Shot, **kwargs) -> None:
    """
    Specific overrides when Spring is loaded in 02_020A.
    """

@shot_tools.hook(match_task_type='anim')
def hook_task_anim(task: shot_tools.Task, shot: shot_tools.Shot, **kwargs) -> None:
    """
    Specific overrides for any animation task.
    """
```

### Data

All hooks must have Python’s `**kwargs` parameter. The `kwargs` contains
the context at the moment the hook is invoked. The context can contain the
following items.

* `production`: `shot_tools.Production`: Include the name of the production
  and the location on the filesystem.
* `task`: `shot_tools.Task`: The task (combination of task_type and shot)
* `task_type`: `shot_tools.TaskType`: Is part of the `task`.
* `sequence`: `shot_tools.Sequence`: Is part of `shot`.
* `shot`: `shot_tools.Shot` Is part of `task`.
* `asset`: `shot_tools.Asset`: Only available during asset loading phase.
* `asset_type`: `shot_tools.AssetType`: Only available during asset loading phase.

### Execution Order

The add-on will internally create a list containing the hooks that needs to be
executed for the command in a sensible order. It will then execute them in that
order.

By default the next order will be used:

* Production wide hooks
* Asset Type hooks
* Asset hooks
* Sequence hooks
* Shot hooks
* Task type hooks

A hook with a single ‘match’ rule will be run in the corresponding phase. A hook with
multiple ‘match’ rules will be run in the last matching phase. For example, a hook with
‘asset’ and ‘task type’ match rules will be run in the ‘task type’ phase.

#### Events

Order of execution can be customized by adding the optional `run_before`
or `run_after` parameters.

```
@shot_tools.hook(match_task_type='anim',
                 requires={shot_tools.events.AssetsLoaded, hook_task_other_anim},
                 is_required_by={shot_tools.events.ShotOverrides})
def hook_task_anim(task: shot_tools.Task, shot: shot_tools.Shot, **kwargs) -> None:
    """
    Specific overrides for any animation task run after all assets have been loaded.
    """
```

Events could be:

* `shot_tools.events.BuildStart`
* `shot_tools.events.ProductionSettingsLoaded`
* `shot_tools.events.AssetsLoaded`
* `shot_tools.events.AssetTypeOverrides`
* `shot_tools.events.SequenceOverrides`
* `shot_tools.events.ShotOverrides`
* `shot_tools.events.TaskTypeOverrides`
* `shot_tools.events.BuildFinished`
* `shot_tools.events.HookStart`
* `shot_tools.events.HookEnd`

During usage we should see which one of these or other events are needed.

`shot_tools.events.BuildStart`, `shot_tools.events.ProductionSettingsLoaded`
and `shot_tools.events.HookStart` can only be used in the `run_after`
parameter. `shot_tools.events.BuildFinished`, `shot_tools.events.HookFinished`
can only be used in the `run_before` parameter.


## API

The shot builder has an API between the add-on and the configuration files. This
API contains convenience functions and classes to hide complexity and makes
sure that the configuration files are easy to maintain.

```
register_task_type(task_type="anim")
register_task_type(task_type="lighting")
```

```
# shot_tool/characters.py
class Asset(shot_tool.some_module.Asset):
    asset_file = "/{asset_type}/{name}/{name}.blend"
    collection = “{class_name}”
    name = “{class_name}”

class Character(Asset):
    asset_type = ‘char’


class Ellie(Character):
    collection = “{class_name}-{variant_name}”
    variants = {‘default’, ‘short_hair’}

class Victoria(Character): pass
class Rex(Character): pass

# shot_tool/shots.py
class Shot_01_020_A(shot_tool.some_module.Shot):
    shot_id = ‘01_020_A’
    assets = {
        characters.Ellie(variant=”short_hair”),
        characters.Rex,
        sets.LogOverChasm,
    }

class AllHumansShot(shot_tool.some_module.Shot):
    assets = {
        characters.Ellie(variant=”short_hair”),
        characters.Rex,
        characters.Victoria,
    }

class Shot_01_035_A(AllHumansShot):
    assets = {
        sets.Camp,
    }

```

This API is structured/implemented in a way that it keeps track of what
is being done. This will be used when an error occurs so a descriptive
error message can be generated that would help the TD to solve the issue more
quickly. The goal would be that the error messages are descriptive enough to
direct the TD into the direction where the actual cause is. And when possible
propose several solutions to fix it.

## Setting up the tool

The artist/TD can configure their current local project directory in the add-on preferences. 
This can then be used for new blend files. The project associated with an opened (so existing)
blend file can be found automatically by iterating over parent directories until a Shot Builder
configuration file is found. Project-specific settings are not configured/stored in the add-on,
but in this configuration file.

The add-on will look in the root of the production repository to locate the
main configuration file `config/shot-builder/config.py`. This file contains general
settings about the production, including:

* The name of the production for reporting back to the user when needed.
* Naming standards to test against when reporting deviations.
* Location of other configuration (`tasks.py`, `assets.py`) relative to the `shot-builder` directory of the production.
* Configuration of the needed connectors.

## Usage

Any artist can open a shot file via the `File` menu. A modal panel appears
where the user can select the task type and sequence/shot. When the file
already exists, it will be opened. When the file doesn't exist, the file
will be built.

In the future other use cases will also be accessible, such as:

* Syncing data back from a work file to the source of the data.
* Report of errors/differences between the shot file and the configuration.

## Open Issues

### Security

* Security keys needed by connectors need to be stored somewhere. The easy
  place is to place inside the production repository, but that isn't secure
  Anyone with access to the repository could misuse the keys to access the
  connector. Other solution might be to use the OS key store or retrieve the
  keys from an online service authenticated by the blender cloud add-on.

  We could use `keyring` to access OS key stores.