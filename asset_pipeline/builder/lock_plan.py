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

from typing import List, Dict, Union, Any, Set, Optional, Tuple

from .task_layer import TaskLayer

from ..asset_files import AssetPublish

logger = logging.getLogger("BSP")


class TaskLayerLockPlan:
    """
    When creating a new incrementation of an asset publish we need to somehow store
    from which previous asset publishes which task layer will be locked.
    This is automatically calculated, but this information should also be displayed in the UI.
    This class helps with that. This class can also actually lock the task layers.
    """

    def __init__(
        self, asset_publish: AssetPublish, task_layers_to_lock: List[TaskLayer]
    ):
        self._asset_publish = asset_publish
        self._task_layers_to_lock = task_layers_to_lock

    @property
    def asset_publish(self) -> AssetPublish:
        return self._asset_publish

    @property
    def task_layers_to_lock(self) -> List[TaskLayer]:
        return self._task_layers_to_lock

    def get_task_layer_ids_to_lock(self) -> List[str]:
        return [tl.get_id() for tl in self.task_layers_to_lock]

    def lock(self) -> None:

        """
        Sets the is_locked attribute of each TaskLayer to lock in writes
        metadata to disk.
        """
        for meta_task_layer in self.asset_publish.metadata.meta_task_layers:

            if (
                not meta_task_layer.is_locked
                and meta_task_layer.id in self.get_task_layer_ids_to_lock()
            ):
                meta_task_layer.is_locked = True

        self.asset_publish.write_metadata()
