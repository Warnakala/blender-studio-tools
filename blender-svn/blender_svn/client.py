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

from . import wheels

# This will load the dateutil and svn wheel file.
wheels.preload_dependencies()

from svn.local import LocalClient

from typing import List, Dict, Union, Any, Set, Optional, Tuple
from pathlib import Path

logger = logging.getLogger("SVN")

LOCAL_CLIENT: LocalClient = None


def init_local_client(svn_root_path: Path) -> LocalClient:
    global LOCAL_CLIENT

    # If not .svn in path invalid.
    if not svn_root_path.joinpath(".svn").exists():
        logger.warning(
            "Failed to init local SVN client. Found not SVN repo in: %s",
            svn_root_path.as_posix(),
        )
        LOCAL_CLIENT = None
        return

    LOCAL_CLIENT = LocalClient(svn_root_path.as_posix())
    logger.info("Initiated local SVN client: %s", LOCAL_CLIENT)
