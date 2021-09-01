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
