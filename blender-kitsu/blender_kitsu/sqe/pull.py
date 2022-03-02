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

import bpy

from blender_kitsu import bkglobals
from blender_kitsu.types import Cache, Sequence, Project, Shot
from blender_kitsu.logger import LoggerFactory

logger = LoggerFactory.getLogger()


def shot_meta(strip: bpy.types.Sequence, shot: Shot, clear_cache: bool = True) -> None:

    if clear_cache:
        # Clear cache before pulling.
        Cache.clear_all()

    # Update sequence props.
    seq = Sequence.by_id(shot.parent_id)
    strip.kitsu.sequence_id = seq.id
    strip.kitsu.sequence_name = seq.name

    # Update shot props.
    strip.kitsu.shot_id = shot.id
    strip.kitsu.shot_name = shot.name
    strip.kitsu.shot_description = shot.description if shot.description else ""

    # Update project props.
    project = Project.by_id(shot.project_id)
    strip.kitsu.project_id = project.id
    strip.kitsu.project_name = project.name

    # Update meta props.
    strip.kitsu.initialized = True
    strip.kitsu.linked = True

    # Update strip name.
    strip.name = shot.name

    # Log.
    logger.info("Pulled meta from shot: %s to strip: %s", shot.name, strip.name)
