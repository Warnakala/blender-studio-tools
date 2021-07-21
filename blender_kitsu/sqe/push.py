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
    shot.data["3d_in"] = strip.kitsu_frame_start
    shot.data["3d_out"] = strip.kitsu_frame_end
    shot.nb_frames = strip.frame_final_duration
    shot.data["fps"] = bkglobals.FPS

    # if user changed the seqeunce the shot belongs to
    # (can only be done by operator not by hand)
    if strip.kitsu.sequence_id != shot.sequence_id:
        sequence = Sequence.by_id(strip.kitsu.sequence_id)
        shot.sequence_id = sequence.id
        shot.parent_id = sequence.id
        shot.sequence_name = sequence.name

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
        data={
            "fps": bkglobals.FPS,
            "3d_in": strip.kitsu_frame_start,
            "3d_out": strip.kitsu_frame_end,
        },
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
