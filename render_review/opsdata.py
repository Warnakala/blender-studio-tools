import json
from pathlib import Path
from typing import Set, Union, Optional, List, Dict, Any

import bpy

from render_review import vars, prefs
from render_review.log import LoggerFactory

logger = LoggerFactory.getLogger(name=__name__)


def get_frame_storage_path(strip: bpy.types.ImageSequence) -> Path:
    # fs > frame_storage | fo > farm_output
    addon_prefs = prefs.addon_prefs_get(bpy.context)
    fo_dir = Path(strip.directory)
    fs_dir_name = fo_dir.parent.name + ".lighting"
    fs_dir = (
        addon_prefs.frame_storage_path
        / fo_dir.parent.relative_to(fo_dir.parents[3])
        / fs_dir_name
    )

    return fs_dir


def get_frame_storage_backup_path(strip: bpy.types.ImageSequence) -> Path:
    fs_dir = get_frame_storage_path(strip)
    return fs_dir.parent / f"_backup.{fs_dir.name}"


def get_frame_storage_metadata_path(strip: bpy.types.ImageSequence) -> Path:
    fs_dir = get_frame_storage_path(strip)
    return fs_dir.parent / "metadata.json"


def load_json(path: Path) -> Any:
    with open(path.as_posix(), "r") as file:
        obj = json.load(file)
    return obj


def save_to_json(obj: Any, path: Path) -> None:
    with open(path.as_posix(), "w") as file:
        json.dump(obj, file)
