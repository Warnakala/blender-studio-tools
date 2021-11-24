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
# (c) 2021, Blender Foundation - Paul Golter

import re
import json
from pathlib import Path
from typing import Tuple, Any, List, Union, Dict, Optional
from collections import OrderedDict

import bpy

from media_viewer import vars
from media_viewer.log import LoggerFactory

# MEDIA VIEWER


logger = LoggerFactory.getLogger(name=__name__)


def is_movie(filepath: Path) -> bool:
    if filepath.suffix.lower() in vars.EXT_MOVIE:
        return True
    return False


def is_image(filepath: Path) -> bool:
    if filepath.suffix.lower() in vars.EXT_IMG:
        return True
    return False


def is_text(filepath: Path) -> bool:
    if filepath.suffix.lower() in vars.EXT_TEXT:
        return True
    return False


def is_script(filepath: Path) -> bool:
    if filepath.suffix.lower() in vars.EXT_SCRIPT:
        return True
    return False


def del_all_sequences(context: bpy.types.Context) -> None:
    for seq_name in [s.name for s in context.scene.sequence_editor.sequences_all]:
        context.scene.sequence_editor.sequences.remove(
            context.scene.sequence_editor.sequences[seq_name]
        )


def del_all_images() -> None:
    for image_name in [i.name for i in bpy.data.images]:
        bpy.data.images.remove(bpy.data.images[image_name])


def del_all_texts() -> None:
    for name in [i.name for i in bpy.data.texts]:
        bpy.data.texts.remove(bpy.data.texts[name])


def fit_frame_range_to_strips(
    context: bpy.types.Context,
) -> Tuple[int, int]:
    """
    Fits frame range of active scene to exactly encapsulate all strips in the Sequence Editor.
    """

    def get_sort_tuple(strip: bpy.types.Sequence) -> Tuple[int, int]:
        return (strip.frame_final_start, strip.frame_final_duration)

    strips = context.scene.sequence_editor.sequences_all

    if not strips:
        context.scene.frame_start = 0
        context.scene.frame_end = 0
        return (0, 0)

    strips = list(strips)
    strips.sort(key=get_sort_tuple)

    context.scene.frame_start = strips[0].frame_final_start
    context.scene.frame_end = strips[-1].frame_final_end - 1

    return (context.scene.frame_start, context.scene.frame_end)


def find_area(context: bpy.types.Context, area_name: str) -> Optional[bpy.types.Area]:
    if isinstance(context, dict):
        # Handle override context.
        screen = context["screen"]
    else:
        screen = context.screen

    for area in screen.areas:
        if area.type == area_name:
            return area
    return None


def fit_timeline_view(context: bpy.types.Context, area: bpy.types.Area = None) -> None:
    if not area:
        area = find_area(context, "DOPESHEET_EDITOR")
        if not area:
            return

    ctx = get_context_for_area(area)
    bpy.ops.action.view_all(ctx)


def fit_image_editor_view(
    context: bpy.types.Context, area: bpy.types.Area = None
) -> None:
    if not area:
        area = find_area(context, "IMAGE_EDITOR")
        if not area:
            return

    ctx = get_context_for_area(area)
    bpy.ops.image.view_all(ctx, fit_view=True)


def fit_sqe_preview(context: bpy.types.Context, area: bpy.types.Area = None) -> None:
    if not area:
        area = find_area(context, "SEQUENCE_EDITOR")
        if not area:
            return

    ctx = get_context_for_area(area)
    bpy.ops.sequencer.view_all_preview(ctx)


def fit_view(context: bpy.types.Context, area: bpy.types.Area) -> None:
    if area.type == "SEQUENCE_EDITOR":
        fit_sqe_preview(context, area=area)
    elif area.type == "IMAGE_EDITOR":
        fit_image_editor_view(context, area=area)
    elif area.type == "DOPESHEET_EDITOR":
        fit_timeline_view(context, area=area)


def get_context_for_area(area: bpy.types.Area, region_type="WINDOW") -> Dict:
    for region in area.regions:
        if region.type == region_type:
            ctx = {}

            # In weird cases, e.G mouse over toolbar of filebrowser,
            # bpy.context.copy is None. Check for that.
            if bpy.context.copy:
                ctx = bpy.context.copy()

            ctx["area"] = area
            ctx["region"] = region
            ctx["screen"] = area.id_data
            return ctx
    return {}


def split_area(
    context: bpy.types.Context,
    area_split: bpy.types.Area,
    area_type_new: str,
    direction: str,
    factor: float,
) -> bpy.types.Area:

    if isinstance(context, dict):
        # Handle override context.
        screen = context["screen"]
        ctx = context
    else:
        screen = context.screen
        ctx = get_context_for_area(area_split)

    start_areas = screen.areas[:]
    bpy.ops.screen.area_split(ctx, direction=direction, factor=factor)

    for area in screen.areas:
        if area not in start_areas:
            area.type = area_type_new.upper()
            return area


