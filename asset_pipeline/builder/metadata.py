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

"""
The idea here is to have Schemas in the form of Python `Dataclasses` that can be converted to their equivalent as XML Element. That way we have a clear definition of what kind of field are expected and available.
Schemas can have nested Dataclasses. The conversion from Dataclass to XML Element happens in the `ElementMetadata` class and is automated.
Metadata Classes can also be generated from ElementClasses. This conversion is happening in the `from_element()` function.

The code base should only work with Dataclasses.
That means it is forbidden to import Element[] classes, the conversion from and to Dataclasses is only handled in this module.

That results in this logic:
A: Saving Metadata to file:
   -> MetadataClass -> ElementClass -> XML File on Disk
B: Loading Metadata from file:
   -> XML File on Disk -> ElementClass -> MetadataClass

"""

import inspect
import logging

from typing import List, Dict, Union, Any, Set, Optional, Tuple, TypeVar, Callable
from dataclasses import dataclass, asdict, field, fields
from pathlib import Path

from xml.etree import ElementTree as ET
from xml.etree.ElementTree import Element, ElementTree
from xml.dom import minidom

from ..asset_status import AssetStatus

logger = logging.getLogger("BSP")

M = TypeVar("M", bound="MetadataClass")
E = TypeVar("E", bound="ElementMetadata")


class FailedToInitAssetElementTree(Exception):
    pass


class FailedToInitMetadataTaskLayer(Exception):
    pass


def prettify(element: Element) -> str:
    xmlstr = ET.tostring(element, "utf-8")
    reparse: minidom.Document = minidom.parseString(xmlstr)
    pretty_str: bytes = reparse.toprettyxml(indent="    ", encoding="utf-8")
    return pretty_str.decode()


def write_element_tree_to_file(filepath: Path, tree: ElementTree) -> None:
    xmlstr = prettify(tree.getroot())
    with open(filepath.as_posix(), "w") as f:
        f.write(xmlstr)
    # tree.write(filepath.as_posix())


def write_asset_metadata_tree_to_file(
    filepath: Path, asset_metadata_tree: "MetadataTreeAsset"
) -> None:
    e_tree = ElementTreeAsset.from_metadata_cls(asset_metadata_tree)
    write_element_tree_to_file(filepath, e_tree)


def load_from_file(filepath: Path) -> ElementTree:
    return ET.parse(filepath.as_posix())


def load_asset_metadata_tree_from_file(filepath: Path) -> "MetadataTreeAsset":
    tree = load_from_file(filepath)
    asset_tree = ElementTreeAsset(element=tree.getroot())
    return MetadataTreeAsset.from_element(asset_tree)


def convert_value_for_xml(value: Any) -> Any:
    """
    Takes as input a value and converts it so it can
    be saved by to the xml format.
    """
    if type(value) == bool:
        return str(value).lower()

    # TODO: XML does not support Lists, add some functionality to handle the conversion
    # of lists in Metadata classes to elements.
    elif type(value) == list:
        return ""

    elif type(value) == Path:
        return value.as_posix()

    elif type(value) == AssetStatus:
        # If value is AssetStatus(Enum)
        # save the name as str instead of value(int), so its
        # more human readable
        return value.name

    return value


def convert_value_from_xml(element: Element) -> Any:
    """
    Takes as input an element and converts the element.text
    to a value that works for the MetadataClasses.
    """
    value = element.text
    if value == "false":
        return False
    elif value == "true":
        return True
    elif element.tag == "status":
        return getattr(AssetStatus, value)
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
        # print(f"Processing: {key}:{value}")
        # print(type(value))
        if issubclass(type(value), MetadataClass):
            convert_metadata_obj_to_elements(e, value)
        else:
            e.text = convert_value_for_xml(value)

        root_element.append(e)

    return root_element


# METADATA CLASSES
# ----------------------------------------------


class MetadataClass:
    @classmethod
    def from_dict(cls: type[M], env: Dict[str, Any]) -> M:
        return cls(
            **{k: v for k, v in env.items() if k in inspect.signature(cls).parameters}
        )

    @classmethod
    def from_element(cls: type[M], element: Element) -> M:
        d = {}
        # Take care to only take fist layer with './', otherwise we would take the
        # e.G the 'id' attribute of author and overwrite it.
        # cannot use e.iter().
        for sub_e in element.findall("./"):
            d[sub_e.tag] = convert_value_from_xml(sub_e)
        return cls.from_dict(d)


@dataclass
class MetadataUser(MetadataClass):
    """
    Tries to mirror Kitsu Asset data structure as much as possible.
    """

    id: str = "00000000-0000-0000-0000-000000000000"
    first_name: str = "Unknown"
    last_name: str = "Unknown"
    full_name: str = "Unknown"


@dataclass
class MetadataTaskLayer(MetadataClass):
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

    @classmethod
    def from_element(cls: type[M], element: Element) -> M:
        # For nested Metadata Classes we need to re-implement this.
        d = {}
        # Take care to only take fist layer with './', otherwise we would take the
        # e.G the 'id' attribute of author and overwrite it.
        # cannot use e.iter().
        for sub_e in element.findall("./"):
            if sub_e.tag == "author":
                continue
            d[sub_e.tag] = convert_value_from_xml(sub_e)

        # Convert Author element to MetadataUser.
        author = element.find(".author")
        if author == None:
            raise FailedToInitMetadataTaskLayer(
                "Expected to find 'author' element in input"
            )
        d["author"] = MetadataUser.from_element(element.author)
        return cls.from_dict(d)


