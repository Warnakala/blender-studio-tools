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
from blender_studio_pipeline.asset_pipeline.builder.asset_builder import AssetBuilder
from blender_studio_pipeline.asset_pipeline.builder.asset_importer import AssetImporter

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

print(BUILD_CONTEXT)

print(
    f"IMPORTING ASSET COLLECTION FROM TASK: {BUILD_CONTEXT.asset_task.path.as_posix()}"
)

# Import Asset Collection form Asset Task.
asset_task = BUILD_CONTEXT.asset_task
ASSET_IMPORTER = AssetImporter(BUILD_CONTEXT)
ASSET_IMPORTER.import_asset_task()
