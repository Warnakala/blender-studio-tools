import json
import os
import contextlib

from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Union, Optional, Tuple, Dict
from copy import deepcopy

import bpy

from . import prefs, propsdata, cmglobals, opsdata
from .logger import LoggerFactory, gen_processing_string, log_new_lines

logger = LoggerFactory.getLogger(__name__)


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
        json.dump(data, file, indent=2)


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


class CacheConfig:
    def __init__(self, filepath: Path):
        self.filepath: Path = filepath
        self._load(filepath)

    def _load(self, filepath: Path) -> None:
        self._json_obj: Dict[str, Any] = read_json(self.filepath)
        self.filepath = filepath
        logger.info("Loaded cacheconfig from: %s", filepath.as_posix())

    @property
    def json_obj(self) -> Any:
        return self._json_obj

    def get_meta(self) -> Dict[str, Any]:
        return deepcopy(self._json_obj["meta"])

    def get_meta_key(self, key: str) -> Any:
        return self._json_obj["meta"][key]

    def get_all_coll_ref_names(self, libfile: str) -> List[str]:
        return sorted(
            self._json_obj["libs"][libfile]["data_from"]["collections"].keys()
        )

    def get_all_libfiles(self):
        return self._json_obj["libs"].keys()

    def get_cachefile(self, libfile: str, coll_ref_name: str, variant: str) -> str:
        return self._json_obj["libs"][libfile]["data_from"]["collections"][
            coll_ref_name
        ][variant]["cachefile"]

    def get_all_collvariants(self, libfile: str, coll_ref_name: str) -> Dict[str, Any]:
        return deepcopy(
            self._json_obj["libs"][libfile]["data_from"]["collections"][coll_ref_name]
        )

    def get_coll_to_lib_mapping(self) -> Dict[str, str]:
        remapping = {}
        for libfile in self._json_obj["libs"]:
            for coll_str in self._json_obj["libs"][libfile]["data_from"]["collections"]:
                for variant_name in self._json_obj["libs"][libfile]["data_from"][
                    "collections"
                ][coll_str]:
                    remapping[variant_name] = libfile
        return remapping

    def get_animation_data(self) -> Dict[str, Any]:
        return deepcopy(self._json_obj["animation_data"])

    def get_all_anim_obj_names(self) -> List[str]:
        return sorted(self._json_obj["animation_data"].keys())

    def get_anim_obj(self, obj_name: str) -> Optional[Dict[str, Any]]:
        try:
            anim_obj_dict = self._json_obj["animation_data"][obj_name]
        except KeyError:
            logger.error(
                "%s not found in animation data (cacheconfig: %s)",
                obj_name,
                self.filepath.as_posix(),
            )
            return None
        return deepcopy(anim_obj_dict)

    def get_all_driver_dicts_for_obj(self, obj_name: str) -> List[Dict[str, Any]]:
        return deepcopy(self._json_obj["animation_data"][obj_name]["drivers"])


