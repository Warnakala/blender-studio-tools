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
import logging
from typing import Optional, Any, Set, Tuple, List
from pathlib import Path

import bpy


logger = logging.getLogger(name="BSP")


class BSP_addon_preferences(bpy.types.AddonPreferences):

    bl_idname = __package__

    def get_prod_task_layers_module_path(self) -> str:
        if not self.prod_config_dir:
            return ""

        return Path(self.prod_config_dir).joinpath("task_layers.py").as_posix()

    prod_config_dir: bpy.props.StringProperty(  # type: ignore
        name="Production Config Directory",
        default="",
        subtype="DIR_PATH",
    )

    prod_task_layers_module: bpy.props.StringProperty(  # type: ignore
        name="Production Task Layers Module",
        default="",
        get=get_prod_task_layers_module_path,
    )

    def is_prod_task_layers_module_path_valid(self) -> bool:
        path = self.get_prod_task_layers_module_path()
        if not path:
            return False

        if not Path(path).exists():
            return False
        return True

    def draw(self, context: bpy.types.Context) -> None:
        layout: bpy.types.UILayout = self.layout

        # Production Settings.
        box = layout.box()
        box.label(text="Production", icon="FILEBROWSER")

        # Production Config Dir.
        row = box.row(align=True)
        row.prop(self, "prod_config_dir")

        # Production Task Layers Module.
        icon = "NONE"
        row = box.row(align=True)

        if not self.is_prod_task_layers_module_path_valid():
            icon = "ERROR"

        row.prop(self, "prod_task_layers_module", icon=icon)


# ----------------REGISTER--------------.

classes = [BSP_addon_preferences]


def register() -> None:
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
