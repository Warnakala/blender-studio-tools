from typing import Optional

import bpy

from . import gazu
from .types import Sequence, Project, Shot, Cache
from .logger import ZLoggerFactory

logger = ZLoggerFactory.getLogger(name=__name__)

VALID_STRIP_TYPES = {"MOVIE", "COLOR"}


def is_valid_type(strip: bpy.types.Sequence, log: bool = True) -> bool:
    if not strip.type in VALID_STRIP_TYPES:
        if log:
            logger.info("Strip: %s. Invalid type.", strip.type)
        return False
    return True


def is_initialized(strip: bpy.types.Sequence) -> bool:
    """Returns True if strip.kitsu.initialized is True else False"""
    if not strip.kitsu.initialized:
        logger.info("Strip: %s. Not initialized.", strip.name)
        return False

    logger.info("Strip: %s. Is initialized.", strip.name)
    return True


def is_linked(strip: bpy.types.Sequence, log: bool = True) -> bool:
    """Returns True if strip.kitsu.linked is True else False"""
    if not strip.kitsu.linked:
        if log:
            logger.info("Strip: %s. Not linked yet.", strip.name)
        return False
    if log:
        logger.info("Strip: %s. Is linked to ID: %s.", strip.name, strip.kitsu.shot_id)
    return True


def has_meta(strip: bpy.types.Sequence) -> bool:
    """Returns True if strip.kitsu.shot_name and strip.kitsu.sequence_name is Truethy else False"""
    seq = strip.kitsu.sequence_name
    shot = strip.kitsu.shot_name

    if not bool(seq and shot):
        logger.info("Strip: %s. Missing metadata.", strip.name)
        return False

    logger.info(
        "Strip: %s. Has metadata (Sequence: %s, Shot: %s).", strip.name, seq, shot
    )
    return True


def shot_exists_by_id(strip: bpy.types.Sequence) -> Optional[Shot]:
    """Returns Shot instance if shot with strip.kitsu.shot_id exists else None"""

    Cache.clear_all()

    try:
        shot = Shot.by_id(strip.kitsu.shot_id)
    except (gazu.exception.RouteNotFoundException, gazu.exception.ServerErrorException):
        logger.info(
            "Strip: %s No shot found on server with ID: %s",
            strip.name,
            strip.kitsu.shot_id,
        )
        return None

    logger.info(
        "Strip: %s Shot %s exists on server (ID: %s).", strip.name, shot.name, shot.id
    )
    return shot


def seq_exists_by_name(
    strip: bpy.types.Sequence, project: Project
) -> Optional[Sequence]:
    """Returns Sequence instance if strip.kitsu.sequence_name exists on server, else None"""

    Cache.clear_all()

    zseq = project.get_sequence_by_name(strip.kitsu.sequence_name)
    if not zseq:
        logger.info(
            "Strip: %s Sequence %s does not exist on server.",
            strip.name,
            strip.kitsu.sequence_name,
        )
        return None

    logger.info(
        "Strip: %s Sequence %s exists in on server (ID: %s).",
        strip.name,
        zseq.name,
        zseq.id,
    )
    return zseq


def shot_exists_by_name(
    strip: bpy.types.Sequence, project: Project, sequence: Sequence
) -> Optional[Shot]:
    """Returns Shot instance if strip.kitsu.shot_name exists on server, else None."""

    Cache.clear_all()

    shot = project.get_shot_by_name(sequence, strip.kitsu.shot_name)
    if not shot:
        logger.info(
            "Strip: %s Shot %s does not exist on server.",
            strip.name,
            strip.kitsu.shot_name,
        )
        return None

    logger.info(
        "Strip: %s Shot already existent on server (ID: %s).", strip.name, shot.id
    )
    return shot


def contains(strip: bpy.types.Sequence, framenr: int) -> bool:
    """Returns True if the strip covers the given frame number"""
    return int(strip.frame_final_start) <= framenr <= int(strip.frame_final_end)
