import argparse
import sys
import os
import importlib

from pathlib import Path

from blender_purge import app
from blender_purge.log import LoggerFactory

importlib.reload(app)
logger = LoggerFactory.getLogger()

# Command line arguments
parser = argparse.ArgumentParser()
parser.add_argument(
    "path", help="Path to a file or folder on which to perform purge", type=str
)
parser.add_argument(
    "-R",
    "--recursive",
    help="If -R is provided in combination with a folder path will perform recursive purge",
    action="store_true",
)
parser.add_argument(
    "-c", "--confirm", help="Ask for confirmation before purging", action="store_true"
)

parser.add_argument(
    "--regex",
    help="Provide any regex pattern that will be performed on each found filepath with re.search()",
)


def main():
    args = parser.parse_args()
    app.purge(args)


if __name__ == "__main__":
    main()