@dataclass
class MetadataAsset(MetadataClass):
    """
    Tries to mirror Kitsu Asset data structure as much as possible.
    """

    name: str
    parent_id: str
    parent_name: str
    project_id: str

    version: str
    status: AssetStatus

    id: str = "00000000-0000-0000-0000-000000000000"

    # Optional.
    flags: List[str] = field(default_factory=list)

    # This is only placeholder and will be filled when creating
    task_layers_production: List[MetadataTaskLayer] = field(default_factory=list)


@dataclass
class MetadataTreeAsset(MetadataClass):
    meta_asset: MetadataAsset
    meta_task_layers: List[MetadataTaskLayer]

    @classmethod
    def from_element(cls: type[M], element: "ElementTreeAsset") -> M:
        # For nested Metadata Classes we need to re-implement this.
        d = {}
        e_asset = element.asset_element
        e_task_layers: List[ElementTaskLayer] = element.get_element_task_layers()
        d["meta_asset"] = MetadataAsset.from_element(e_asset)
        d["meta_task_layers"] = []
        for e_tl in e_task_layers:
            m_tl = MetadataTaskLayer.from_element(e_tl)
            d["meta_task_layers"].append(m_tl)

        return cls.from_dict(d)

    def get_metadata_task_layer(self, id: str) -> Optional[MetadataTaskLayer]:
        """
        Id == TaskLayer.get_id()
        """
        for tl in self.meta_task_layers:
            if tl.id == id:
                return tl
        return None

    def get_locked_metadata_task_layer(self) -> List[MetadataTaskLayer]:
        return [tl for tl in self.meta_task_layers if tl.is_locked]

    def get_locked_task_layer_ids(self) -> List[str]:
        return [tl.id for tl in self.meta_task_layers if tl.is_locked]

    def get_task_layer_ids(self) -> List[str]:
        return [tl.id for tl in self.meta_task_layers]

    def add_metadata_task_layer(self, meta_tl: MetadataTaskLayer) -> None:
        if meta_tl.id in self.get_task_layer_ids():
            logger.warning("Will not add metadata task layer. %s already in list", meta_tl.id)
            return
        self.meta_task_layers.append(meta_tl)

# ELEMENT CLASSES
# ----------------------------------------------
class ElementMetadata(Element):
    _tag: str = ""

    def __init__(self, element: Optional[Element] = None) -> None:
        super().__init__(self._tag)
        # If we initialize with an element, we basically want to
        # copy the content of the element in to an instance of type
        # ElementMetadata to benefit from additional functions.
        if element:
            for child in element:
                self.append(child)

    @classmethod
    def from_metadata_cls(cls, meta_class: M) -> E:
        # If metaclass has an ID field
        # Add a "id" attribute to the element for convenient
        # querying.
        instance = cls()
        if hasattr(meta_class, "id") and meta_class.id:
            instance.attrib.update({"id": meta_class.id})

        # This function makes sure that the input  MetadataClass
        # will be converted to an element tree. It also handles
        # nested MetadataClasses respectively.
        convert_metadata_obj_to_elements(instance, meta_class)
        return instance


class ElementUser(ElementMetadata):
    _tag: str = "User"


class ElementAsset(ElementMetadata):
    _tag: str = "Asset"

    @property
    def task_layers_production(self) -> Element:
        return self.find(".task_layers_production")


class ElementTaskLayer(ElementMetadata):
    _tag: str = "TaskLayer"

    @classmethod
    def from_metadata_cls(cls, meta_class: MetadataTaskLayer) -> "ElementTaskLayer":

        instance = super().from_metadata_cls(meta_class)

        # Update Author field.
        e = instance.find(".author")
        e.text = e.find(".full_name").text
        return instance

    @property
    def author(self) -> Optional[Element]:
        return self.find(".author")


class ElementTreeAsset(ElementTree):
    @classmethod
    def from_metadata_cls(
        cls, meta_tree_asset: MetadataTreeAsset
    ) -> "ElementTreeAsset":
        # Create Asset Element and append to root.
        asset_element: ElementAsset = ElementAsset.from_metadata_cls(
            meta_tree_asset.meta_asset
        )

        # Create ProductionTaskLayers Element
        prod_task_layers = asset_element.task_layers_production

        # TODO: I DONT UNDERSTAND:
        # For some reasons the task_layers_production entry will
        # be duplicated if we just use
        # prod_task_layers = asset_element.task_layers_production
        # no idea why, we need to first delete it and add it again???
        for i in asset_element:
            if i.tag == "task_layers_production":
                asset_element.remove(i)

        prod_task_layers = Element("task_layers_production")

        # Need to check for None, if element empty it is falsy.
        if prod_task_layers == None:
            raise FailedToInitAssetElementTree(
                f"Failed to find  task_layers_production child in ElementAsset Class."
            )

        # Append all meta task layers to it.
        for meta_tl in meta_tree_asset.meta_task_layers:
            tl_element = ElementTaskLayer.from_metadata_cls(meta_tl)
            prod_task_layers.append(tl_element)

        asset_element.append(prod_task_layers)

        return cls(asset_element)

    def get_element_task_layers(self) -> List[ElementTaskLayer]:
        l: List[ElementTaskLayer] = []
        for e in self.findall(".//TaskLayer"):
            # We need to pass e as ElementTree otherwise we won't receive
            # a full tree copy of all childrens recursively.
            e_tl = ElementTaskLayer(element=e)
            l.append(e_tl)

        return l

    def get_task_layer(self, id: str) -> Optional[Element]:
        return self.find(f".//TaskLayer[@id='{id}']")

    @property
    def asset_element(self) -> Element:
        return self.getroot()
