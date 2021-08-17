import sys
import bpy

import logging

logger = logging.getLogger(__name__)

# Check if recursive is on.
if not bpy.context.preferences.experimental.override_auto_resync:
    logger.error("Override auto resync is turned off!")
    sys.exit(1)
