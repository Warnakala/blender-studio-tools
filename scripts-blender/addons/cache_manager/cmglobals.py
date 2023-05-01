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
# (c) 2021, Blender Foundation

from typing import List

MODIFIER_NAME = "cm_cache"

CACHE_OFF_SUFFIX = ".cacheoff"
CACHE_ON_SUFFIX = ".cacheon"

CONSTRAINT_NAME = "cm_cache"

VALID_OBJECT_TYPES = {"MESH", "CAMERA", "EMPTY", "LATTICE"}
CAMERA_TYPES = {"PERSP", "ORTHO", "PANO"}

_VERSION_PATTERN = "v\d\d\d"

MODIFIERS_KEEP: List[str] = [
    "SUBSURF",
    "PARTICLE_SYSTEM",
    "MESH_SEQUENCE_CACHE",
    "DATA_TRANSFER",
    "NORMAL_EDIT",
    "NODES",
]
CONSTRAINTS_KEEP: List[str] = [
    "TRANSFORM_CACHE",
]

DRIVER_VIS_DATA_PATHS: List[str] = [
    "hide_viewport",
    "hide_render",
    "show_viewport",
    "show_render",
]

CAM_DATA_PATHS: List[str] = [
    "clip_end",
    "clip_start",
    "display_size",
    "dof.aperture_blades",
    "dof.aperture_fstop",
    "dof.aperture_ratio",
    "dof.aperture_rotation",
    "dof.focus_distance",
    "lens",
    "ortho_scale",
    "sensor_fit",
    "sensor_height",
    "sensor_width",
    "shift_x",
    "shift_y",
]

INSTANCE_TYPES: List[str] = ["NONE", "COLLECTION", "VERTS", "FACES"]

# "lens_unit",
# "angle",
# "angle_x",
# "angle_y",
