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
"""
This script can be passed as -P option when starting a blender exe.
It needs a pickle_path after -- . The pickle path contains a pickled BuildContext from the AssetTask.
This BuildContext will be unpickled in this script and processed, which means performing
the publish of the selected TaskLayers in the AssetTask.
"""

import pickle
import sys
from typing import List, Dict, Union, Any, Set, Optional

from blender_studio_pipeline.asset_pipeline.builder.context import BuildContext
from blender_studio_pipeline.asset_pipeline.builder.asset_importer import AssetImporter
from blender_studio_pipeline.asset_pipeline.builder.asset_mapping import (
    TransferCollectionTriplet,
    AssetTransferMapping,
)
from blender_studio_pipeline.asset_pipeline import prop_utils
from blender_studio_pipeline.asset_pipeline.builder import asset_suffix
from blender_studio_pipeline import util
from blender_studio_pipeline.asset_pipeline.builder.vis import EnsureVisible

from pathlib import Path

import bpy

# Get cli input.
argv = sys.argv
# print(argv)
argv = argv[argv.index("--") + 1 :]

print("\n" * 2)
print(f"STARTING NEW BLENDER: {bpy.data.filepath}")
print("RUNNING PUSH SCRIPT")
print("------------------------------------")

try:
    argv[0]
except IndexError:
    raise ValueError("Supply pickle path as first argument after '--'.")
    sys.exit(1)

# Check if pickle path is valid.
pickle_path = argv[0]

if not pickle_path:
    raise ValueError("Supply valid pickle path as first argument after '--'.")

pickle_path = Path(pickle_path)

if not pickle_path.exists():
    raise ValueError(f"Pickle path does not exist: {pickle_path.as_posix()}")

# Load pickle
print(f"LOADING PICKLE: {pickle_path.as_posix()}")
with open(pickle_path.as_posix(), "rb") as f:
    BUILD_CONTEXT: BuildContext = pickle.load(f)

print("LOAD TRANSFER SETTINGS")
# Fetch transfer settings from AssetContext.
TRANSFER_SETTINGS = bpy.context.scene.bsp_asset_transfer_settings
for prop_name, prop in prop_utils.get_property_group_items(TRANSFER_SETTINGS):
    try:
        value = BUILD_CONTEXT.asset_context.transfer_settings[prop_name]
    except KeyError:
        continue
    else:
        setattr(TRANSFER_SETTINGS, prop_name, value)
        print(f"Loaded setting({prop_name}: {value})")

print(BUILD_CONTEXT)

print(
    f"IMPORTING ASSET COLLECTION FROM TASK: {BUILD_CONTEXT.asset_task.path.as_posix()}"
)

# Import Asset Collection form Asset Task.
asset_task = BUILD_CONTEXT.asset_task
ASSET_IMPORTER = AssetImporter(BUILD_CONTEXT)
merge_triplet: TransferCollectionTriplet = ASSET_IMPORTER.import_asset_task()

# Apparently Blender does not evaluate objects or collections in the depsgraph
# in some cases if they are not visible. This is something Users should not have to take
# care about when writing their transfer data instructions. So we will make sure here
# that everything is visible and after the transfer the original state will be restored.
vis_objs: List[EnsureVisible] = []
for coll in merge_triplet.get_collections():
    for obj in coll.all_objects:
        vis_objs.append(EnsureVisible(obj))


# The target collection (base) was already decided by ASSET_IMPORTER.import_asset_task()
# and is saved in merge_triplet.target_coll.
mapping_task_target = AssetTransferMapping(
    merge_triplet.task_coll, merge_triplet.target_coll
)
mapping_publish_target = AssetTransferMapping(
    merge_triplet.publish_coll, merge_triplet.target_coll
)

# Process only the TaskLayers that were ticked as 'use'.
used_task_layers = (
    BUILD_CONTEXT.asset_context.task_layer_assembly.get_used_task_layers()
)

# Should be ordered, just in case.
task_layers = BUILD_CONTEXT.prod_context.task_layers
task_layers.sort(key=lambda tl: tl.order)

# Perform Task Layer merging.

# Note: We always want to apply all TaskLayers except for the Task Layer with the lowest order
# aka 'Base Task Layer'. This Task Layer gives us the starting point on which to apply all other Task Layers
# on. The asset importer already handles this logic by supplying as with the right TARGET collection
# after import. That's why we exclude the first task layer here in the loop.

print(f"Using {task_layers[0].name} as base.")
for task_layer in task_layers[1:]:

    # Now we need to decide if we want to transfer data from
    # the task collection to the target collection
    # or
    # the publish collection to the target collection
    if task_layer in used_task_layers:
        print(
            f"Transferring {task_layer.name} from {merge_triplet.task_coll.name} to {merge_triplet.target_coll.name}."
        )
        task_layer.transfer_data(bpy.context, mapping_task_target, TRANSFER_SETTINGS)
    else:
        print(
            f"Transferring {task_layer.name} from {merge_triplet.publish_coll.name} to {merge_triplet.target_coll.name}."
        )
        task_layer.transfer_data(bpy.context, mapping_publish_target, TRANSFER_SETTINGS)


# Restore Visibility.
for obj in vis_objs:
    obj.restore()


# Remove non TARGET collections.
for coll in [merge_triplet.publish_coll, merge_triplet.task_coll]:
    util.del_collection(coll)


# Remove suffix from TARGET Collection.
asset_suffix.remove_suffix_from_hierarchy(merge_triplet.target_coll)
