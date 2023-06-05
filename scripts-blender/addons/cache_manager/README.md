# Cache Manager
cache-Manager is a Blender Add-on to streamline the alembic cache workflow of assets.

## Table of Contents

- [Installation](#installation)
- [How to Get Started](#how-to-get-started)
- [Features](#features)

## Disclaimer
This addon is not used in the production of the Blender-Studio anymore and is not maintained actively.
## Installation
1. Download [latest release](../addons/overview) 
2. Launch Blender, navigate to `Edit > Preferences` select `Addons` and then `Install`, 
3. Navigate to the downloaded add-on and select `Install Add-on` 

## How to get started
After installing the addon you need to setup the addon preferences.

**Root Cache Directory**: Root directory in which the caches will be exported. Will create subfolders during export

## Features
The goal of this add-on was:

- Automate export of Alembic caches on a collection basis by tagging them as a "cache collection"
- Export of a cacheconfig.json that holds metadata and contains animation values of properties that are not supported by Blender's implementation of Alembic.
- Automate import of the Alembic cache on top of existing assets by using the Mesh Sequence Cache Modifier and Transform Cache Constraint
- Being able to process the cacheconfig.json
    - Link in all assets from their source file based on metadata in the cacheconfig.json
    - Applying additional animation which is stored in the cacheconfig.json



You can control if modifiers should be disabled / enabled during import /export:
- enable disable modifiers for cache with suffix in modifier name
    - modifier_name.cacheoff -> modifier off for export on  for import
    - modifier_name.cacheon  -> modifier on  for export off for import

