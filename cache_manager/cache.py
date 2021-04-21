import json
import os
import contextlib

from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Union, Optional, Tuple, Dict
from copy import deepcopy

import bpy

from . import prefs, props, cmglobals, opsdata
from .logger import LoggerFactory, gen_processing_string, log_new_lines

logger = LoggerFactory.getLogger(__name__)


_CACHECONFIG_TEMPL: Dict[str, Any] = {
    "meta": {"name": "", "creation_date": ""},
    "libs": {},  # {filepath_to_lib: _LIBDICT_TEMPL}
}
_LIBDICT_TEMPL: Dict[str, Any] = {
    "data_from": {"collections": {}},  # {'colname': {'cachefile': cachepath}}
    "animation_data": {},
}
_OBJECTDICT_TEMPL = {"type": "", "drivers": []}
_DRIVERDICT_TEMPL = {"data_path": "", "value": []}

_DATE_FORMAT = "%Y-%m-%dT%H:%M:%S"


def gen_filename_collection(collection: bpy.types.Collection) -> str:
    return f"{collection.name}.abc"


def gen_cachepath_collection(
    collection: bpy.types.Collection, context: bpy.types.Context
) -> Path:
    addon_prefs = prefs.addon_prefs_get(context)
    cachedir_path = Path(addon_prefs.cachedir_path)

    if not cachedir_path:
        raise ValueError(
            f"Failed to generate cachepath for collection: {collection.name}. Invalid cachepath: {str(cachedir_path)}"
        )
    return cachedir_path.joinpath(gen_filename_collection(collection)).absolute()


def is_valid_cache_object(obj: bpy.types.Object) -> bool:
    if obj.type in cmglobals.VALID_OBJECT_TYPES and obj.name.startswith("GEO"):
        return True
    return False


def get_valid_cache_objects(collection: bpy.types.Collection) -> List[bpy.types.Object]:
    object_list = [obj for obj in collection.all_objects if is_valid_cache_object(obj)]
    return object_list


def get_current_time_string(date_format: str) -> str:
    now = datetime.now()
    current_time_string = now.strftime(date_format)
    return current_time_string


def read_json(filepath: Path) -> Any:
    with open(filepath.as_posix(), "r") as file:
        json_dict = json.loads(file.read())
        return json_dict


def save_as_json(data: Any, filepath: Path) -> None:
    with open(filepath.as_posix(), "w+") as file:
        json.dump(data, file, indent=4)


@contextlib.contextmanager
def temporary_current_frame(context):
    """Allows the context to set the scene current frame, restores it on exit.

    Yields the initial current frame, so it can be used for reference in the context.
    """
    current_frame = context.scene.frame_current
    try:
        yield current_frame
    finally:
        context.scene.frame_current = current_frame


def _get_coll_to_lib_mapping(_json_obj: Dict[str, Any]) -> Dict[str, str]:
    remapping = {}
    for libfile in _json_obj["libs"]:
        for coll_str in _json_obj["libs"][libfile]["data_from"]["collections"]:
            remapping[coll_str] = libfile
    return remapping


def _get_obj_to_lib_mapping(_json_obj: Dict[str, Any]) -> Dict[str, str]:
    remapping = {}
    for libfile in _json_obj["libs"]:
        for obj_str in _json_obj["libs"][libfile]["animation_data"]:
            remapping[obj_str] = libfile
    return remapping


