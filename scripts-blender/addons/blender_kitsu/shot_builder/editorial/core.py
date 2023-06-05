import bpy
import re
from pathlib import Path
from typing import Set
from blender_kitsu import prefs
from blender_kitsu import cache

def editorial_export_get_latest(context:bpy.types.Context, shot) -> list[bpy.types.Sequence]: #TODO add info to shot
        """Loads latest export from editorial department"""
        addon_prefs = prefs.addon_prefs_get(context)
        strip_channel = 1
        latest_file = editorial_export_check_latest(context)
        if not latest_file:
            return None
        # Check if Kitsu server returned empty shot
        if shot.get("id") == '':
            return None
        strip_filepath = latest_file.as_posix()
        strip_frame_start = addon_prefs.shot_builder_frame_offset

        scene = context.scene
        if not scene.sequence_editor:
            scene.sequence_editor_create()
        seq_editor = scene.sequence_editor
        movie_strip = seq_editor.sequences.new_movie(
            latest_file.name,
            strip_filepath,
            strip_channel + 1,
            strip_frame_start,
            fit_method="FIT",
        )
        sound_strip = seq_editor.sequences.new_sound(
            latest_file.name,
            strip_filepath,
            strip_channel,
            strip_frame_start,
        )
        new_strips = [movie_strip, sound_strip]
        
        # Update shift frame range prop.
        frame_in = shot["data"].get("frame_in")
        frame_3d_in = shot["data"].get("3d_in")
        frame_3d_offset = frame_3d_in - addon_prefs.shot_builder_frame_offset
        edit_export_offset = addon_prefs.edit_export_frame_offset

        # Set sequence strip start kitsu data.
        for strip in new_strips:
            strip.frame_start = -frame_in + (strip_frame_start * 2) + frame_3d_offset + edit_export_offset
        return new_strips



def editorial_export_check_latest(context: bpy.types.Context):
    """Find latest export in editorial export directory"""
    addon_prefs = prefs.addon_prefs_get(context)

    edit_export_path = Path(addon_prefs.edit_export_dir)

    files_list = [
        f
        for f in edit_export_path.iterdir()
        if f.is_file() and editorial_export_is_valid_edit_name(addon_prefs.edit_export_file_pattern, f.name)
    ]
    if len(files_list) >= 1:
        files_list = sorted(files_list, reverse=True)
        return files_list[0]
    return None


def editorial_export_is_valid_edit_name(file_pattern:str, filename: str) -> bool:
    """Verify file name matches file pattern set in preferences"""
    match = re.search(file_pattern, filename)
    if match:
        return True
    return False
