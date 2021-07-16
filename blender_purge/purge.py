import logging


logger = logging.getLogger(__name__)

import bpy

# purge
logger.info("Starting Recursive Purge")
bpy.ops.outliner.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)

# save
bpy.ops.wm.save_as_mainfile(filepath="/tmp/test.blend")
logger.info("Saved file: %s", bpy.data.filepath)

# quit
logger.info("Closing File")
bpy.ops.wm.quit_blender()
