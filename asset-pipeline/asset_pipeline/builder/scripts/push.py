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
As the publish process requires a number of more complex operations, we need to actually have a Blender Instance
opening that file and then executing the operations.
This script can be passed as -P option when starting a blender exe.
It needs a pickle_path after -- . The pickle path contains a pickled BuildContext from the AssetTask.
This BuildContext will be unpickled in this script and processed, which means performing
the publish of the selected TaskLayers in the AssetTask.
"""
import logging
import pickle
import sys

from typing import List, Dict, Union, Any, Set, Optional
from pathlib import Path

from asset_pipeline import prop_utils
from asset_pipeline.builder import AssetBuilder
from asset_pipeline.builder.context import BuildContext
from asset_pipeline.asset_files import AssetPublish

import bpy

logger = logging.getLogger("BSP")

# Get cli input.
argv = sys.argv
# logger.info(argv)
argv = argv[argv.index("--") + 1 :]

logger.info("\n" * 2)
logger.info(f"STARTING NEW BLENDER: {bpy.data.filepath}")
logger.info("RUNNING PUSH SCRIPT")
logger.info("------------------------------------")

try:
    argv[0]
except IndexError:
    raise ValueError("Supply pickle path as first argument after '--'.")
    sys.exit(1)

# Check if pickle path is valid.
pickle_path: str = argv[0]

if not pickle_path:
    raise ValueError("Supply valid pickle path as first argument after '--'.")

pickle_path: Path = Path(pickle_path)

if not pickle_path.exists():
    raise ValueError(f"Pickle path does not exist: {pickle_path.as_posix()}")

# Load pickle
logger.info(f"LOADING PICKLE: %s", pickle_path.as_posix())
with open(pickle_path.as_posix(), "rb") as f:
    BUILD_CONTEXT: BuildContext = pickle.load(f)

# If first publish, only link in asset collection and update properties.
if not BUILD_CONTEXT.asset_publishes:
    asset_publish = AssetPublish(Path(bpy.data.filepath))
    asset_coll = BUILD_CONTEXT.asset_context.asset_collection
    # Update scene asset collection.
    bpy.context.scene.bsp_asset.asset_collection = asset_coll

    # Update asset collection properties.
    asset_coll.bsp_asset.update_props_by_asset_publish(asset_publish)

    # Link in asset collection in scene.
    bpy.context.scene.collection.children.link(asset_coll)
    bpy.context.scene.bsp_asset.asset_collection = asset_coll

    bpy.ops.wm.save_mainfile()
    bpy.ops.wm.quit_blender()
    sys.exit(0)

logger.info("LOAD TRANSFER SETTINGS")

# Fetch transfer settings from AssetContext and update scene settings
# as they are the ones that are used by the pull() process.
TRANSFER_SETTINGS = bpy.context.scene.bsp_asset_transfer_settings
for prop_name, prop in prop_utils.get_property_group_items(TRANSFER_SETTINGS):
    try:
        value = BUILD_CONTEXT.asset_context.transfer_settings[prop_name]
    except KeyError:
        continue
    else:
        setattr(TRANSFER_SETTINGS, prop_name, value)
        logger.info("Loaded setting(%s: %s)", prop_name, str(value))

logger.info(BUILD_CONTEXT)

logger.info(
    f"IMPORTING ASSET COLLECTION FROM TASK: %s",
    BUILD_CONTEXT.asset_task.path.as_posix(),
)

ASSET_BUILDER = AssetBuilder(BUILD_CONTEXT)

ASSET_BUILDER.pull_from_task(bpy.context)

# Delete pickle.
pickle_path.unlink()
logger.info("Deleted pickle: %s", pickle_path.name)

# Quit.
bpy.ops.wm.save_mainfile()
bpy.ops.wm.quit_blender()
sys.exit(0)
