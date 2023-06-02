# Lighting Overrider

System to create, manage and apply python overrides in a flexible and reliable way as they are used in the lighting process of the Blender Studio pipeline. Addon overrides specific settings of linked data.

## Table of Contents
- [Installation](#installation)
- [Features](#features)


## Installation
1. Download [latest release](../addons/overview) 
2. Launch Blender, navigate to `Edit > Preferences` select `Addons` and then `Install`, 
3. Navigate to the downloaded add-on and select `Install Add-on` 



 ## Purpose

The purpose of this addon is to manage, store and apply several python overrides that have to be imposed on linked data for rendering. The idea is not to formalize things like render settings that can be changed manually, but only settings that need to be reiterated after file load because they override library data.

Additionally to formalizing the python override process for specific use-cases in our pipeline, this addon provides the user interface to inspect, create and manage overrides of different types on the fly.

The addon however is not a necessary part of this override system, it just adds the interface between locally stored settings that are applied on file-load, regardless of whether the addon is used, and the user.

### Categories

Categories are types of settings that have to be applied in the same way and aim at simplifying how the settings are communicated by grouping them together. Categories make up the first level of access in the json file and new ones can easily be added on demand.

The exact way the categories are referred to is with their names as listed here, stylized in `snake_case`.

- **Variable Settings**
    
    Sets controls defined in the `VAR-settings` nodegroup of the `variables.blend` file.
    
- **Motion Blur Settings**
    
    Disables deformation motion blur on all objects part of specified collection (except camera objects).
    
    The collection `Master Collection` refers to the scene collection and every object that is contained in the blend data.
    
- **Shader Settings**
    
    Sets custom properties on specified objects, usually helper object following the naming convention: `HLP-<character/prop name>_settings`
    
- **Rig Settings**
    
    Sets custom properties on properties bone of specified armature objects, usually  following the naming convention: `RIG-<character/prop name>`
    
    The properties bone is assumed to be named `Properties_Character_<character/prop name>`
    
- **RNA Overrides**
    
    Sets custom overrides based on RNA path.

## Settings

The setup is based on two levels of settings:

1. **Sequence Settings**
    
    Specified in `<sequence name>.settings.json` text datablock and stored on disk within the sequence folder under the same name.
    
2. **Shot Settings**
    
    Specified and stored locally in `<shot name>.settings.json` text datablock in the shot's lighting file.
    

Upon either loading the lighting file or running the `lighting_overrider_executtion.py` script the settings are loaded and applied according to their categories. For that the sequence settings are always applied first, so that the individual shot settings have the power to override the sequence settings.

If the addon has been used to manage the settings, the JSON setting data-blocks are referenced in the UI, otherwise the defaults are assumed. By default the shot settings are stored within the file itself and the sequence settings are stored externally in the sequence folder. (Relative to the lighting file that is: `//../<sequence name>.settings.json`)

Whether the JSON data is stored as an external file or packed in the blend file is displayed with an icon:

![json icons](/media/addons/lighting_overrider/json_icon_example.png)

#### Specifiers

To identify where the settings that are to be overridden can be found they need to be listed under a specifier that specifies the name of the empty object, armature object collection, etc. where the settings should be applied. How this name is used specifically varies depending on the category and is hard-coded in nature in favour of the ease of use.

The specifier can either refer to a single item by specifying its name or it can use a suffix `:all` to affect all items whose name starts with the preceding string.

E.g.: `HLP-sprite_settings` refers only to the one sprite character whose settings object has this name, while `HLP-sprite_settings:all` refers to all sprite characters in the file. `HLP-:all` even refers to all helper objects in general.

Settings marked with the `:all` suffix are displayed with the world icon when this functionality is available for the category.
![suffixes](/media/addons/lighting_overrider/lighting_override_suffixes.png)

#### Override Picker

Based on the Override Master addon by Andy and Sybren, the Lighting Overrider addon adds the functionality to override any given property (names excluded) on the fly to the `O` hotkey.

This automatically adds an entry to the RNA overrides and is added to the settings that run on file-load.
![rna ovrrides](/media/addons/lighting_overrider/rna_override.png)


## Structure

The general structure of the settings json files has the following nested pattern:

- `Category Name`
    - `Specifier`
        - `Setting Name`: [`Setting Value`, `Setting Type`]

## Example

```json
{
    "variable_settings":{
        "day_night":[ 1.0, "FACTOR" ]
    },
    "motion_blur_settings":{
        "Master Collection":[]
    },
    "shader_settings":{
        "HLP-sprite_settings:all":{
            "hat_color":[ [ 0.14224213361740112, 0.8000000715255737, 0.08591208606958389, 1.0 ], "COLOR" ],
            "highlight_strength":[ 0.0, "VALUE" ],
            "hat_toggle":[ true, "BOOL" ]
        }
    },
    "rig_settings":{
        "RIG-:all":{
            "Quality":[ 0, "INTEGER" ]
        },
        "RIG-Sprite":{
            "Dot Seed":[ 28, "INTEGER" ]
        },
        "RIG-Sprite.001":{
            "Dot Seed":[ 9, "INTEGER" ]
        }
    },
    "rna_overrides":{
        "Dot Color":[ "bpy.data.materials[\"fungus-toadstool.cap.mat\"].node_tree.nodes[\"Mix.003\"].inputs[2].default_value", [ 1.0, 0.02594516985118389, 0.11171756684780121, 1.0 ], "COLOR" ]
    }
}
```

