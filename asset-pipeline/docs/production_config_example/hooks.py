from typing import Any, Dict, List, Set, Union, Optional
import bpy

from blender_studio_pipeline.asset_pipeline.builder.hook import hook
from blender_studio_pipeline.asset_pipeline.builder.hook import Wildcard, DoNotMatch

# Hooks can be matched with the following parameters.
# As match input you can use str, list, WildCard, DoNotMatch

# Examples:
# - Global Hooks (No match filter):                  @hook()
# - Hooks for an asset type only:                    @hook(match_asset_type="Character")
# - Hooks for a specific asset:                      @hook(match_asset: "Sprite")
# - Hooks for a task layer only                      @hook(match_task_layers: ["ShadingTaskLayer", "RiggingTaskLayer"]
# - Hooks for an asset and a task layer combination: @hook(macth_asset: "Sprite", match_task_layers: "ShadingTaskLayer")
# Note: the decorator needs to be executed.


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
