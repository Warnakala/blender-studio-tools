# ***** BEGIN GPL LICENSE BLOCK *****
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
# ***** END GPL LICENCE BLOCK *****
#
# (c) 2021, Blender Foundation - Paul Golter

from pathlib import Path
import bpy

PATTERN_FRAME_COUNTER = r"\d+$"

EXT_MOVIE = [
    ".avi",
    ".flc",
    ".mov",
    ".movie",
    ".mp4",
    ".m4v",
    ".m2v",
    ".m2t",
    ".m2ts",
    ".mts",
    ".ts",
    ".mv",
    ".avs",
    ".wmv",
    ".ogv",
    ".ogg",
    ".r3d",
    ".dv",
    ".mpeg",
    ".mpg",
    ".mpg2",
    ".vob",
    ".mkv",
    ".flv",
    ".divx",
    ".xvid",
    ".mxf",
    ".webm",
]

EXT_IMG = [
    ".jpg",
    ".png",
    ".exr",
    ".tga",
    ".bmp",
    ".jpeg",
    ".sgi",
    ".rgb",
    ".rgba",
    ".tif",
    ".tiff",
    ".tx",
    ".hdr",
    ".dpx",
    ".cin",
    ".psd",
    ".pdd",
    ".psb",
]

EXT_TEXT = [
    ".txt",
    ".glsl",
    ".osl",
    ".data",
    ".pov",
    ".ini",
    ".mcr",
    ".inc",
    ".fountain",
    ".rst",
    ".ass",
]

EXT_SCRIPT = [".py"]


def get_config_file() -> Path:
    path = bpy.utils.user_resource("CONFIG", path="media_viewer", create=True)
    return Path(path) / "config.json"


FOLDER_HISTORY_STEPS: int = 10
