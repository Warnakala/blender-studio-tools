import bpy

from .types import ZCache, ZSequence, ZProject, ZShot
from .logger import ZLoggerFactory

logger = ZLoggerFactory.getLogger(name=__name__)


def shot_meta(strip: bpy.types.Sequence, zshot: ZShot) -> None:
    # clear cache before pulling
    ZCache.clear_all()

    # update sequence props
    zseq = ZSequence.by_id(zshot.parent_id)
    strip.kitsu.sequence_id = zseq.id
    strip.kitsu.sequence_name = zseq.name

    # update shot props
    strip.kitsu.shot_id = zshot.id
    strip.kitsu.shot_name = zshot.name
    strip.kitsu.shot_description = zshot.description if zshot.description else ""

    # update project props
    zproject = ZProject.by_id(zshot.project_id)
    strip.kitsu.project_id = zproject.id
    strip.kitsu.project_name = zproject.name

    # update meta props
    strip.kitsu.initialized = True
    strip.kitsu.linked = True
    logger.info("Pulled meta from shot: %s to strip: %s", zshot.name, strip.name)
