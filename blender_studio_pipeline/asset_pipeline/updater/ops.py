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

from typing import List, Dict, Union, Any, Set, Optional, Tuple
from pathlib import Path

import bpy
from bpy.app.handlers import persistent

from ... import util
from .. import updater
from .asset_updater import AssetUpdater
from . import opsdata

class BSP_ASSET_UPDATER_collect_assets(bpy.types.Operator):
    bl_idname = "bsp_asset.collect_assets"
    bl_label = "Collect Assets"
    bl_description = "Scans Scene for imported Assets"

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return True

    def execute(self, context: bpy.types.Context) -> Set[str]:

        # Initialize Asset Updater and scan for scene.
        updater.ASSET_UPDATER = AssetUpdater(context)

        # Populate context with collected asset collections.
        opsdata.populate_context_with_imported_asset_colls(context, updater.ASSET_UPDATER)

        # Redraw UI.
        util.redraw_ui()

        return {"FINISHED"}


@persistent
def collect_assets_in_scene(_):
    pass


# ----------------REGISTER--------------.

classes = [BSP_ASSET_UPDATER_collect_assets]


def register() -> None:
    for cls in classes:
        bpy.utils.register_class(cls)

    # Handlers.
    # bpy.app.handlers.load_post.append(create_prod_context)


def unregister() -> None:

    # Handlers.
    # bpy.app.handlers.load_post.remove(create_undo_context)

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