class CacheConfig:
    def __init__(self, filepath: Path):
        self.filepath = filepath
        self._json_obj: List[Dict[str, Any]] = []

        self.load(filepath)

    def load(self, filepath: Path) -> None:
        self.filepath = filepath
        self._json_obj = read_json(self.filepath)
        logger.info("Loaded cacheconfig from: %s", filepath.as_posix())

    @property
    def json_obj(self) -> List[Dict[str, Any]]:
        return self._json_obj

    def import_collections(
        self, context: bpy.types.Context, link: bool = True
    ) -> List[bpy.types.Collection]:

        # list of collections to track which ones got imported
        colls: List[bpy.types.Collection] = []

        for libfile in self._json_obj["libs"]:

            libpath = Path(libfile)
            colldata = self._json_obj["libs"][libfile]["data_from"]["collections"]

            with bpy.data.libraries.load(
                libpath.as_posix(), relative=True, link=link
            ) as (
                data_from,
                data_to,
            ):

                for coll_name in colldata:
                    cachefile = colldata[coll_name]["cachefile"]

                    if coll_name not in data_from.collections:
                        logger.warning(
                            "Failed to import collection %s from %s. Doesn't exist in file.",
                            coll_name,
                            libpath.as_posix(),
                        )
                        continue

                    if coll_name in data_to.collections:
                        logger.warning("Collection %s already in blendfile.", coll_name)
                        continue

                    data_to.collections.append(coll_name)
                    logger.info(
                        "Appended collection: %s from library: %s",
                        coll_name,
                        libpath.as_posix(),
                    )

            # link collections in current scene and add cm.cachfile property
            for coll_name in colldata:
                cachefile = colldata[coll_name]["cachefile"]

                """
                try:
                    bpy.context.scene.collection.children.link(coll)
                except RuntimeError:
                    logger.warning("Collection %s already in blendfile.", coll_name)
                """
                # instance collection to scene so adding override works properly
                bpy.ops.object.collection_instance_add(collection=coll_name)

                # deselect all
                bpy.ops.object.select_all(action="DESELECT")

                # needs active object (coll instance)
                obj = bpy.data.objects[coll_name]
                context.view_layer.objects.active = obj

                # add lib override
                bpy.ops.object.make_override_library()

                # get collection by name
                coll = bpy.data.collections[coll_name]

                # set cm.cachefile property
                coll.cm.cachefile = cachefile
                self._add_coll_to_cm_collections(context, coll)
                colls.append(coll)

        return colls

    def import_animation_data(self, colls: List[bpy.types.Collection]) -> None:

        frame_in = self._json_obj["meta"]["frame_start"]
        frame_out = self._json_obj["meta"]["frame_end"]

        log_new_lines(1)
        logger.info("-START- Importing Animation Data")

        coll_to_lib_mapping = _get_coll_to_lib_mapping(self._json_obj)

        for coll in colls:
            log_new_lines(1)
            logger.info("%s", gen_processing_string(coll.name + " animation data"))

            libfile = coll_to_lib_mapping[coll.name]

            # if there is no animation_data for this libfile skip
            if not self._json_obj["libs"][libfile]["animation_data"]:
                logger.info("No animation data available for collection %s", coll.name)
                continue

            # for each object in this lib file that has animation data set keyframes on each frame
            for obj_str in self._json_obj["libs"][libfile]["animation_data"]:

                # get object from string
                obj = bpy.data.objects[obj_str]

                # disable drivers
                opsdata.disable_drivers([obj])

                # only if obj in the filter collections
                if not coll in obj.users_collection:
                    continue

                driven_props_list = []  # for log
                # get property that was driven and set keyframes
                for driver_dict in self._json_obj["libs"][libfile]["animation_data"][
                    obj_str
                ]["drivers"]:

                    data_path_str = driver_dict["data_path"]
                    # for log
                    driven_props_list.append(data_path_str)

                    # insert keyframe for frames in json_obj
                    for frame in range(frame_in, frame_out + 1):

                        # get value to set prop to
                        prop_value = driver_dict["value"][frame - frame_in]

                        deliminater = "."
                        # set property to value
                        if data_path_str.startswith("["):
                            deliminater = ""
                        exec(
                            f'bpy.data.objects["{obj_str}"]{deliminater}{data_path_str}={prop_value}'
                        )
                        obj.keyframe_insert(data_path=data_path_str, frame=frame)

                        """
                        print(
                            f"Frame {frame}: Keying {obj.name} with value: {prop_value}"
                        )
                        """
                logger.info(
                    "%s imported animation (%s, %s) for props: %s",
                    obj.name,
                    frame_in,
                    frame_out,
                    " ,".join(driven_props_list),
                )
        log_new_lines(1)
        logger.info("-END- Importing Animation Data")

    def _add_coll_to_cm_collections(
        self, context: bpy.types.Context, coll: bpy.types.Collection
    ) -> bpy.types.Collection:
        scn = context.scene
        if coll.name in [c[1].name for c in scn.cm_collections_import.items()]:
            logger.info("%s already in the cache collections list", coll.name)

        else:
            item = scn.cm_collections_import.add()
            item.coll_ptr = coll
            item.name = item.coll_ptr.name
            scn.cm_collections_import_index = len(scn.cm_collections_import) - 1

            logger.info("%s added to cache collections list", item.name)

        return coll

    def _is_filepath(self) -> bool:
        if not self.filepath:
            logger.error("CacheConfig has no valid filepath. Not loaded yet?")
            return False

        if not self.filepath.exists():
            logger.error("CacheConfig filepath does not exists on disk.")
            return False

        return True


