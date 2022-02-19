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

import inspect
import logging

from typing import List, Dict, Union, Any, Set, Optional, Tuple, TypeVar, Callable
from dataclasses import dataclass, asdict, field, fields
from pathlib import Path
from enum import Enum, auto

from xml.etree import ElementTree
from xml.etree.ElementTree import Element
from xml.dom import minidom

from .task_layer import TaskLayer
from .asset_status import AssetStatus

logger = logging.getLogger("BSP")

M = TypeVar("M", bound="MetadataClass")


def prettify(element: Element) -> str:
    xmlstr = ElementTree.tostring(element, "utf-8")
    reparse: minidom.Document = minidom.parseString(xmlstr)
    pretty_str: bytes = reparse.toprettyxml(indent="    ", encoding="utf-8")
    return pretty_str.decode()


def write_tree_to_file(filepath: Path, tree: ElementTree.ElementTree) -> None:
    xmlstr = prettify(tree.getroot())
    with open(filepath.as_posix(), "w") as f:
        f.write(xmlstr)
    # tree.write(filepath.as_posix())


def convert_value_for_xml(value: Any) -> Any:
    if type(value) == bool:
        return str(value).lower()
    return value


def convert_metadata_obj_to_elements(
    root_element: Element, metadata_class: M
) -> Element:
    """
    This function makes sure that the input MetadataClass
    will be converted to an element tree. It also handles
    nested MetadataClasses respectively. The resulting tree of elements
    will be appended to the input root_element.
    """
    # asdict() recursively converts all dataclasses to dicts.
    # even nested ones. https://docs.python.org/3/library/dataclasses.html#dataclasses.asdict
    # That's why we need to do it this way, otherwise the issubclass() check for MetadataClass
    # won't work.
    d = dict(
        (field.name, getattr(metadata_class, field.name))
        for field in fields(metadata_class)
    )
    for key, value in d.items():

        e = Element(key)
        print(f"Processing: {key}:{value}")
        # print(type(value))
        if issubclass(type(value), MetadataClass):
            convert_metadata_obj_to_elements(e, value)
        else:
            e.text = convert_value_for_xml(value)
            root_element.append(e)

    return root_element


# The idea here is to have Schemas in the form of Python Dataclasses that can be converted to their equivalent as XML Element.
# Schemas can have nested Dataclasses. The conversion happens in MetadataElement and can handle that.


@dataclass
class MetadataClass:
    @classmethod
    def from_dict(cls: type[M], env: Dict[str, Any]) -> M:
        return cls(
            **{k: v for k, v in env.items() if k in inspect.signature(cls).parameters}
        )


@dataclass
class MetadataUser(MetadataClass):
    """
    Tries to mirror Kitsu Asset data structure as much as possible.
    """

    id: str
    first_name: str
    last_name: str
    full_name: str


@dataclass
class MetaDataTaskLayer(MetadataClass):
    id: str
    name: str

    source_path: str
    source_revision: str
    is_locked: bool

    created_at: str
    updated_at: str
    author: MetadataUser
    software_hash: str
    hostname: str

    # Optional.
    flags: List[str] = field(default_factory=list)


@dataclass
class MetadataAsset(MetadataClass):
    """
    Tries to mirror Kitsu Asset data structure as much as possible.
    """

    id: str
    name: str
    project_id: str
    version: str
    # status: AssetStatus

    # Optional.
    flags: List[str] = field(default_factory=list)
    task_layers: List[MetaDataTaskLayer] = field(default_factory=list)


class MetadataElement(Element):
    _tag: str = ""

    def __init__(self, meta_class: MetadataClass) -> None:
        super().__init__(self._tag)

        # This function makes sure that the input  MetadataClass
        # will be converted to an element tree. It also handles
        # nested MetadataClasses respectively.
        convert_metadata_obj_to_elements(self, meta_class)


class UserElement(MetadataElement):
    _tag: str = "User"

    def __init__(self, meta_class: MetadataUser) -> None:
        super().__init__(meta_class)


class AssetElement(MetadataElement):
    _tag: str = "Asset"

    def __init__(self, meta_class: MetadataAsset) -> None:
        super().__init__(meta_class)


class TaskLayerElement(MetadataElement):
    _tag: str = "TaskLayer"

    def __init__(self, meta_class: MetaDataTaskLayer) -> None:
        super().__init__(meta_class)


class AssetMetadataTree(ElementTree.ElementTree):
    def __init__(
        self, meta_asset: MetadataAsset, meta_task_layers: List[MetaDataTaskLayer]
    ):
        # Create Asset Element and append to root.
        asset_element = AssetElement(meta_asset)

        super().__init__(asset_element)

        # Create ProductionTaskLayers Element
        prod_task_layers = Element("ProductionTaskLayers")

        # Append all meta task layers to it.
        for meta_tl in meta_task_layers:
            tl_element = TaskLayerElement(meta_tl)
            prod_task_layers.append(tl_element)

        self.getroot().append(prod_task_layers)
