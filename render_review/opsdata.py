from typing import Set, Union, Optional, List, Dict, Any, Tuple
import json
from pathlib import Path

import bpy

from render_review import vars, prefs, checksqe
from render_review.log import LoggerFactory
from render_review.exception import NoImageSequenceAvailableException

logger = LoggerFactory.getLogger(name=__name__)


def get_frame_storage_path(strip: bpy.types.ImageSequence) -> Path:
    # fs > frame_storage | fo > farm_output
    addon_prefs = prefs.addon_prefs_get(bpy.context)
    fo_dir = Path(strip.directory)
    fs_dir_name = get_shot_dot_task_type(fo_dir)
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
    # 110_0150_A.lighting-2021-04-09_134706 -> 110_0150_A.lighting
    edit_storage_dir_name = get_shot_dot_task_type(fo_dir)

    edit_storage_dir = (
        addon_prefs.edit_storage_path
        / fo_dir.parent.relative_to(fo_dir.parents[3])
        / edit_storage_dir_name
    )

    return edit_storage_dir


def get_shot_dot_task_type(path: Path):
    return path.name.split("-")[0]


def get_farm_output_mp4_path(strip: bpy.types.ImageSequence) -> Path:
    render_dir = Path(bpy.path.abspath(strip.directory))
    shot_name = render_dir.parent.name

    # 070_0040_A.lighting-101-136.mp4 #farm always does .lighting not .comp
    # because flamenco writes in and out frame in filename we need check the first and
    # last frame in the folder
    preview_seq = get_best_preview_sequence(render_dir)

    mp4_filename = f"{shot_name}.lighting-{int(preview_seq[0].stem)}-{int(preview_seq[-1].stem)}.mp4"

    return render_dir / mp4_filename


def get_best_preview_sequence(dir: Path) -> List[Path]:

    files: List[List[Path]] = gather_files_by_suffix(
        dir, output=dict, search_suffixes=[".jpg", ".png"]
    )
    if not files:
        raise NoImageSequenceAvailableException(
            f"No peview files found in: {dir.as_posix()}"
        )

    # select the right images sequence
    if len(files) == 1:
        # if only one image sequence available take that
        preview_seq = files[list(files.keys())[0]]

    # both jpg and png available
    else:
        # if same amount of frames take png
        if len(files[".jpg"]) == len(files[".png"]):
            preview_seq = files[".png"]
        else:
            # if not take whichever is longest
            preview_seq = [files[".jpg"], files[".png"]].sort(key=lambda x: len(x))[-1]

    return preview_seq


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


def gen_frames_found_text(
    dir: Path, search_suffixes: List[str] = [".jpg", ".png", ".exr"]
) -> str:
    files_dict = gather_files_by_suffix(
        dir, output=dict, search_suffixes=search_suffixes
    )

    frames_found_text = ""  # frames found text will be used in ui
    for suffix, file_list in files_dict.items():
        frames_found_text += f" | {suffix}: {len(file_list)}"

    # replace first occurence, we dont want that at the beginning
    frames_found_text = frames_found_text.replace(
        " | ",
        "",
        1,
    )
    return frames_found_text


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


def get_sqe_editor(context: bpy.types.Context) -> Optional[bpy.types.Area]:
    sqe_editor = None

    for area in context.screen.areas:
        if area.type == "SEQUENCE_EDITOR":
            sqe_editor = area

    return sqe_editor


def fit_frame_range_to_strips(
    context: bpy.types.Context, strips: Optional[List[bpy.types.Sequence]] = None
) -> Tuple[int, int]:
    def get_sort_tuple(strip: bpy.types.Sequence) -> Tuple[int, int]:
        return (strip.frame_final_start, strip.frame_final_duration)

    if not strips:
        strips = context.scene.sequence_editor.sequences_all

    if not strips:
        return (0, 0)

    strips = list(strips)
    strips.sort(key=get_sort_tuple)

    context.scene.frame_start = strips[0].frame_final_start
    context.scene.frame_end = strips[-1].frame_final_end

    return (context.scene.frame_start, context.scene.frame_end)


def get_top_level_strips_continious(
    context: bpy.types.Context,
) -> List[bpy.types.Sequence]:

    sequences_tmp = list(context.scene.sequence_editor.sequences_all)
    sequences_tmp.sort(key=lambda s: (s.channel, s.frame_final_start), reverse=True)
    sequences: List[bpy.types.Sequence] = []

    for strip in sequences_tmp:
        if strip.type not in ["IMAGE", "MOVIE"]:
            continue

        if strip.mute == True:
            continue

        occ_ranges = checksqe.get_occupied_ranges_for_strips(sequences)
        s_range = range(strip.frame_final_start, strip.frame_final_end + 1)
        if not checksqe.is_range_occupied(s_range, occ_ranges):
            print(f"Range {str(s_range)} not in occ_ranges: {str(occ_ranges)}")
            sequences.append(strip)

    return sequences
