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
