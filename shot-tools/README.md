# Project Description

Shot tools is an Add-on that helps studios to work with task specific 
blend-files. The main functionalities are

* Build blend files for a specific task and shot.
* Sync data back from work files to places like kitsu, or sequence.blend.

## Design Principles

The main design principles are:

* The tool can be installed as an add-on, but the (production specific) 
  configuration should be part of the production repository.
* The configuration files are a collection of python files. The API between
  the configuration files and the add-on should be very friendly as pipeline
  TD's working on the production should be able to work with it.
* TD's/artists should be able to handle issues during building without looking
  at how the add-on is structured.
* The tool contains connectors that can be configured to read/write data
  from the system/file that is the main location of the data. For example
  The start and end time of a shot could be stored in a sequence.blend or
  in an external production tracking application.

## Connectors

Connectors are components that can be used to read or write to a files or
systems. The connectors will add flexibility to the add-on so it could be used
in multiple productions or studios.

In the configuration files the TD can setup the connectors that are use for
the production. There are several connectors in the add-on:

* Connector for text based config files (json/yaml). 
* Connector for kitsu (https://www.cg-wire.com/en/kitsu.html).
* Connector for blend files.

## Layering & Hooks

The configuration of the tool is layered. When building a work file for a sequence
there are multiple ways how to change the configuration. 

* Configuration for the production.
* Configuration for the asset that is needed.
* Configuration for the asset type of the loaded asset.
* Configuration for the sequence.
* Configuration for the shot.
* Configuration for the task type.

For any combination of these configurations hooks can be defined.

```[python]
@shot_tools.hook(asset='Spring', shot='02_020A')
fn hook_Spring_02_020A(asset: shot_tools.Asset, shot: shot_tools.Shot, **kwargs):
    """
    Specific overrides when Spring is loaded in 02_020A.
    """

@shot_tools.hook(task='anim')
fn hook_task_anim(task: shot_tools.Task, shot: shot_tools.Shot, **kwargs):
    """
    Specific overrides for any animation task.
    """
```

The add-on will internally create a list containing the hooks that needs to be
executed for the command in the order what will make sense. It will then
execute them one by one.

A hook can request/use needed data by simply adding a parameter. The `**kwargs`
will contain data that cannot be mapped to a parameter.


## API

The shot tool has an API between the add-on and the configuration files. This
API contains convenience functions and classes to hide complexity and makes
sure that the configuration files are easy to maintain. 

```
register_task_type(task_type="anim")
register_task_type(task_type="lighting")
```

```
register_asset_type(asset_type="char")
```

```
register_asset(name="Spring", asset_type="char", asset_file="/chars/spring/Spring.blend")
```

This API is structured/implemented in such a way that it keeps track of what
the is being done. This will be used when an error occurs so a descriptive
error message can be generated that would help the TD to solve the issue more
quickly. The goal would be that the error messages are descriptive enough to
direct the TD into the direction where the actual cause lies.


## Setting up the tool

When enabled the artist/TD can point the add-on to a default production
repository. This is only needed when the location cannot be determined based
on the current blend-file.

The add-on will look in the root of the production repository to locate the
main configuration file `.shot-tools/config.py`. This file contains general
settings about the production, including:

* Define the name of the production for reporting back to the user when needed.
* Define naming standards to test against when reporting deviations.
* Location of other configuration (`tasks.py`, `assets.py`, `asset_types.py`)
  relative from the root of the production.
* Configuration of the connectors that are needed.

## Usage

Any artist can open a shot file via the `File` menu. A modal panel appears
where the user can select the task type and sequence/shot. When the file
already exists it will be opened. When the file doesn't exist the file
will be build.

In the future other use cases will also be accessible. Use cases like:

* Syncing data back from a work file to the source of the data.
* Report of errors/differences between the shot file and the configuration.
