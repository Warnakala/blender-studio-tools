import bpy

from .types import ZCache, ZSequence, ZProject, ZShot
from .logger import ZLoggerFactory

logger = ZLoggerFactory.getLogger(name=__name__)


def shot_meta(strip: bpy.types.Sequence, zshot: ZShot) -> None:
    # clear cache before pulling
    ZCache.clear_all()

    # update sequence props
    zseq = ZSequence.by_id(zshot.parent_id)
    strip.blezou.sequence_id = zseq.id
    strip.blezou.sequence_name = zseq.name

    # update shot props
    strip.blezou.shot_id = zshot.id
    strip.blezou.shot_name = zshot.name
    strip.blezou.shot_description = zshot.description if zshot.description else ""

    # update project props
    zproject = ZProject.by_id(zshot.project_id)
    strip.blezou.project_id = zproject.id
    strip.blezou.project_name = zproject.name

    # update meta props
    strip.blezou.initialized = True
    strip.blezou.linked = True
    logger.info("Pulled meta from shot: %s to strip: %s", zshot.name, strip.name)
