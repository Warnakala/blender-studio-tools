import sys
from pathlib import Path

from blender_purge.log import LoggerFactory

logger = LoggerFactory.getLogger()


def cancel_program():
    logger.info("# Exiting blender-purge")
    sys.exit(0)

def purge_file(path: Path) -> None:
    print(f"Purging path: {path.as_posix()}")
