import argparse
import sys
import os

from pathlib import Path

from blender_purge import app
from blender_purge.log import LoggerFactory

logger = LoggerFactory.getLogger()

# Command line arguments
parser = argparse.ArgumentParser()
parser.add_argument("path", help="Path to a file or folder on which to perform purge")
parser.add_argument(
    "-R",
    help="If -R is provided in combination with a folder path will perform recursive purge",
)
parser.add_argument(
    "-c", "--confirm", help="Ask for confirmation before purging", action="store_true"
)


def main():
    # Parse arguments
    args = parser.parse_args()
    path = args.path
    print(type(args))
    if not path:
        logger.error("Please provide a path as first argument")
        app.cancel_program()

    app.purge(args)


if __name__ == "__main__":
    main()
