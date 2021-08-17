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

import bpy

from contactsheet.log import LoggerFactory

logger = LoggerFactory.getLogger(name=__name__)


class CS_meta(bpy.types.PropertyGroup):
    scene: bpy.props.PointerProperty(type=bpy.types.Scene)
    use_proxies: bpy.props.BoolProperty()
    proxy_render_size: bpy.props.StringProperty(default="PROXY_100")


class CS_property_group_scene(bpy.types.PropertyGroup):
    is_contactsheet: bpy.props.BoolProperty()

    contactsheet_meta: bpy.props.PointerProperty(type=CS_meta)

    rows: bpy.props.IntProperty(
        name="Rows",
        description="Controls how many rows should be used for the contactsheet",
        min=1,
        default=4,
    )

    use_custom_rows: bpy.props.BoolProperty(
        name="Use custom amount of rows",
        description="Enables to overwrite the amount of rows for the contactsheet. Is otherwise calculated automatically",
    )

    contactsheet_x: bpy.props.IntProperty(
        name="Resolution X",
        default=1920,
        min=100,
        description="X resolution of contactsheet",
    )
    contactsheet_y: bpy.props.IntProperty(
        name="Resolution Y",
        default=1080,
        min=100,
        description="Y resolution of contactsheet",
    )


# ----------------REGISTER--------------.

classes = [
    CS_meta,
    CS_property_group_scene,
]


def register():

    for cls in classes:
        bpy.utils.register_class(cls)

    # Scene Properties.
    bpy.types.Scene.contactsheet = bpy.props.PointerProperty(
        name="Contactsheet",
        type=CS_property_group_scene,
        description="Metadata that is required for contactsheet",
    )


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
