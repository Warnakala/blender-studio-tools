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
from types import ModuleType

from pathlib import Path

logger = logging.getLogger("BSP")


class TaskLayer:

    name: str = ""
    description: str = ""
    order: int = -1

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
        return bool(cls.name and cls.order >= 0)

    def __repr__(self) -> str:
        return f"TaskLayer{self.name}"

    # Private Interface to be implemented by Production Config
    # -------------------------------------------------------#


class TaskLayerConfig:
    """
    This Class holds a TaskLayer and additional Information that
    determine how this TaskLayer is handeled during build.
    For example .use controls if TaskLayer should be used for build.
    """

    def __init__(self, task_layer: type[TaskLayer]):
        self._task_layer = task_layer
        self._use: bool = False

    @property
    def task_layer(self) -> type[TaskLayer]:
        return self._task_layer

    @property
    def use(self) -> bool:
        return self._use

    @use.setter
    def use(self, value: bool) -> None:
        self._use = value

    def reset(self) -> None:
        self._use = False

    def __repr__(self) -> str:
        return f"{self.task_layer.name}(use: {self.use})"


class TaskLayerAssembly:

    """
    This Class holds all TaskLayers relevant for build.
    Each TaskLayer is stored as TaskLayerConfig object which provides
    the built additional information.
    """

    def __init__(self, task_layers: List[type[TaskLayer]]):
        # Create a dictionary data structure here, so we can easily control
        # from within Blender by string which TaskLayers to enable and disable for built.
        # As key we will use the class.__name__ attribute of each TaskLayer. (Should be unique)
        self._task_layer_config_dict: Dict[str, TaskLayerConfig] = {}

        # For each TaskLayer create a TaskLayerConfig and add entry in
        # dictionary.
        for task_layer in task_layers:

            # Make sure that for whatever reason there are no 2 identical TaskLayer.
            if task_layer.__name__ in self._task_layer_config_dict:

                self._task_layer_config_dict.clear()
                raise Exception(
                    f"Detected 2 TaskLayers with the same Class name. [{task_layer.__name__}]"
                )

            self._task_layer_config_dict[task_layer.__name__] = TaskLayerConfig(
                task_layer
            )

    def get_task_layer_config(self, key: str) -> TaskLayerConfig:
        return self._task_layer_config_dict[key]

    @property
    def task_layer_config_dict(self) -> Dict[str, TaskLayerConfig]:
        return self._task_layer_config_dict

    @property
    def task_layer_configs(self) -> List[TaskLayerConfig]:
        return list(self._task_layer_config_dict.values())

    @property
    def task_layers(self) -> List[type[TaskLayer]]:
        return list(t.task_layer for t in self.task_layer_configs)

    @property
    def task_layer_names(self) -> List[str]:
        return [l.name for l in self.task_layers]

    def as_blender_enum(self) -> List[Tuple[str, str, str]]:
        """
        Returns data structure that works for Blender Enums.
        [(TaskLayer Class Name, TaskLayer Name, TaskLayer Description)]
        """

        l = []
        for key, value in self._task_layer_configs.items():
            t = (key, value.task_layer.name, value.task_layer.description)
            l.append(t)
        return l

    def get_task_layer_orders(self, only_used: bool = False) -> List[int]:
        """
        Returns a list of all TaskLayers.order values.
        """
        if not only_used:
            return [t.order for t in self.task_layers]
        else:
            return [tc.task_layer.order for tc in self.task_layer_configs if tc.use]

    def reset_task_layer_configs(self) -> None:
        for tc in self.task_layer_configs:
            tc.reset()

    def __repr__(self) -> str:
        body = f"{', '.join([str(t) for t in self.task_layer_configs])}"
        return f"TaskLayerAssembly: ({body})"

    def __bool__(self) -> bool:
        return bool(self._task_layer_config_dict)
