import json
from pathlib import Path
from typing import Set, Union, Optional, List, Dict, Any

import bpy

from render_review import vars, prefs
from render_review.log import LoggerFactory
from render_review.exception import NoImageSequenceAvailableException

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


def get_edit_storage_path(strip: bpy.types.ImageSequence) -> Path:
    # fs > frame_storage | fo > farm_output
    addon_prefs = prefs.addon_prefs_get(bpy.context)
    fo_dir = Path(bpy.path.abspath(strip.directory))
    edit_storage_dir_name = fo_dir.parent.name + ".lighting"

    edit_storage_dir = (
        addon_prefs.edit_storage_path
        / fo_dir.parent.relative_to(fo_dir.parents[3])
        / edit_storage_dir_name
    )

    return edit_storage_dir


def get_farm_output_mp4_path(strip: bpy.types.ImageSequence) -> Path:
    render_dir = Path(bpy.path.abspath(strip.directory))
    shot_name = render_dir.parent.name

    # 070_0040_A.lighting-101-136.mp4
    # because flamenco writes in and out frame in filename we need check the first and
    # last frame in the folder
    files: List[List[Path]] = gather_files_by_suffix(
        render_dir, output=list, search_suffixes=[".jpg"]
    )
    if not files:
        raise NoImageSequenceAvailableException(
            f"No jpg files found in: {render_dir.as_posix()}"
        )

    mp4_filename = (
        f"{shot_name}.lighting-{int(files[0][0].stem)}-{int(files[0][-1].stem)}.mp4"
    )

    return render_dir / mp4_filename


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
        json.dump(obj, file, indent=4)


def update_is_approved(
    context: bpy.types.Context,
) -> List[bpy.types.ImageSequence]:
    sequences = [
        s
        for s in context.scene.sequence_editor.sequences_all
        if s.type == "IMAGE" and s.rr.is_render and s.directory
    ]

    approved_strips = []

    for s in sequences:
        metadata_path = get_frame_storage_metadata_path(s)
        if not metadata_path.exists():
            continue
        json_obj = load_json(
            metadata_path
        )  # TODO: prevent opening same json multi times

        if Path(json_obj["source_current"]) == Path(bpy.path.abspath(s.directory)):
            s.rr.is_approved = True
            approved_strips.append(s)
            logger.info("Detected aprooved strip: %s", s.name)
        else:
            s.rr.is_approved = False

    return approved_strips


def gather_files_by_suffix(
    dir: Path, output=str, search_suffixes: List[str] = [".jpg", ".png", ".exr"]
) -> Union[str, List, Dict]:
    """
    Gathers files in dir that end with an extension in search_suffixes.
    Supported values for output: str, list, dict
    """

    files: Dict[str, List[Path]] = {}

    # gather files
    for f in dir.iterdir():
        if not f.is_file():
            continue

        for suffix in search_suffixes:
            if f.suffix == suffix:
                files.setdefault(suffix, [])
                files[suffix].append(f)

    # sort
    for suffix, file_list in files.items():
        files[suffix] = sorted(file_list, key=lambda f: f.name)

    # return
    if output == str:
        return_str = ""
        for suffix, file_list in files.items():
            return_str += f" | {suffix}: {len(file_list)}"

        # replace first occurence, we dont want that at the beginning
        return_str = return_str.replace(" | ", "", 1)

        return return_str

    elif output == dict:
        return files

    elif output == list:
        output_list = []
        for suffix, file_list in files.items():
            output_list.append(file_list)

        return output_list
    else:
        raise ValueError(
            f"Supported output types are: str, dict, list. {str(output)} not implemented yet."
        )


def is_sequence_dir(dir: Path) -> bool:
    return dir.parent.name == "shots"


def get_shot_name_from_dir(dir: Path) -> str:
    return dir.stem  # 060_0010_A.lighting > 060_0010_A

def get_image_editor(context: bpy.types.Context) -> Optional[bpy.types.Area]:
    image_editor = None

    for area in context.screen.areas:
        if area.type == "IMAGE_EDITOR":
            image_editor = area

    return image_editor
