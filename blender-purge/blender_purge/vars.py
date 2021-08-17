import os
from pathlib import Path

PURGE_PATH = Path(os.path.abspath(__file__)).parent.joinpath("purge.py")
CHECK_PATH = Path(os.path.abspath(__file__)).parent.joinpath("check.py")

BLENDER_PATH = "/media/data/blender_guest/cmake_release/bin/blender"
PROJECT_PATH = "/media/data/sprites"
PURGE_AMOUNT = 2
