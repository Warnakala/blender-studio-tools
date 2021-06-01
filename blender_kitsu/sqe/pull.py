import bpy

from blender_kitsu import bkglobals
from blender_kitsu.types import Cache, Sequence, Project, Shot
from blender_kitsu.logger import LoggerFactory

logger = LoggerFactory.getLogger(name=__name__)


def shot_meta(strip: bpy.types.Sequence, shot: Shot, clear_cache: bool = True) -> None:

    if clear_cache:
        # clear cache before pulling
        Cache.clear_all()

    # update sequence props
    seq = Sequence.by_id(shot.parent_id)
    strip.kitsu.sequence_id = seq.id
    strip.kitsu.sequence_name = seq.name

    # update shot props
    strip.kitsu.shot_id = shot.id
    strip.kitsu.shot_name = shot.name
    strip.kitsu.shot_description = shot.description if shot.description else ""

    # update project props
    project = Project.by_id(shot.project_id)
    strip.kitsu.project_id = project.id
    strip.kitsu.project_name = project.name

    # update meta props
    strip.kitsu.initialized = True
    strip.kitsu.linked = True

    # update strip name
    strip.name = shot.name

    # log
    logger.info("Pulled meta from shot: %s to strip: %s", shot.name, strip.name)


def update_strip_start_offset_from_shot(strip: bpy.types.Sequence, shot: Shot) -> None:
    if "3d_out" not in shot.data:
        logger.warning(
            "%s no update to frame_start_offset. '3d_out' key not in shot.data",
            shot.name,
        )
        return

    if not shot.data["3d_out"]:
        logger.warning(
            "%s no update to frame_start_offset. '3d_out' key invalid value: %i",
            shot.name,
            shot.data["3d_out"],
        )
        return

    start_offset = (
        bkglobals.FRAME_START
        + strip.frame_duration
        + ((strip.frame_final_end - 1) - (strip.frame_start + strip.frame_duration))
        - int(shot.data["3d_out"])
    )
    strip.kitsu.frame_start_offset = start_offset
    return None
