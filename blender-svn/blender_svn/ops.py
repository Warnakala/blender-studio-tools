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

from . import util, client, opsdata

logger = logging.getLogger("SVN")


class SVN_collect_dirty_files_local(bpy.types.Operator):
    bl_idname = "svn.collect_dirty_files_local"
    bl_label = "Collect Dirty Files Local"
    bl_description = (
        "Checks this .blend file and all its external references for uncommitted changes "
        "Populates a scene property with those files so they can be displayed in the UI"
    )

    def execute(self, context: bpy.types.Context) -> Set[str]:

        # Populate context with collected asset collections.
        opsdata.populate_context_with_external_files(
            context,
        )

        # Redraw UI.
        util.redraw_ui()

        return {"FINISHED"}


@persistent
def init_svn_client_local(_) -> None:
    prefs = util.get_addon_prefs()
    path: Optional[Path] = prefs.svn_directory_path

    # If path not set yet in add-on preferences.
    if not path:
        return

    client.init_local_client(path)


# ----------------REGISTER--------------.

classes = [SVN_collect_dirty_files_local]


def register() -> None:
    for cls in classes:
        bpy.utils.register_class(cls)

    # Handlers.
    bpy.app.handlers.load_post.append(init_svn_client_local)


def unregister() -> None:

    # Handlers.
    bpy.app.handlers.load_post.remove(init_svn_client_local)

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
