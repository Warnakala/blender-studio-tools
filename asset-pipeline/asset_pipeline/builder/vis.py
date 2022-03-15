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

from .. import util

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


class EnsureObjectVisibility:
    def get_visibility_driver(self) -> Optional[bpy.types.FCurve]:
        obj = bpy.data.objects.get(self.obj_name)
        assert obj, "Object was renamed while its visibility was being ensured?"
        if hasattr(obj, "animation_data") and obj.animation_data:
            return obj.animation_data.drivers.find("hide_viewport")


    def __init__(self, obj: bpy.types.Object):
        self.obj_name = obj.name

        # Eye icon
        self.hide = obj.hide_get()
        obj.hide_set(False)

        # Screen icon driver
        self.drv_mute = None
        drv = self.get_visibility_driver()
        if drv:
            self.drv_mute = drv.mute
            drv.mute = True

        # Screen icon
        self.hide_viewport = obj.hide_viewport
        obj.hide_viewport = False


    def restore(self):
        obj = bpy.data.objects.get(self.obj_name)
        assert obj, f"Error: Object {self.obj_name} was renamed or removed before its visibility was restored!"
        obj.hide_set(self.hide)

        if self.drv_mute != None: # We want to catch both True and False here.
            drv = self.get_visibility_driver()
            drv.mute = self.drv_mute

        obj.hide_viewport = self.hide_viewport


class EnsureCollectionVisibility:
    """Ensure a collection and all objects within it are visible.
    The original visibility states can be restored using .restore().
    NOTE: Collection and Object names must not change until restore() is called!!!
    """

    def __init__(self, coll: bpy.types.Collection, do_objects=True):
        self.coll_name = coll.name

        # Screen icon
        self.hide_viewport = coll.hide_viewport
        coll.hide_viewport = False

        # Exclude
        layer_coll = get_layer_coll_from_coll(coll)
        self.exclude = layer_coll.exclude
        layer_coll.exclude = False

        # Eye icon
        self.hide = layer_coll.hide_viewport
        layer_coll.hide_viewport = False

        # Objects
        self.object_visibilities = []
        if do_objects:
            for ob in coll.objects:
                self.object_visibilities.append(EnsureObjectVisibility(ob))

    def restore(self) -> None:
        """Restore visibility settings to their original state."""
        coll = bpy.data.collections.get(self.coll_name)

        # Screen icon
        coll.hide_viewport = self.hide_viewport

        # Exclude
        layer_coll = get_layer_coll_from_coll(coll)
        layer_coll.exclude = self.exclude

        # Eye icon
        layer_coll.hide_viewport = self.hide

        # Objects
        for ob_vis in self.object_visibilities:
            ob_vis.restore()
