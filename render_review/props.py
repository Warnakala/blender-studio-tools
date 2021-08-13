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

from typing import Set, Union, Optional, List, Dict, Any
from pathlib import Path

import bpy

from render_review.log import LoggerFactory

logger = LoggerFactory.getLogger(name=__name__)


class RR_isolate_collection_prop(bpy.types.PropertyGroup):
    mute: bpy.props.BoolProperty()


class RR_property_group_scene(bpy.types.PropertyGroup):
    """"""

    render_dir: bpy.props.StringProperty(name="Render Directory", subtype="DIR_PATH")
    isolate_view: bpy.props.CollectionProperty(type=RR_isolate_collection_prop)

    @property
    def render_dir_path(self):
        if not self.is_render_dir_valid:
            return None
        return Path(bpy.path.abspath(self.render_dir)).absolute()

    @property
    def is_render_dir_valid(self) -> bool:
        if not self.render_dir:
            return False

        if not bpy.data.filepath and self.render_dir.startswith("//"):
            return False

        return True


class RR_property_group_sequence(bpy.types.PropertyGroup):
    """
    Property group that will be registered on sequence strips.
    """

    is_render: bpy.props.BoolProperty(name="Is Render")
    is_approved: bpy.props.BoolProperty(name="Is Approved")
    frames_found_text: bpy.props.StringProperty(name="Frames Found")
    shot_name: bpy.props.StringProperty(name="Shot")


# ----------------REGISTER--------------

classes = [
    RR_isolate_collection_prop,
    RR_property_group_scene,
    RR_property_group_sequence,
]


def register():

    for cls in classes:
        bpy.utils.register_class(cls)

    # Scene Properties
    bpy.types.Scene.rr = bpy.props.PointerProperty(
        name="Render Review",
        type=RR_property_group_scene,
        description="Metadata that is required for render_review",
    )

    # Sequence Properties
    bpy.types.Sequence.rr = bpy.props.PointerProperty(
        name="Render Review",
        type=RR_property_group_sequence,
        description="Metadata that is required for render_review",
    )


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
