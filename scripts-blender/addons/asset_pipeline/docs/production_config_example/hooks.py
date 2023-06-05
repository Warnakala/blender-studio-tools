from typing import Any, Dict, List, Set, Union, Optional
import bpy

from asset_pipeline.api import hook, Wildcard, DoNotMatch

"""
Hooks can be matched with the following parameters.
As match input you can use str, list, WildCard, DoNotMatch

Examples:
- Global Hooks (No match filter):                  @hook()
- Hooks for an asset type only:                    @hook(match_asset_type="Character")
- Hooks for a specific asset:                      @hook(match_asset: "Sprite")
- Hooks for a task layer only                      @hook(match_task_layers: ["ShadingTaskLayer", "RiggingTaskLayer"]
- Hooks for an asset and a task layer combination: @hook(macth_asset: "Sprite", match_task_layers: "ShadingTaskLayer")
Note: the decorator needs to be executed.

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

By exposing these parameters in the hook function you can use them in your code.
"""

@hook()
def test_hook_A(asset_collection: bpy.types.Collection, **kwargs) -> None:
    print("Test Hook A running!")


@hook(match_asset="Test")
def test_hook_B(**kwargs) -> None:
    print("Test Hook B running!")


@hook(
    match_asset="Generic Sprite",
    match_task_layers="ShadingTaskLayer",
)
def test_hook_sprite(asset_collection: bpy.types.Collection, **kwargs) -> None:
    print(f"Test Hook Sprite {asset_collection} is running!")
