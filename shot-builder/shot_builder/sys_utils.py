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

import sys
import pathlib
from typing import List

class SystemPathInclude:

    """
    Resource class to temporary include system paths to `sys.paths`.

    Usage:
        ```
        paths = [pathlib.Path("/home/guest/my_python_scripts")]
        with SystemPathInclude(paths) as t:
            import my_module
            reload(my_module)
        ```

    It is possible to nest multiple SystemPathIncludes.
    """
    def __init__(self, paths_to_add: List[pathlib.Path]):
        # TODO: Check if all paths exist and are absolute.
        self.__paths = paths_to_add
        self.__original_sys_path = None

    def __enter__(self):
        self.__original_sys_path = sys.path
        for path_to_add in self.__paths:
            # Do not add paths that are already in the sys path.
            # Report this to the logger as this might indicate wrong usage.
            path_to_add_str = str(path_to_add)
            if path_to_add_str in self.__original_sys_path:
                logger.warn(f"{path_to_add_str} already added to `sys.path`")
                continue
            sys.path.append(path_to_add_str)
    
    def __exit__(self, exc_type, exc_value, exc_traceback):
        sys.path = self.__original_sys_path