def close_area(area: bpy.types.Area) -> None:
    ctx = get_context_for_area(area)
    bpy.ops.screen.area_close(ctx)


def setup_filebrowser_area(filebrowser_area: bpy.types.Area) -> None:
    params = filebrowser_area.spaces.active.params
    params.display_type = "THUMBNAIL"
    params.display_size = "NORMAL"
    params.use_filter = True
    params.use_filter_image = True
    params.use_filter_folder = True
    params.use_filter_movie = True
    params.use_filter_text = True
    params.use_filter_script = True
    return


def load_json(path: Path) -> Any:
    with open(path.as_posix(), "r") as file:
        obj = json.load(file)
    return obj


def save_to_json(obj: Any, path: Path) -> None:
    with open(path.as_posix(), "w") as file:
        json.dump(obj, file, indent=4)


def set_filebrowser_dir(filebrowser_area: bpy.types.Area, path: Path) -> None:
    params = filebrowser_area.spaces.active.params
    params.directory = bytes(path.as_posix(), "utf-8")
    logger.info(f"Loaded recent directory: {path.as_posix()}")
    return


def load_filebrowser_dir_from_config_file(filebrowser_area: bpy.types.Area) -> None:
    path = vars.get_config_file()

    if not path.exists():
        return

    json_obj = load_json(path)

    if not "recent_dir" in json_obj:
        return

    if not json_obj["recent_dir"]:
        return

    path = Path(json_obj["recent_dir"])

    if not path.exists():
        return

    set_filebrowser_dir(filebrowser_area, path)


def ensure_config_file() -> None:
    path = vars.get_config_file()
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        save_to_json({}, path)
        logger.info(f"Created config file: {path.as_posix()}")


def get_last_strip_frame(context: bpy.types.Context) -> int:
    """
    Checks all strips in the Sequence Editor and returns the
    last frame from the most right strip.
    If there are not strips it will return the start frame of the scene
    as this function is used to place a strip at a specific point in time.
    """
    sequences = list(context.scene.sequence_editor.sequences_all)
    if not sequences:
        return context.scene.frame_start
    sequences.sort(key=lambda s: s.frame_final_end)
    return sequences[-1].frame_final_end


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


def get_frame_counter(filepath: Path) -> Optional[str]:
    # Match for frame counter
    match = re.search(vars.PATTERN_FRAME_COUNTER, filepath.stem)

    # If input filepath has no counter
    if not match:
        return None

    return match.group(0)


def get_movie_strips(
    context: bpy.types.Context,
) -> List[bpy.types.Sequence]:
    strips = [
        s for s in context.scene.sequence_editor.sequences_all if s.type == "MOVIE"
    ]
    strips.sort(key=lambda s: (s.frame_final_start, s.channel))
    return strips


def get_loaded_movie_sound_strip_paths(context: bpy.types.Context) -> List[Path]:
    filepath_list = []
    for strip in context.scene.sequence_editor.sequences_all:
        if strip.type == "MOVIE":
            filepath_list.append(Path(bpy.path.abspath(strip.filepath)))
        elif strip.type == "SOUND":
            filepath_list.append(Path(bpy.path.abspath(strip.sound.filepath)))
        else:
            continue

    return filepath_list


def add_to_folder_history(
    ordered_dict: OrderedDict, key: str, value: Any
) -> OrderedDict:
    if not value:
        return
    # If dictionary exceeds length of FOLDER_HISTORY_STEPS make sure to pop first item.
    if len(ordered_dict) == vars.FOLDER_HISTORY_STEPS:
        ordered_dict.popitem(last=False)

    # If key is already in dict, make sure to pop it first
    # So it gets appended at the end.
    if key in ordered_dict:
        ordered_dict.pop(key)

    ordered_dict[key] = value
    return ordered_dict


def update_gp_object_with_filepath(
    gp_obj: bpy.types.GreasePencil, filepath: Path
) -> None:
    """
    Takes input greace pencil object and adds a new layer named after filepath if not existent.
    Sets filepath layer as active and hides all other layers.
    """
    try:
        gp_obj.layers[filepath.as_posix()]

    except KeyError:
        # Create new layer with filename.
        gp_obj.layers.new(filepath.as_posix(), set_active=True)

    # Get index of existing layer and set as active.
    gp_index = gp_obj.layers.find(filepath.as_posix())
    gp_obj.layers.active_index = gp_index
    gp_obj.layers[gp_index].annotation_hide = False

    # Hide all other layers.
    for idx in range(len(gp_obj.layers)):
        if idx == gp_index:
            continue
        gp_obj.layers[idx].annotation_hide = True
