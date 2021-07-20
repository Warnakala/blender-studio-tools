import sys
import logging


logger = logging.getLogger(__name__)

import bpy

# setup prefs
bpy.context.preferences.filepaths.save_version = 0

# purge
logger.info("Starting Recursive Purge")
bpy.ops.outliner.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)

# save
bpy.ops.wm.save_mainfile()
logger.info("Saved file: %s", bpy.data.filepath)

# quit
logger.info("Closing File")
bpy.ops.wm.quit_blender()
