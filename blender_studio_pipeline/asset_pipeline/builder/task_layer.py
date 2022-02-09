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

import logging

from typing import List, Dict, Union, Any, Set, Optional
from types import ModuleType

from pathlib import Path

logger = logging.getLogger(__name__)


class TaskLayer:

    name: str = ""

    def __init__(self):
        self.source_path: str = ""
        self.source_revision: str = ""
        self.is_locked: bool = False

        # created_at: str
        # updated_at: str
        # author: Author
        # software_hash: str
        # workstation: str
        # flags: List[str]

    @classmethod
    def is_valid(cls) -> bool:
        return bool(cls.name)

    def __repr__(self) -> str:
        return f"TaskLayer{self.name}"

    # Private Interface to be implemented by Production Config
    # -------------------------------------------------------#
