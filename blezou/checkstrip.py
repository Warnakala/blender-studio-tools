from typing import Optional

import bpy

from . import gazu, util
from .types import ZSequence, ZProject, ZShot, ZCache
from .logger import ZLoggerFactory

logger = ZLoggerFactory.getLogger(name=__name__)


def is_valid_type(strip: bpy.types.Sequence) -> bool:
    if not strip.type in util.VALID_STRIP_TYPES:
        logger.info("Strip: %s. Invalid type.", strip.type)
        return False
    return True


def is_initialized(strip: bpy.types.Sequence) -> bool:
    """Returns True if strip.blezou.initialized is True else False"""
    if not strip.blezou.initialized:
        logger.info("Strip: %s. Not initialized.", strip.name)
        return False

    logger.info("Strip: %s. Is initialized.", strip.name)
    return True


def is_linked(strip: bpy.types.Sequence) -> bool:
    """Returns True if strip.blezou.linked is True else False"""
    if not strip.blezou.linked:
        logger.info("Strip: %s. Not linked yet.", strip.name)
        return False

    logger.info("Strip: %s. Is linked to ID: %s.", strip.name, strip.blezou.shot_id)
    return True


def has_meta(strip: bpy.types.Sequence) -> bool:
    """Returns True if strip.blezou.shot_name and strip.blezou.sequence_name is Truethy else False"""
    seq = strip.blezou.sequence_name
    shot = strip.blezou.shot_name

    if not bool(seq and shot):
        logger.info("Strip: %s. Missing metadata.", strip.name)
        return False

    logger.info(
        "Strip: %s. Has metadata (Sequence: %s, Shot: %s).", strip.name, seq, shot
    )
    return True


def shot_exists_by_id(strip: bpy.types.Sequence) -> Optional[ZShot]:
    """Returns ZShot instance if shot with strip.blezou.shot_id exists else None"""

    ZCache.clear_all()

    try:
        zshot = ZShot.by_id(strip.blezou.shot_id)
    except (gazu.exception.RouteNotFoundException, gazu.exception.ServerErrorException):
        logger.info(
            "Strip: %s No shot found on server with ID: %s",
            strip.name,
            strip.blezou.shot_id,
        )
        return None

    logger.info(
        "Strip: %s Shot %s exists on server (ID: %s).", strip.name, zshot.name, zshot.id
    )
    return zshot


def seq_exists_by_name(
    strip: bpy.types.Sequence, zproject: ZProject
) -> Optional[ZSequence]:
    """Returns ZSequence instance if strip.blezou.sequence_name exists on server, else None"""

    ZCache.clear_all()

    zseq = zproject.get_sequence_by_name(strip.blezou.sequence_name)
    if not zseq:
        logger.info(
            "Strip: %s Sequence %s does not exist on server.",
            strip.name,
            strip.blezou.sequence_name,
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
    strip: bpy.types.Sequence, zproject: ZProject, zsequence: ZSequence
) -> Optional[ZShot]:
    """Returns ZShot instance if strip.blezou.shot_name exists on server, else None."""

    ZCache.clear_all()

    zshot = zproject.get_shot_by_name(zsequence, strip.blezou.shot_name)
    if not zshot:
        logger.info(
            "Strip: %s Shot %s does not exist on server.",
            strip.name,
            strip.blezou.shot_name,
        )
        return None

    logger.info(
        "Strip: %s Shot already existent on server (ID: %s).", strip.name, zshot.id
    )
    return zshot


def contains(strip: bpy.types.Sequence, framenr: int) -> bool:
    """Returns True if the strip covers the given frame number"""
    return int(strip.frame_final_start) <= framenr <= int(strip.frame_final_end)
