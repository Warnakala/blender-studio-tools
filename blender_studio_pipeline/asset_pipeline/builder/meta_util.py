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

import socket
from dataclasses import asdict
from datetime import datetime
from typing import List, Dict, Union, Any, Set, Optional, Tuple
from pathlib import Path

import bpy

from .. import constants
from .task_layer import TaskLayer
from .asset_status import AssetStatus
from .metadata import MetaDataTaskLayer, MetadataUser

from blender_kitsu import cache
from blender_kitsu.types import User

logger = logging.getLogger("BSP")


def init_meta_task_layer(task_layer: type[TaskLayer]) -> MetaDataTaskLayer:

    d: Dict[str, Any] = {}
    time = datetime.now()
    user: User = cache.user_active_get()

    d["id"] = task_layer.__name__
    d["name"] = task_layer.name

    d["source_revision"] = ""  # TODO:
    d["source_path"] = bpy.data.filepath  # TODO:
    d["is_locked"] = False

    d["created_at"] = time.strftime(constants.TIME_FORMAT)
    d["updated_at"] = time.strftime(constants.TIME_FORMAT)
    d["author"] = MetadataUser.from_dict(asdict(user))
    d["software_hash"] = bpy.app.build_hash.decode()
    d["hostname"] = socket.gethostname()

    return MetaDataTaskLayer.from_dict(d)