class CacheConfigBlueprint(CacheConfig):
    _CACHECONFIG_TEMPL: Dict[str, Any] = {
        "meta": {},
        "libs": {},
        "animation_data": {},  # {filepath_to_lib: _LIBDICT_TEMPL}
    }
    _LIBDICT_TEMPL: Dict[str, Any] = {
        "data_from": {"collections": {}},  # {'colname': {'cachefile': cachepath}}
    }
    _OBJECTDICT_TEMPL = {"type": "", "drivers": []}
    _DRIVERDICT_TEMPL = {"data_path": "", "value": []}

    def __init__(self):
        self._json_obj: Dict[str, Any] = deepcopy(self._CACHECONFIG_TEMPL)

    def init_by_file(self, filepath: Path) -> None:
        self._json_obj = read_json(filepath)

    def set_meta_key(self, key: str, value: Any) -> None:
        self._json_obj["meta"][key] = value

    def save_as_cacheconfig(self, filepath: Path) -> None:
        save_as_json(self._json_obj, filepath)

    def _ensure_lib(self, libfile: str) -> None:
        self._json_obj["libs"].setdefault(libfile, deepcopy(self._LIBDICT_TEMPL))

    def _ensure_coll_ref(self, libfile: str, coll_ref_name: str) -> None:
        self._json_obj["libs"][libfile]["data_from"]["collections"].setdefault(
            coll_ref_name, {}
        )

    def _ensure_coll_variant(
        self, libfile: str, coll_ref_name: str, coll_var_name: str
    ) -> None:
        self._json_obj["libs"][libfile]["data_from"]["collections"][
            coll_ref_name
        ].setdefault(coll_var_name, {})

    def _ensure_anim_obj(self, obj_name: str) -> None:
        self._json_obj["animation_data"].setdefault(
            obj_name, deepcopy(self._OBJECTDICT_TEMPL)
        )

    def _ensure_driver_dict(self, obj_name: str) -> None:
        self._json_obj["animation_data"][obj_name].setdefault(
            "drivers", deepcopy(self._DRIVERDICT_TEMPL)
        )

    def append_driver_dict(self, obj_name: str, driver_dict: Dict[str, Any]) -> None:
        self._json_obj["animation_data"][obj_name]["drivers"].append(driver_dict)

    def set_driver_dict_at_index(
        self, obj_name: str, driver_dict: Dict[str, Any], index: int
    ) -> None:
        self._json_obj["animation_data"][obj_name]["drivers"][index] = driver_dict

    def clear_all_driver_dicts(self, obj_name: str) -> None:
        self._json_obj["animation_data"][obj_name]["drivers"].clear()

    def set_anim_obj_key(self, obj_name: str, key: str, value: Any) -> None:

        self._ensure_anim_obj(obj_name)
        self._json_obj["animation_data"][obj_name][key] = value

    def set_coll_variant(
        self,
        libfile: str,
        coll_ref_name: str,
        coll_var_name: str,
        coll_dict: Dict[str, Any],
    ) -> None:

        self._ensure_lib(libfile)
        self._ensure_coll_ref(libfile, coll_ref_name)
        self._ensure_coll_variant(libfile, coll_ref_name, coll_var_name)

        self.json_obj["libs"][libfile]["data_from"]["collections"][coll_ref_name][
            coll_var_name
        ] = coll_dict

    def get_drivers_dict_templ(self):
        return deepcopy(self._DRIVERDICT_TEMPL)


