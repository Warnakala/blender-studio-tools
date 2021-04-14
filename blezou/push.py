from typing import Tuple

import bpy

from .types import ZSequence, ZProject, ZShot
from .logger import ZLoggerFactory

logger = ZLoggerFactory.getLogger(name=__name__)


def shot_meta(strip: bpy.types.Sequence, zshot: ZShot) -> None:

    # update shot info
    zshot.name = strip.blezou.shot_name
    zshot.description = strip.blezou.shot_description
    zshot.data["frame_in"] = strip.frame_final_start
    zshot.data["frame_out"] = strip.frame_final_end

    # update sequence info if changed
    if not zshot.sequence_name == strip.blezou.sequence_name:
        zseq = ZSequence.by_id(strip.blezou.sequence_id)
        zshot.sequence_id = zseq.id
        zshot.parent_id = zseq.id
        zshot.sequence_name = zseq.name

    # update on server
    zshot.update()
    logger.info("Pushed meta to shot: %s from strip: %s" % (zshot.name, strip.name))


def new_shot(
    strip: bpy.types.Sequence,
    zsequence: ZSequence,
    zproject: ZProject,
) -> ZShot:

    frame_range = (strip.frame_final_start, strip.frame_final_end)
    zshot = zproject.create_shot(
        strip.blezou.shot_name,
        zsequence,
        frame_in=frame_range[0],
        frame_out=frame_range[1],
    )
    # update description, no option to pass that on create
    if strip.blezou.shot_description:
        zshot.description = strip.blezou.shot_description
        zshot.update()

    # set project name locally, will be available on next pull
    zshot.project_name = zproject.name
    logger.info("Pushed create shot: %s for project: %s" % (zshot.name, zproject.name))
    return zshot


def new_sequence(strip: bpy.types.Sequence, zproject: ZProject) -> ZSequence:
    zsequence = zproject.create_sequence(
        strip.blezou.sequence_name,
    )
    logger.info(
        "Pushed create sequence: %s for project: %s" % (zsequence.name, zproject.name)
    )
    return zsequence


def delete_shot(strip: bpy.types.Sequence, zshot: ZShot) -> str:
    result = zshot.remove()
    logger.info(
        "Pushed delete shot: %s for project: %s"
        % (zshot.name, zshot.project_name if zshot.project_name else "Unknown")
    )
    strip.blezou.clear()
    return result


def _remap_frame_range(frame_in: int, frame_out: int) -> Tuple[int, int]:
    start_frame = 101
    nb_of_frames = frame_out - frame_in
    return (start_frame, start_frame + nb_of_frames)
