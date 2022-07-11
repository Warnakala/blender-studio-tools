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

from typing import List, Dict, Union, Any, Set, Optional, Tuple, Generator

import bpy
from bpy import types
import addon_utils


def redraw_ui() -> None:
    """
    Forces blender to redraw the UI.
    """
    for screen in bpy.data.screens:
        for area in screen.areas:
            area.tag_redraw()


def get_addon_prefs() -> bpy.types.AddonPreferences:
    return bpy.context.preferences.addons[__package__].preferences


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


def is_addon_active(module_name, context=None):
    """Returns whether an addon is loaded and enabled in the current workspace."""
    if not context:
        context=bpy.context
    is_enabled_in_prefs = addon_utils.check(module_name)[1]
    if is_enabled_in_prefs and context.workspace.use_filter_by_owner:
        is_enabled_in_workspace = module_name in context.workspace.owner_ids
        return is_enabled_in_workspace

    return is_enabled_in_prefs


def reset_armature_pose(
    rig: bpy.types.Object,
    only_selected=False,
    reset_transforms=True,
    reset_properties=True,
):
    bones = rig.pose.bones
    if only_selected:
        bones = [pb for pb in rig.pose.bones if pb.bone.select]

    for pb in bones:
        if reset_transforms:
            pb.location = (0, 0, 0)
            pb.rotation_euler = (0, 0, 0)
            pb.rotation_quaternion = (1, 0, 0, 0)
            pb.scale = (1, 1, 1)

        if reset_properties and len(pb.keys()) > 0:
            rna_properties = [
                prop.identifier for prop in pb.bl_rna.properties if prop.is_runtime
            ]

            # Reset custom property values to their default value
            for key in pb.keys():
                if key.startswith("$"):
                    continue
                if key in rna_properties:
                    continue  # Addon defined property.

                ui_data = None
                try:
                    ui_data = pb.id_properties_ui(key)
                    if not ui_data:
                        continue
                    ui_data = ui_data.as_dict()
                    if not "default" in ui_data:
                        continue
                except TypeError:
                    # Some properties don't support UI data, and so don't have a
                    # default value. (like addon PropertyGroups)
                    pass

                if not ui_data:
                    continue

                if type(pb[key]) not in (float, int):
                    continue
                pb[key] = ui_data["default"]


ID_INFO = [
    (types.WindowManager, 'WINDOWMANAGER', 'window_managers'),
    (types.Scene, 'SCENE', 'scenes'),
    (types.World, 'WORLD', 'worlds'),
    (types.Collection, 'COLLECTION', 'collections'),

    (types.Armature, 'ARMATURE', 'armatures'),
    (types.Mesh, 'MESH', 'meshes'),
    (types.Camera, 'CAMERA', 'cameras'),
    (types.Lattice, 'LATTICE', 'lattices'),
    (types.Light, 'LIGHT', 'lights'),
    (types.Speaker, 'SPEAKER', 'speakers'),
    (types.Volume, 'VOLUME', 'volumes'),
    (types.GreasePencil, 'GREASEPENCIL', 'grease_pencils'),
    (types.Curve, 'CURVE', 'curves'),
    (types.LightProbe, 'LIGHT_PROBE', 'lightprobes'),

    (types.MetaBall, 'METABALL', 'metaballs'),
    (types.Object, 'OBJECT', 'objects'),
    (types.Action, 'ACTION', 'actions'),
    (types.Key, 'KEY', 'shape_keys'),
    (types.Sound, 'SOUND', 'sounds'),
 
    (types.Material, 'MATERIAL', 'materials'),
    (types.NodeTree, 'NODETREE', 'node_groups'),
    (types.Image, 'IMAGE', 'images'),

    (types.Mask, 'MASK', 'masks'),
    (types.FreestyleLineStyle, 'LINESTYLE', 'linestyles'),
    (types.Library, 'LIBRARY', 'libraries'),
    (types.VectorFont, 'FONT', 'fonts'),
    (types.CacheFile, 'CACHE_FILE', 'cache_files'),
    (types.PointCloud, 'POINT_CLOUD', 'pointclouds'),
    (types.Curves, 'HAIR_CURVES', 'hair_curves'),
    (types.Text, 'TEXT', 'texts'),
    (types.Simulation, 'SIMULATION', 'simulations'),
    (types.ParticleSettings, 'PARTICLE', 'particles'),
    (types.Palette, 'PALETTE', 'palettes'),
    (types.PaintCurve, 'PAINT_CURVE', 'paint_curves'),
    (types.MovieClip, 'MOVIE_CLIP', 'movieclips'),

    (types.WorkSpace, 'WORKSPACE', 'workspaces'),
    (types.Screen, 'SCREEN', 'screens'),
    (types.Brush, 'BRUSH', 'brushes'),
    (types.Texture, 'TEXTURE', 'textures'),
]

# Map datablock Python classes to their string representation.
ID_CLASS_TO_IDENTIFIER: Dict[type, Tuple[str, int]] = dict(
    [(tup[0], (tup[1])) for tup in ID_INFO]
)

def get_fundamental_id_type(datablock: bpy.types.ID) -> Any:
    """Certain datablocks have very specific types.
    This function should return their fundamental type, ie. parent class."""
    for id_type in ID_CLASS_TO_IDENTIFIER.keys():
        if isinstance(datablock, id_type):
            return id_type


def get_storage_of_id(datablock: bpy.types.ID) -> 'bpy_prop_collection':
    """Return the storage collection property of the datablock.
    Eg. for an object, returns bpy.data.objects.
    """

    fundamental_type = get_fundamental_id_type(datablock)
    return getattr(bpy.data, ID_INFO[fundamental_type][2])