class CacheConfigProcessor:
    @classmethod
    def import_collections(
        cls, cacheconfig: CacheConfig, context: bpy.types.Context, link: bool = True
    ) -> List[bpy.types.Collection]:

        # list of collections to track which ones got imported
        colls: List[bpy.types.Collection] = []

        for libfile in cacheconfig.get_all_libfiles():

            libpath = Path(libfile)

            with bpy.data.libraries.load(
                libpath.as_posix(), relative=True, link=link
            ) as (
                data_from,
                data_to,
            ):

                for coll_name in cacheconfig.get_all_coll_ref_names(libfile):

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
            for coll_name in cacheconfig.get_all_coll_ref_names(libfile):

                instance_objs = []

                # for each variant add instance object
                for variant_name in sorted(
                    cacheconfig.get_all_collvariants(libfile, coll_name)
                ):

                    source_collection = bpy.data.collections[coll_name]
                    cachefile = cacheconfig.get_cachefile(
                        libfile, coll_name, variant_name
                    )

                    instance_obj = bpy.data.objects.new(
                        name=variant_name, object_data=None
                    )
                    instance_obj.instance_collection = source_collection
                    instance_obj.instance_type = "COLLECTION"

                    parent_collection = bpy.context.view_layer.active_layer_collection
                    parent_collection.collection.objects.link(instance_obj)

                    instance_objs.append(
                        (
                            instance_obj,
                            variant_name,
                            cachefile,
                        )
                    )
                    logger.info(
                        "Instanced collection: %s as: %s (variant: %s)",
                        source_collection.name,
                        instance_obj.name,
                        variant_name,
                    )

                # override the instance objects
                for obj, variant_name, cachefile in instance_objs:

                    # deselect all
                    bpy.ops.object.select_all(action="DESELECT")

                    # needs active object (coll instance)
                    context.view_layer.objects.active = obj
                    obj.select_set(True)

                    # add lib override
                    bpy.ops.object.make_override_library()

                    # get collection by name
                    coll = bpy.data.collections[variant_name]

                    # set cm.cachefile property
                    coll.cm.cachefile = cachefile
                    cls._add_coll_to_cm_collections(context, coll)
                    colls.append(coll)

                    logger.info(
                        "%s added override and assigned cachefile: %s (variant: %s)",
                        coll.name,
                        cachefile,
                        variant_name,
                    )

        return sorted(colls, key=lambda x: x.name)

    @classmethod
    def import_animation_data(
        cls, cacheconfig: CacheConfig, colls: List[bpy.types.Collection]
    ) -> None:

        colls = sorted(colls, key=lambda x: x.name)

        frame_in = cacheconfig.get_meta_key("frame_start")
        frame_out = cacheconfig.get_meta_key("frame_end")

        log_new_lines(1)
        logger.info("-START- Importing Animation Data")

        coll_to_lib_mapping = cacheconfig.get_coll_to_lib_mapping()

        for coll in colls:
            log_new_lines(1)
            logger.info("%s", gen_processing_string(coll.name + " animation data"))

            # TODO: what if coll does not exist in cacheconfig
            libfile = coll_to_lib_mapping[coll.name]

            # if there is no animation_data for this libfile skip
            if not cacheconfig.get_animation_data():
                logger.info("No animation data available for collection %s", coll.name)
                continue

            # for each object in this lib file that has animation data set keyframes on each frame
            for obj in coll.all_objects:

                obj_name = obj.name
                anim_obj_dict = cacheconfig.get_anim_obj(obj_name)

                if not anim_obj_dict:
                    logger.info(
                        "Failed to import animation data for %s. Not found in cacheconfig.",
                        obj_name,
                    )
                    continue

                # disable drivers
                opsdata.disable_vis_drivers([obj])

                driven_props_list = []  # for log

                # get property that was driven and set keyframes
                for driver_dict in cacheconfig.get_all_driver_dicts_for_obj(obj_name):

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

                        command = f'bpy.data.objects["{obj_name}"]{deliminater}{data_path_str}={prop_value}'
                        json_
                        print(command)
                        exec(command)
                        # obj.keyframe_insert(data_path=data_path_str, frame=frame)

                logger.info(
                    "%s imported animation (%s, %s) for props: %s",
                    obj.name,
                    frame_in,
                    frame_out,
                    " ,".join(driven_props_list),
                )

        log_new_lines(1)
        logger.info("-END- Importing Animation Data")

    @classmethod
    def _add_coll_to_cm_collections(
        cls, context: bpy.types.Context, coll: bpy.types.Collection
    ) -> bpy.types.Collection:
        scn = context.scene
        if coll.name in [c[1].name for c in scn.cm.colls_import.items()]:
            logger.info("%s already in the cache collections list", coll.name)

        else:
            item = scn.cm.colls_import.add()
            item.coll_ptr = coll
            item.name = item.coll_ptr.name
            scn.cm.colls_import_index = len(scn.cm.colls_import) - 1

            logger.info("%s added to cache collections list", item.name)

        return coll


