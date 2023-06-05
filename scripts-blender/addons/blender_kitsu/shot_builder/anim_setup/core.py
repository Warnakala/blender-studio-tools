import bpy
import re
from pathlib import Path
from typing import Set
from blender_kitsu import prefs
from blender_kitsu import cache


def animation_workspace_vse_area_add(context:bpy.types.Context):
    """Split smallest 3D View in current workspace"""
    for workspace in [workspace for workspace in bpy.data.workspaces if workspace.name == "Animation"]:
        context.window.workspace = workspace
        context.view_layer.update()
        areas = workspace.screens[0].areas
        view_3d_areas = sorted([area for area in areas if area.ui_type =="VIEW_3D"], key=lambda x: x.width, reverse=False)
        small_view_3d = view_3d_areas[0]    
        with context.temp_override(window=context.window, area=small_view_3d):
            bpy.ops.screen.area_split(direction='HORIZONTAL', factor=0.5)
        small_view_3d.ui_type = "SEQUENCE_EDITOR"
        small_view_3d.spaces[0].view_type = "PREVIEW"

def animation_workspace_delete_others():
    """Delete any workspace that is not an animation workspace"""
    for ws in bpy.data.workspaces:
        if ws.name != "Animation":
            bpy.ops.workspace.delete({"workspace": ws})
    


