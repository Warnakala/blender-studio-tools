# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

# <pep8 compliant>

# This file was made by Jeroen Bakker in the shot-builder repository:
# https://developer.blender.org/diffusion/BSTS/browse/master/shot-builder/shot_builder/sys_utils
import logging
import subprocess

from pathlib import Path
from typing import List, Dict, Union, Any, Optional

logger = logging.getLogger("BSP")

import bpy


class BuilderBlenderStarter:

    path: Path = Path(bpy.app.binary_path)
    publish_script: Path = Path(__file__).parent.joinpath("scripts/push.py")

    @classmethod
    def start_publish(cls, filepath: Path, pickle_path: Path) -> None:
        cmd_str = (
            f"{cls.path.as_posix()} {filepath.as_posix()}"
            " -b"
            # " --factory-startup"
            # f" --addons blender_kitsu,asset_pipeline"
            f" -P {cls.publish_script.as_posix()}"
            f" -- {pickle_path.as_posix()}"
        )
        popen = subprocess.Popen(cmd_str, shell=True)
        popen.wait()
