import argparse
import sys
import os

from pathlib import Path

from blender_purge.main import purge_file, cancel_program
from blender_purge.log import LoggerFactory

logger = LoggerFactory.getLogger()

# Command line arguments
parser = argparse.ArgumentParser()
parser.add_argument(
    "-f", "--file", help="Path to a file on which to perform recursive purge"
)


def main():
    # Collect arguments
    args = parser.parse_args()
    file = args.file

    if not file:
        logger.error("Please provide a file to be purged with -f/--file")
        cancel_program()

    sys.exit(purge_file(Path(args.file)))


if __name__ == "__main__":
    main()
