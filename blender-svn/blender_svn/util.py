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
# (c) 2022, Blender Foundation - Demeter Dzadik

from typing import List, Dict, Union, Any, Set, Optional, Tuple, Generator, Callable

import bpy


def redraw_ui() -> None:
    """
    Forces blender to redraw the UI.
    """
    for screen in bpy.data.screens:
        for area in screen.areas:
            area.tag_redraw()


def get_addon_prefs(context: bpy.types.Context=None) -> bpy.types.AddonPreferences:
    return context.preferences.addons[__package__].preferences

def make_setter_func_readonly(prop: str) -> Callable:
    """A setter function for read-only Python properties.
    We can use a 'lock' toggle to prevent changing properties in the UI.
    This way we can avoid graying out read-only properties in the UI.
    """
    def set_readonly(self, value: Any):
        if hasattr(self, 'lock'):
            if self.lock:
                return
        else:
            # If there is no lock property, always prevent changing the property.
            # In this case the property can still be changed via Python dictionary syntax.
            return
        self[prop] = value

    return set_readonly

def make_getter_func(prop: str, default: Any) -> Callable:
    """Does nothing special, but property definitions require a getter 
    if we want to give them a setter, so this has to exist as well."""

    def get(self):
        if prop in self:
            return self[prop]
        return default

    return get


def is_file_saved() -> bool:
    return bool(bpy.data.filepath)


def traverse_collection_tree(
    collection: bpy.types.Collection,
) -> Generator[bpy.types.Collection, None, None]:
    yield collection
    for child in collection.children:
        yield from traverse_collection_tree(child)


def del_collection(collection: bpy.types.Collection) -> None:
    collection.user_clear()
    bpy.data.collections.remove(collection)
