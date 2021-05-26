from typing import Tuple

import bpy

from blender_kitsu import bkglobals
from blender_kitsu.types import Sequence, Project, Shot
from blender_kitsu.logger import LoggerFactory

logger = LoggerFactory.getLogger(name=__name__)


def shot_meta(strip: bpy.types.Sequence, shot: Shot) -> None:

    # update shot info
    shot.name = strip.kitsu.shot_name
    shot.description = strip.kitsu.shot_description
    shot.data["frame_in"] = strip.frame_final_start
    shot.data["frame_out"] = strip.frame_final_end
    shot.nb_frames = strip.frame_final_duration
    shot.data["fps"] = bkglobals.FPS

    # if user changed the seqeunce the shot belongs to
    # (can only be done by operator not by hand)
    if strip.kitsu.sequence_id != shot.sequence_id:
        zseq = Sequence.by_id(strip.kitsu.sequence_id)
        shot.sequence_id = zseq.id
        shot.parent_id = zseq.id
        shot.sequence_name = zseq.name

    # update on server
    shot.update()
    logger.info("Pushed meta to shot: %s from strip: %s", shot.name, strip.name)


def new_shot(
    strip: bpy.types.Sequence,
    sequence: Sequence,
    project: Project,
) -> Shot:

    frame_range = (strip.frame_final_start, strip.frame_final_end)
    shot = project.create_shot(
        sequence,
        strip.kitsu.shot_name,
        nb_frames=strip.frame_final_duration,
        frame_in=frame_range[0],
        frame_out=frame_range[1],
        data={"fps": bkglobals.FPS},
    )
    # update description, no option to pass that on create
    if strip.kitsu.shot_description:
        shot.description = strip.kitsu.shot_description
        shot.update()

    # set project name locally, will be available on next pull
    shot.project_name = project.name
    logger.info("Pushed create shot: %s for project: %s", shot.name, project.name)
    return shot


def new_sequence(strip: bpy.types.Sequence, project: Project) -> Sequence:
    sequence = project.create_sequence(
        strip.kitsu.sequence_name,
    )
    logger.info(
        "Pushed create sequence: %s for project: %s", sequence.name, project.name
    )
    return sequence


def delete_shot(strip: bpy.types.Sequence, shot: Shot) -> str:
    result = shot.remove()
    logger.info(
        "Pushed delete shot: %s for project: %s",
        shot.name,
        shot.project_name or "Unknown",
    )
    strip.kitsu.clear()
    return result


def _remap_frame_range(frame_in: int, frame_out: int) -> Tuple[int, int]:
    start_frame = bkglobals.FRAME_START
    nb_of_frames = frame_out - frame_in
    return (start_frame, start_frame + nb_of_frames)
