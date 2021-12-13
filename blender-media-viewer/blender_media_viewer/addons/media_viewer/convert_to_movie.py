# ***** BEGIN GPL LICENSE BLOCK *****
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
# ***** END GPL LICENCE BLOCK *****
#
# (c) 2021, Blender Foundation

import sys
import re
from pathlib import Path
import bpy
from typing import List, Union, Any, Dict, Optional

PATTERN_FRAME_COUNTER = r"\d+$"


def get_frame_counter(filepath: Path) -> Optional[str]:
    # Match for frame counter
    match = re.search(PATTERN_FRAME_COUNTER, filepath.stem)

    # If input filepath has no counter
    if not match:
        return None

    return match.group(0)


def get_image_sequence(filepath: Path) -> List[Path]:
    """
    Returns list of filepath objects. If input filepath is part
    of an image sequence it will return all found items of sequence.
    If filepath is not part of sequence it will just return it
    as a single item list.
    """
    # Matches continuos number sequence end of string.
    # Which follows format for most frame counters.

    # Match for frame counter
    frame_counter = get_frame_counter(filepath)

    # If input filepath has no counter
    # return list with only input item.
    if not frame_counter:
        return [filepath]

    filename_no_counter = filepath.stem.replace(frame_counter, "")
    files: List[Path] = []

    for item in filepath.parent.iterdir():

        # Continue if directory.
        if not item.is_file():
            continue

        # Continue if different suffix.
        if item.suffix != filepath.suffix:
            continue

        # Continue if file has no counter.
        frame_counter = get_frame_counter(item)
        if not frame_counter:
            continue

        # If filename is same as filename_no_counter it
        # is part of a the same sequence.
        if item.stem.replace(frame_counter, "") == filename_no_counter:
            files.append(item)

    # Sort files list.
    files.sort(key=lambda file: file.name)

    return files


# Get cli input.
argv = sys.argv
# print(argv)
argv = argv[argv.index("--") + 1 :]

try:
    argv[0]
except IndexError:
    print("ERROR: Supply input path as first argument after '--'.")
    sys.exit(1)

try:
    argv[1]
except IndexError:
    print("ERROR: Supply output path as first argument after '--'.")
    sys.exit(1)

input_path = Path(argv[0])
output_path = Path(argv[1])
filepath_list = get_image_sequence(input_path)
start_frame = 1

# Load image sequence in Sequence Editor.
# Create new image strip.
strip = bpy.context.scene.sequence_editor.sequences.new_image(
    filepath_list[0].parent.name,
    filepath_list[0].as_posix(),
    1,
    start_frame,
)

# Extend strip elements with all the available frames.
for f in filepath_list[1:]:
    strip.elements.append(f.name)

# Set frame range.
bpy.context.scene.frame_start = start_frame
bpy.context.scene.frame_end = strip.frame_final_end

# Set render settings.
bpy.context.scene.render.filepath = output_path.as_posix()
bpy.context.scene.render.image_settings.file_format = "FFMPEG"
bpy.context.scene.render.image_settings.color_mode = "RGB"
bpy.context.scene.render.ffmpeg.format = "MPEG4"
bpy.context.scene.render.ffmpeg.codec = "H264"
bpy.context.scene.render.ffmpeg.constant_rate_factor = "HIGH"
bpy.context.scene.render.ffmpeg.ffmpeg_preset = "GOOD"

print(
    f"Exporting movie ({bpy.context.scene.frame_start}-{bpy.context.scene.frame_end}) to: {output_path.as_posix()}"
)
bpy.ops.render.render(animation=True)
