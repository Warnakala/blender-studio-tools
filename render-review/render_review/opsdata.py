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

import json
import shutil
from pathlib import Path
from typing import Set, Union, Optional, List, Dict, Any, Tuple

import bpy

from render_review import vars, prefs, checksqe, prefs
from render_review.log import LoggerFactory
from render_review.exception import NoImageSequenceAvailableException

logger = LoggerFactory.getLogger(name=__name__)

copytree_list: List[Path] = []
copytree_num_of_items: int = 0


def copytree_verbose(src: Union[str, Path], dest: Union[str, Path], **kwargs):
    _copytree_init_progress_update(Path(src))
    shutil.copytree(src, dest, copy_function=_copy2_tree_progress, **kwargs)
    _copytree_clear_progress_update()


def _copytree_init_progress_update(source_dir: Path):
    global copytree_num_of_items
    file_list = [f for f in source_dir.glob("**/*") if f.is_file()]
    copytree_num_of_items = len(file_list)


def _copy2_tree_progress(src, dst):
    """
    Function that can be used for copy_function
    argument on shutil.copytree function.
    Logs every item that is currently copied.
    """
    global copytree_num_of_items
    global copytree_list

    copytree_list.append(Path(src))
    progress = round((len(copytree_list) * 100) / copytree_num_of_items)
    logger.info("Copying %s (%i%%)", src, progress)
    shutil.copy2(src, dst)


def _copytree_clear_progress_update():
    global copytree_num_of_items

    copytree_num_of_items = 0
    copytree_list.clear()


def get_valid_cs_sequences(
    context: bpy.types.Context, sequence_list: List[bpy.types.Sequence] = []
) -> List[bpy.types.Sequence]:

    sequences: List[bpy.types.Sequence] = []

    if sequence_list:
        sequences = sequence_list
    else:
        sequences = (
            context.selected_sequences or context.scene.sequence_editor.sequences_all
        )

    if prefs.is_blender_kitsu_enabled():

        valid_sequences = [
            s
            for s in sequences
            if s.type in ["MOVIE", "IMAGE"] and not s.mute and not s.kitsu.initialized
        ]
    else:
        valid_sequences = [
            s for s in sequences if s.type in ["MOVIE", "IMAGE"] and not s.mute
        ]

    return valid_sequences


def get_shot_frames_dir(strip: bpy.types.ImageSequence) -> Path:
    # sf = shot_frames | fo = farm_output.
    addon_prefs = prefs.addon_prefs_get(bpy.context)
    fo_dir = Path(strip.directory)
    sf_dir = (
        addon_prefs.shot_frames_dir
        / fo_dir.parent.relative_to(fo_dir.parents[3])
    )

    return sf_dir


def get_shot_previews_path(strip: bpy.types.ImageSequence) -> Path:
    # Fo > farm_output.
    addon_prefs = prefs.addon_prefs_get(bpy.context)
    fo_dir = Path(bpy.path.abspath(strip.directory))
    shot_previews_dir = (
        addon_prefs.shot_previews_path
        / fo_dir.parent.relative_to(fo_dir.parents[3])
    )

    return shot_previews_dir


def get_shot_dot_task_type(path: Path):
    return path.parent.name


def get_farm_output_mp4_path(strip: bpy.types.ImageSequence) -> Path:
    render_dir = Path(bpy.path.abspath(strip.directory))
    shot_name = render_dir.parent.name

    # 070_0040_A.lighting-101-136.mp4 #farm always does .lighting not .comp
    # because flamenco writes in and out frame in filename we need check the first and
    # last frame in the folder
    preview_seq = get_best_preview_sequence(render_dir)

    mp4_filename = f"{shot_name}-{int(preview_seq[0].stem)}-{int(preview_seq[-1].stem)}.mp4"

    return render_dir / mp4_filename


def get_best_preview_sequence(dir: Path) -> List[Path]:

    files: List[List[Path]] = gather_files_by_suffix(
        dir, output=dict, search_suffixes=[".jpg", ".png"]
    )
    if not files:
        raise NoImageSequenceAvailableException(
            f"No preview files found in: {dir.as_posix()}"
        )

    # Select the right images sequence.
    if len(files) == 1:
        # If only one image sequence available take that.
        preview_seq = files[list(files.keys())[0]]

    # Both jpg and png available.
    else:
        # If same amount of frames take png.
        if len(files[".jpg"]) == len(files[".png"]):
            preview_seq = files[".png"]
        else:
            # If not, take whichever is longest.
            preview_seq = [files[".jpg"], files[".png"]].sort(key=lambda x: len(x))[-1]

    return preview_seq


def get_shot_frames_backup_path(strip: bpy.types.ImageSequence) -> Path:
    fs_dir = get_shot_frames_dir(strip)
    return fs_dir.parent / f"_backup.{fs_dir.name}"


def get_shot_frames_metadata_path(strip: bpy.types.ImageSequence) -> Path:
    fs_dir = get_shot_frames_dir(strip)
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
        metadata_path = get_shot_frames_metadata_path(s)
        if not metadata_path.exists():
            continue
        json_obj = load_json(
            metadata_path
        )  # TODO: prevent opening same json multi times

        if Path(json_obj["source_current"]) == Path(bpy.path.abspath(s.directory)):
            s.rr.is_approved = True
            approved_strips.append(s)
            logger.info("Detected approved strip: %s", s.name)
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

    # Gather files.
    for f in dir.iterdir():
        if not f.is_file():
            continue

        for suffix in search_suffixes:
            if f.suffix == suffix:
                files.setdefault(suffix, [])
                files[suffix].append(f)

    # Sort.
    for suffix, file_list in files.items():
        files[suffix] = sorted(file_list, key=lambda f: f.name)

    # Return.
    if output == str:
        return_str = ""
        for suffix, file_list in files.items():
            return_str += f" | {suffix}: {len(file_list)}"

        # Replace first occurence, we dont want that at the beginning.
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

    # Replace first occurence, we dont want that at the beginning.
    frames_found_text = frames_found_text.replace(
        " | ",
        "",
        1,
    )
    return frames_found_text


def is_sequence_dir(dir: Path) -> bool:
    return dir.parent.name == "shots"


def is_shot_dir(dir: Path) -> bool:
    return dir.parent.parent.name == "shots"


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
    context.scene.frame_end = strips[-1].frame_final_end -1

    return (context.scene.frame_start, context.scene.frame_end)


def get_top_level_valid_strips_continious(
    context: bpy.types.Context,
) -> List[bpy.types.Sequence]:

    sequences_tmp = get_valid_cs_sequences(
        context, sequence_list=list(context.scene.sequence_editor.sequences_all)
    )

    sequences_tmp.sort(key=lambda s: (s.channel, s.frame_final_start), reverse=True)
    sequences: List[bpy.types.Sequence] = []

    for strip in sequences_tmp:

        occ_ranges = checksqe.get_occupied_ranges_for_strips(sequences)
        s_range = range(strip.frame_final_start, strip.frame_final_end + 1)

        if not checksqe.is_range_occupied(s_range, occ_ranges):
            sequences.append(strip)

    return sequences

def setup_color_management(context: bpy.types.Context) -> None:
    if context.scene.view_settings.view_transform != 'Standard':
        context.scene.view_settings.view_transform = 'Standard'
        logger.info("Set view transform to: Standard")