class CacheConfigFactory:

    _DATE_FORMAT = "%Y-%m-%dT%H:%M:%S"

    @classmethod
    def gen_config_from_colls(
        cls,
        context: bpy.types.Context,
        colls: List[bpy.types.Collection],
        filepath: Path,
    ) -> CacheConfig:

        blueprint = CacheConfigBlueprint()

        colls = sorted(colls, key=lambda x: x.name)

        # if cacheconfig already exists load it and update entries
        if filepath.exists():
            logger.info(
                "Cacheconfig already exists: %s. Will update entries.",
                filepath.as_posix(),
            )
            blueprint.init_by_file(filepath)

        log_new_lines(2)
        noun = "Updating" if filepath.exists else "Creating"
        logger.info("-START- %s CacheConfig", noun)

        # populate metadata
        cls._populate_metadata(context, blueprint)

        # poulate cacheconfig with libs based on collections
        cls._populate_libs(context, colls, blueprint)

        # populate collections with animation data
        objects_with_anim = cls._populate_with_animation_data(colls, blueprint)

        # get drive values for each frame
        cls._read_and_store_animation_data(context, objects_with_anim, blueprint)

        # save json obj to disk
        blueprint.save_as_cacheconfig(filepath)
        logger.info("Generated cacheconfig and saved to: %s", filepath.as_posix())

        log_new_lines(1)
        logger.info("-END- %s CacheConfig", noun)

        return CacheConfig(filepath)

    @classmethod
    def _populate_metadata(
        cls, context: bpy.types.Context, blueprint: CacheConfigBlueprint
    ) -> CacheConfigBlueprint:

        blueprint.set_meta_key(
            "blendfile",
            Path(bpy.data.filepath).absolute().as_posix()
            if bpy.data.filepath
            else "unsaved_blendfile",
        )

        blueprint.set_meta_key(
            "name",
            Path(bpy.data.filepath).name if bpy.data.filepath else "unsaved_blendfile",
        )

        if not "creation_date" in blueprint.get_meta():
            blueprint.set_meta_key(
                "creation_date", get_current_time_string(cls._DATE_FORMAT)
            )

        blueprint.set_meta_key("updated_at", get_current_time_string(cls._DATE_FORMAT))

        blueprint.set_meta_key("frame_start", context.scene.frame_start)

        blueprint.set_meta_key("frame_end", context.scene.frame_end)

        logger.info("Created metadata")
        return blueprint

    @classmethod
    def _populate_libs(
        cls,
        context: bpy.types.Context,
        colls: List[bpy.types.Collection],
        blueprint: CacheConfigBlueprint,
    ) -> CacheConfigBlueprint:

        colls = sorted(colls, key=lambda x: x.name)

        # get librarys
        for coll in colls:
            coll_ref = coll.override_library.reference
            lib = coll.override_library.reference.library
            libfile = Path(os.path.abspath(bpy.path.abspath(lib.filepath))).as_posix()

            # create collection dict based on this variant collection
            _coll_dict = {
                "cachefile": propsdata.gen_cachepath_collection(
                    coll, context
                ).as_posix(),
            }

            # set blueprint coll variant
            blueprint.set_coll_variant(libfile, coll_ref.name, coll.name, _coll_dict)

        # log
        for libfile in blueprint.get_all_libfiles():
            logger.info(
                "Gathered libfile: %s with collections: %s",
                libfile,
                ", ".join(blueprint.get_all_coll_ref_names(libfile)),
            )

        return blueprint

    @classmethod
    def _populate_with_animation_data(
        cls,
        colls: List[bpy.types.Collection],
        blueprint: CacheConfigBlueprint,
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

                    # set type
                    blueprint.set_anim_obj_key(obj.name, "type", str(obj.type))

                    # gen driver dict and append to blueprint
                    driver_dict = blueprint.get_drivers_dict_templ()
                    driver_dict["data_path"] = driver.data_path
                    blueprint.append_driver_dict(obj.name, driver_dict)

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
        blueprint: CacheConfigBlueprint,
    ) -> CacheConfigBlueprint:

        # get driver values for each frame
        fin = context.scene.frame_start
        fout = context.scene.frame_end
        frame_range = range(fin, fout + 1)

        with temporary_current_frame(context) as original_curframe:
            for frame in frame_range:
                context.scene.frame_set(frame)
                logger.info("Storing animation data for frame %i", frame)

                for obj in objects:

                    # get deepcopy of all driver dicts
                    driver_data = blueprint.get_all_driver_dicts_for_obj(obj.name)

                    for idx, driver_dict in enumerate(driver_data):
                        data_path_str = driver_dict["data_path"]
                        driven_value = obj.path_resolve(data_path_str)
                        driver_dict["value"].append(driven_value)

                        # update blueprint driver dict at index
                        blueprint.set_driver_dict_at_index(obj.name, driver_dict, idx)
        # log
        logger.info(
            "Stored data for animated properties (%i, %i).",
            fin,
            fout,
        )
        return blueprint

    @classmethod
    def load_config_from_file(cls, filepath: Path) -> CacheConfig:
        if not filepath.exists():
            raise ValueError(
                f"Failed to load config. Path does not exist: {filepath.as_posix()}"
            )

        return CacheConfig(filepath)
