import json
from pathlib import Path
from typing import Tuple, Any, List, Union, Dict, Optional

import bpy

from video_player import vars
from video_player.log import LoggerFactory

# MEDIA VIEWER


logger = LoggerFactory.getLogger(name=__name__)


def is_movie(filepath: Path) -> bool:
    if filepath.suffix in vars.EXT_MOVIE:
        return True
    return False


def is_image(filepath: Path) -> bool:
    if filepath.suffix in vars.EXT_IMG:
        return True
    return False


def is_text(filepath: Path) -> bool:
    if filepath.suffix in vars.EXT_TEXT:
        return True
    return False


def is_script(filepath: Path) -> bool:
    if filepath.suffix in vars.EXT_SCRIPT:
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
    context.scene.frame_end = strips[-1].frame_final_end

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


def fit_timeline_view(context: bpy.types.Context) -> None:
    area = find_area(context, "DOPESHEET_EDITOR")
    if not area:
        return

    ctx = get_context_for_area(area)
    bpy.ops.action.view_all(ctx)


def get_context_for_area(area: bpy.types.Area) -> Dict:
    for region in area.regions:
        if region.type == "WINDOW":
            ctx = bpy.context.copy()
            ctx["area"] = area
            ctx["region"] = region
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
    params.display_size = "TINY"
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
