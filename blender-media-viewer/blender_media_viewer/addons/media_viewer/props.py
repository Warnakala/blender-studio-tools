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


from pathlib import Path
from typing import Tuple, Any, List, Union, Dict, Optional

import bpy

from media_viewer.log import LoggerFactory
from media_viewer import vars

logger = LoggerFactory.getLogger(name=__name__)


class MV_property_group(bpy.types.PropertyGroup):
    """
    Property group that will be registered on scene.
    """

    review_output_dir: bpy.props.StringProperty(
        name="Review Outpout",
        subtype="DIR_PATH",
        default=vars.REVIEW_OUTPUT_DIR.as_posix(),
    )
    sequence_file_type: bpy.props.EnumProperty(
        name="File Format",
        items=[
            ("MOVIE", "MOVIE", "Creates mp4 file"),
            ("IMAGE", "IMAGE", "Creates image sequence in subfolder"),
        ],
        default="MOVIE",
        description="Controls if sequence output should be a .mp4 or a jpg sequence",
    )


# ----------------REGISTER--------------.

classes = [
    MV_property_group,
]


def register():

    for cls in classes:
        bpy.utils.register_class(cls)

    # Window Manager Properties.
    bpy.types.WindowManager.media_viewer = bpy.props.PointerProperty(
        name="Media Viewer",
        type=MV_property_group,
        description="Metadata that is required for the blender-media-viewer",
    )


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
