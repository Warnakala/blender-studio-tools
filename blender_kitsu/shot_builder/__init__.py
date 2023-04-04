# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

# <pep8 compliant>

from blender_kitsu.shot_builder.ui import *
from blender_kitsu.shot_builder.connectors.kitsu import *
from blender_kitsu.shot_builder.operators import *
import bpy

# import logging
# logging.basicConfig(level=logging.DEBUG)


# bl_info = {
#     'name': 'Shot Builder',
#     "author": "Jeroen Bakker",
#     'version': (0, 1),
#     'blender': (2, 90, 0),
#     'location': 'Addon Preferences panel and file new menu',
#     'description': 'Shot builder production tool.',
#     'category': 'Studio',
# }


classes = (
    KitsuPreferences,
    SHOTBUILDER_OT_NewShotFile,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.TOPBAR_MT_file_new.append(topbar_file_new_draw_handler)


def unregister():
    bpy.types.TOPBAR_MT_file_new.remove(topbar_file_new_draw_handler)
    for cls in classes:
        bpy.utils.unregister_class(cls)
