import bpy

from .types import Cache, Sequence, Project, Shot
from .logger import ZLoggerFactory

logger = ZLoggerFactory.getLogger(name=__name__)


def shot_meta(strip: bpy.types.Sequence, shot: Shot) -> None:
    # clear cache before pulling
    Cache.clear_all()

    # update sequence props
    zseq = Sequence.by_id(shot.parent_id)
    strip.kitsu.sequence_id = zseq.id
    strip.kitsu.sequence_name = zseq.name

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
    logger.info("Pulled meta from shot: %s to strip: %s", shot.name, strip.name)
