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

from __future__ import annotations
import bpy
from dataclasses import asdict, dataclass, field
from typing import Optional, Dict, List


def is_area_of_type(area: bpy.types.Area, type: str) -> None:
    if area.type != type:
        raise ValueError(f"Area is of type {area.type}. Expected {type}.")


class FileBrowserState:
    def __init__(self, area: Optional[bpy.types.Area] = None):
        if area:
            is_area_of_type(area, "FILE_BROWSER")
            self.space_data = SpaceData.from_area(area)
            self.params = FbParams.from_area(area)
        else:
            self.space_data = SpaceData()
            self.params = FbParams()

    def apply_to_area(self, area: bpy.types.Area) -> None:
        self.space_data.apply_to_area(area)
        self.params.apply_to_area(area)


class TimelineState:
    def __init__(self, area: Optional[bpy.types.Area] = None):
        if area:
            is_area_of_type(area, "DOPESHEET_EDITOR")
            self.space_data = SpaceData.from_area(area)
        else:
            self.space_data = SpaceData()
            self.space_data.show_region_ui = False

    def apply_to_area(self, area: bpy.types.Area) -> None:
        self.space_data.apply_to_area(area)


@dataclass
class SpaceData:
    show_region_header: bool = False
    show_region_tool_props: bool = False
    show_region_toolbar: bool = False  # Toolbar on the right.
    show_region_ui: bool = True  # File path input bar.

    @classmethod
    def from_area(cls, area: bpy.types.Area) -> SpaceData:
        data_dict = asdict(cls())
        space = area.spaces.active

        for key in data_dict:
            if hasattr(space, key):
                data_dict[key] = getattr(space, key)

        return cls(**data_dict)

    def apply_to_area(self, area: bpy.types.Area) -> None:
        data_dict = asdict(self)
        space = area.spaces.active

        for key, value in data_dict.items():
            if hasattr(space, key):
                setattr(space, key, value)


@dataclass
class FbParams:
    directory: str = ""
    display_type: str = "THUMBNAIL"
    display_size: str = "NORMAL"
    use_filter: bool = True
    use_filter_image: bool = True
    use_filter_folder: bool = True
    use_filter_movie: bool = True
    use_filter_text: bool = True
    use_filter_script: bool = True
    use_filter_asset_only: bool = False
    use_filter_backup: bool = False
    use_filter_blender: bool = False
    use_filter_blendid: bool = False
    use_filter_font: bool = False
    use_filter_sound: bool = True
    use_filter_volume: bool = False
    use_sort_invert: bool = False

    @classmethod
    def from_area(cls, area: bpy.types.Area) -> FbParams:
        is_area_of_type(area, "FILE_BROWSER")

        data_dict = asdict(cls())
        params = area.spaces.active.params

        for key in data_dict:

            # Catch special case directory.
            if key == "directory":
                data_dict[key] = str(getattr(params, key).decode("utf-8"))

            elif hasattr(params, key):
                data_dict[key] = getattr(params, key)

        return cls(**data_dict)

    def apply_to_area(self, area: bpy.types.Area) -> None:
        is_area_of_type(area, "FILE_BROWSER")

        data_dict = asdict(self)
        params = area.spaces.active.params

        for key, value in data_dict.items():

            # Catch special case directory.
            if key == "directory":
                setattr(params, key, value.encode("utf-8"))

            elif hasattr(params, key):
                setattr(params, key, value)