class CacheConfigFactory:
    @classmethod
    def gen_config_from_colls(
        cls,
        context: bpy.types.Context,
        colls: List[bpy.types.Collection],
        filepath: Path,
    ) -> CacheConfig:

        _json_obj: Dict[str, Any] = deepcopy(_CACHECONFIG_TEMPL)

        # if cacheconfig already exists load it and update entries
        if filepath.exists():
            logger.info(
                "Cacheconfig already exists: %s. Will update entries.",
                filepath.as_posix(),
            )
            _json_obj = read_json(filepath)

        log_new_lines(2)
        noun = "Updating" if filepath.exists else "Creating"
        logger.info("-START- %s CacheConfig", noun)

        # populate metadata
        cls._populate_metadata(context, _json_obj)

        # poulate cacheconfig with libs based on collections
        cls._populate_libs(context, colls, _json_obj)

        # populate collections with animation data
        objects_with_anim = cls._populate_with_animation_data(colls, _json_obj)

        # get drive values for each frame
        cls._read_and_store_animation_data(context, objects_with_anim, _json_obj)

        # save json obj to disk
        save_as_json(_json_obj, filepath)
        logger.info("Generated cacheconfig and saved to: %s", filepath.as_posix())

        log_new_lines(1)
        logger.info("-END- %s CacheConfig", noun)

        return CacheConfig(filepath)

    @classmethod
    def _populate_metadata(
        cls, context: bpy.types.Context, _json_obj: Dict[str, Any]
    ) -> Dict[str, Any]:

        _json_obj["meta"]["name"] = Path(bpy.data.filepath).name
        _json_obj["meta"]["creation_date"] = get_current_time_string(_DATE_FORMAT)
        _json_obj["meta"]["frame_start"] = context.scene.frame_start
        _json_obj["meta"]["frame_end"] = context.scene.frame_end
        logger.info("Created metadata")
        return _json_obj

    @classmethod
    def _populate_libs(
        cls,
        context: bpy.types.Context,
        colls: List[bpy.types.Collection],
        _json_obj: Dict[str, Any],
    ) -> Dict[str, Any]:

        # get librarys
        for coll in colls:
            lib = coll.override_library.reference.library
            libfile = Path(os.path.abspath(bpy.path.abspath(lib.filepath))).as_posix()

            # gen libfile key in _json_obj["libs"] if not existent
            if libfile not in _json_obj["libs"]:
                _json_obj["libs"][libfile] = deepcopy(_LIBDICT_TEMPL)

            # gen collk key in _json_obj["libs"][libfile]['data_from']["collections"] if not existent
            if coll.name not in _json_obj["libs"][libfile]["data_from"]["collections"]:
                _json_obj["libs"][libfile]["data_from"]["collections"][coll.name] = {}

            # create collection dict based on this collection
            _col_dict = {
                "cachefile": gen_cachepath_collection(coll, context).as_posix(),
            }

            # append collection dict to libdict
            _json_obj["libs"][libfile]["data_from"]["collections"][
                coll.name
            ] = _col_dict

        # log
        for libfile in _json_obj["libs"]:
            logger.info(
                "Gathered libfile: %s with collections: %s",
                libfile,
                ", ".join(_json_obj["libs"][libfile]["data_from"]["collections"]),
            )

        return _json_obj

    @classmethod
    def _populate_with_animation_data(
        cls,
        colls: List[bpy.types.Collection],
        _json_obj: Dict[str, Any],
    ) -> List[bpy.types.Object]:

        objects_with_anim: List[bpy.types.Object] = []

        for coll in colls:
            lib = coll.override_library.reference.library
            libfile = Path(os.path.abspath(bpy.path.abspath(lib.filepath))).as_posix()

            # loop over all objects in that collection
            for obj in coll.all_objects:

                is_anim = False

                if not is_valid_cache_object(obj):
                    continue

                if not obj.animation_data:
                    continue

                if not obj.animation_data.drivers:
                    continue

                for driver in obj.animation_data.drivers:

                    # don't export animation for vis of modifiers
                    data_path = driver.data_path.split(".")
                    if len(data_path) > 1:
                        if data_path[0].startswith("modifiers"):
                            if data_path[-1] in opsdata.DRIVERS_MUTE:
                                continue

                    driven_value = driver.id_data.path_resolve(driver.data_path)

                    # gen obj.name key in _json_obj["animation_data"] if not existent
                    if obj.name not in _json_obj["libs"][libfile]["animation_data"]:
                        _json_obj["libs"][libfile]["animation_data"][
                            obj.name
                        ] = deepcopy(_OBJECTDICT_TEMPL)

                    # append driver dict
                    object_key = _json_obj["libs"][libfile]["animation_data"][obj.name]
                    drivers_key = object_key["drivers"]

                    # set type
                    object_key["type"] = str(obj.type)

                    # gen driver dict
                    driver_dict = deepcopy(_DRIVERDICT_TEMPL)
                    driver_dict["data_path"] = driver.data_path
                    drivers_key.append(driver_dict)

                    if not is_anim:
                        is_anim = True

                if is_anim:
                    objects_with_anim.append(obj)
        # log
        logger.info("Populated CacheConfig with animated properties.")

        return objects_with_anim

    @classmethod
    def _read_and_store_animation_data(
        cls,
        context: bpy.types.Context,
        objects: List[bpy.types.Object],
        _json_obj: Dict[str, Any],
    ) -> Dict[str, Any]:

        # get driver values for each frame
        fin = context.scene.frame_start
        fout = context.scene.frame_end
        frame_range = range(fin, fout + 1)

        remapping = _get_obj_to_lib_mapping(_json_obj)

        with temporary_current_frame(context) as original_curframe:
            for frame in frame_range:
                context.scene.frame_set(frame)
                logger.info("Storing animation data for frame %i", frame)

                for obj in objects:
                    libfile = remapping[obj.name]
                    for driver_dict in _json_obj["libs"][libfile]["animation_data"][
                        obj.name
                    ]["drivers"]:

                        data_path_str = driver_dict["data_path"]
                        driven_value = obj.path_resolve(data_path_str)
                        driver_dict["value"].append(driven_value)

        # log
        logger.info(
            "Stored data for animated properties (%i, %i).",
            fin,
            fout,
        )
        return _json_obj

    @classmethod
    def load_config_from_file(cls, filepath: Path) -> CacheConfig:
        if not filepath.exists():
            raise ValueError(
                f"Failed to load config. Path does not exist: {filepath.as_posix()}"
            )

        return CacheConfig(filepath)
