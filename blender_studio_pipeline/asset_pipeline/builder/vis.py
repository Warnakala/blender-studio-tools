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

# This code is copied over from character-pipeline-assistant/utils.py file.
# https://gitlab.com/blender/character-pipeline-assistant
# Original Author of this code is: Unknown.

import logging

from typing import List, Dict, Union, Any, Set, Optional, Tuple

from pathlib import Path

import bpy

from ... import util

logger = logging.getLogger("BSP")


def get_layer_coll_from_coll(
    collection: bpy.types.Collection,
) -> Optional[bpy.types.LayerCollection]:

    lcolls = util.traverse_collection_tree(bpy.context.view_layer.layer_collection)
    for lcoll in lcolls:
        if lcoll.name == collection.name:
            return lcoll

    return None


def set_active_collection(collection: bpy.types.Collection) -> None:
    layer_collection = get_layer_coll_from_coll(collection)
    bpy.context.view_layer.active_layer_collection = layer_collection


class EnsureVisible:
    """Ensure an object is visible, then reset it to how it was before."""

    def __init__(self, obj: bpy.types.Object):
        """Ensure an object is visible, and create this small object to manage that object's visibility-ensured-ness."""
        self.obj_name: str = obj.name
        self.obj_hide: bool = obj.hide_get()
        self.obj_hide_viewport: bool = obj.hide_viewport
        self.temp_coll: Optional[bpy.types.Collection] = None
        self.drv_state: bool = (
            False  # Original state of the hide_viewport driver, if exists
        )

        if not obj.visible_get():
            # Mute driver on object visibility if there is one
            if hasattr(obj, "animation_data") and obj.animation_data:
                drv = obj.animation_data.drivers.find("hide_viewport")
                if drv:
                    self.drv_state = drv.mute
                    drv.mute = True

            obj.hide_set(False)
            obj.hide_viewport = False

        if not obj.visible_get():
            # If the object is still not visible, we need to move it to a visible collection. To not break other scripts though, we should restore the active collection afterwards.
            active_coll = bpy.context.collection

            coll_name = "temp_visible"
            temp_coll = bpy.data.collections.get(coll_name)
            if not temp_coll:
                temp_coll = bpy.data.collections.new(coll_name)
            if coll_name not in bpy.context.scene.collection.children:
                bpy.context.scene.collection.children.link(temp_coll)

            if obj.name not in temp_coll.objects:
                temp_coll.objects.link(obj)

            self.temp_coll = temp_coll

            set_active_collection(active_coll)

    def restore(self) -> None:
        """Restore visibility settings to their original state."""
        obj = bpy.data.objects.get(self.obj_name)
        if not obj:
            return

        # Restore driver on object visibility if there is one
        if hasattr(obj, "animation_data") and obj.animation_data:
            drv = obj.animation_data.drivers.find("hide_viewport")
            if drv:
                drv.mute = self.drv_state

        obj.hide_set(self.obj_hide)
        obj.hide_viewport = self.obj_hide_viewport

        # Remove object from temp collection
        if self.temp_coll and obj.name in self.temp_coll.objects:
            self.temp_coll.objects.unlink(obj)

            # Delete temp collection if it's empty now.
            if len(self.temp_coll.objects) == 0:
                bpy.data.collections.remove(self.temp_coll)
                self.temp_coll = None
