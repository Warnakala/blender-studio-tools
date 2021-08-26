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
from typing import Set, Union, Optional, List, Dict, Any, Tuple

import bpy

from video_player.log import LoggerFactory


logger = LoggerFactory.getLogger(name=__name__)


class VP_OT_load_media(bpy.types.Operator):

    bl_idname = "video_player.load_media"
    bl_label = "Load Media"
    bl_description = "Loads media in to sequence editor" ""
    filepath: bpy.props.StringProperty(name="Filepath", subtype="FILE_PATH")

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return True

    def execute(self, context: bpy.types.Context) -> Set[str]:
        print(self.filepath)
        self.report({"INFO"}, self.filepath)
        return {"FINISHED"}


def find_file_browser(context: bpy.types.Context) -> Optional[bpy.types.Area]:
    for area in context.screen.areas:
        if area.type == "FILE_BROWSER":
            return area
    return None


prev_file_name: Optional[str] = None


def callback_filename_change(dummy: None):
    global prev_file_name
    area = find_file_browser(bpy.context)

    # Early return no area.
    if not area:
        return

    params = area.spaces[0].params

    # Early return filename did not change.
    if prev_file_name == params.filename:
        return

    # Update prev_file_name.
    prev_file_name = params.filename
    print(prev_file_name)

    # Execute load media op.
    # TODO: decode byte string to actual string
    filepath = Path(bpy.path.abspath(str(params.directory))) / params.filename
    bpy.ops.video_player.load_media(filepath=filepath.as_posix())


# ----------------REGISTER--------------.


classes = [VP_OT_load_media]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    # Handlers.
    bpy.types.SpaceFileBrowser.draw_handler_add(
        callback_filename_change, (None,), "WINDOW", "POST_PIXEL"
    )


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    # Handlers.
    bpy.types.SpaceFileBrowser.draw_handler_remove(callback_filename_change, "WINDOW")
