import sys
import logging


logger = logging.getLogger(__name__)

import bpy

# Setup prefs.
bpy.context.preferences.filepaths.save_version = 0

# Purge.
logger.info("Starting Recursive Purge")
bpy.ops.outliner.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)

# Save.
bpy.ops.wm.save_mainfile()
logger.info("Saved file: %s", bpy.data.filepath)

# Quit.
logger.info("Closing File")
bpy.ops.wm.quit_blender()
