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
# (c) 2021, Blender Foundation

import json
import os
import contextlib

from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Union, Optional, Tuple, Dict
from copy import deepcopy

import bpy

from cache_manager import prefs, propsdata, cmglobals, opsdata
from cache_manager.logger import LoggerFactory, log_new_lines

logger = LoggerFactory.getLogger(__name__)


def is_valid_cache_object(obj: bpy.types.Object) -> bool:
    if obj.type not in cmglobals.VALID_OBJECT_TYPES:
        return False

    if obj.type == "CAMERA":
        return True

    if obj.type == "EMPTY":
        return True

    if obj.type == "LATTICE":
        return True

    return obj.name.startswith("GEO")


def is_valid_cache_coll(coll: bpy.types.Collection) -> bool:
    if opsdata.is_item_local(coll) and not bpy.data.filepath:
        return False
    return True


def get_valid_cache_objects(collection: bpy.types.Collection) -> List[bpy.types.Object]:
    object_list = [obj for obj in collection.all_objects if is_valid_cache_object(obj)]
    return object_list


def get_current_time_string(date_format: str) -> str:
    now = datetime.now()
    current_time_string = now.strftime(date_format)
    return current_time_string


def get_ref_coll_by_name(coll_name: str) -> bpy.types.Collection:
    coll = bpy.data.collections[coll_name]

    if not coll.override_library:
        return coll

    return coll.override_library.reference


def get_ref_coll(coll: bpy.types.Collection) -> bpy.types.Collection:
    if not coll.override_library:
        return coll

    return coll.override_library.reference


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

    # Meta.

    def get_meta(self) -> Dict[str, Any]:
        return deepcopy(self._json_obj["meta"])

    def get_meta_key(self, key: str) -> Any:
        return self._json_obj["meta"][key]

    # Libfiles / Collections.
    def get_all_libfiles(self):
        return self._json_obj["libs"].keys()

    def get_all_coll_ref_names(self, libfile: str) -> List[str]:
        return sorted(
            self._json_obj["libs"][libfile]["data_from"]["collections"].keys()
        )

    def get_cachefile(self, libfile: str, coll_ref_name: str, variant: str) -> str:
        return self._json_obj["libs"][libfile]["data_from"]["collections"][
            coll_ref_name
        ][variant]["cachefile"]

    def get_all_collvariants(self, libfile: str, coll_ref_name: str) -> Dict[str, Any]:
        return deepcopy(
            self._json_obj["libs"][libfile]["data_from"]["collections"][coll_ref_name]
        )

    # Remapping.
    def get_coll_to_lib_mapping(self) -> Dict[str, str]:
        remapping = {}
        for libfile in self._json_obj["libs"]:
            for coll_str in self._json_obj["libs"][libfile]["data_from"]["collections"]:
                for variant_name in self._json_obj["libs"][libfile]["data_from"][
                    "collections"
                ][coll_str]:
                    remapping[variant_name] = libfile
        return remapping

    # Objs / Cams.
    def get_animation_data(self, obj_category: str) -> Dict[str, Any]:
        return deepcopy(self._json_obj[obj_category])

    def get_all_obj_names(self, obj_category: str) -> List[str]:
        return sorted(self._json_obj[obj_category].keys())

    def get_obj(self, obj_category: str, obj_name: str) -> Optional[Dict[str, Any]]:
        try:
            anim_obj_dict = self._json_obj[obj_category][obj_name]
        except KeyError:
            logger.error(
                "%s not found in cacheconfig.",
                obj_name,
            )
            return None
        return deepcopy(anim_obj_dict)

    def get_all_data_paths(self, obj_category: str, obj_name: str) -> List[str]:
        return self._json_obj[obj_category][obj_name]["data_paths"].keys()

    def get_all_data_path_values(
        self, obj_category: str, obj_name: str, data_path: str
    ) -> List[Any]:
        return deepcopy(
            self._json_obj[obj_category][obj_name]["data_paths"][data_path]["value"]
        )

    def get_data_path_value(
        self, obj_category: str, obj_name: str, data_path: str, frame: int
    ) -> Any:
        return self._json_obj[obj_category][obj_name]["data_paths"][data_path]["value"][
            frame
        ]

    def get_abc_obj_path(self, obj_name: str):
        try:
            abc_path = self._json_obj["objects"][obj_name]["abc_obj_path"]
        except KeyError:
            logger.error(
                "%s not found in cacheconfig. Failed to get abc obj cache path.",
                obj_name,
            )
            return None

        return abc_path


class CacheConfigBlueprint(CacheConfig):
    _CACHECONFIG_TEMPL: Dict[str, Any] = {
        "meta": {},
        "libs": {},
        "objects": {},
        "cameras": {},
    }
    _LIBDICT_TEMPL: Dict[str, Any] = {
        "data_from": {"collections": {}},  # {'colname': {'cachefile': cachepath}}
    }
    _OBJ_DICT_TEMPL: Dict[str, Any] = {"type": "", "abc_obj_path": "", "data_paths": {}}
    _DATA_PATH_DICT: Dict[str, List[Any]] = {"value": []}

    def __init__(self):
        self._json_obj: Dict[str, Any] = deepcopy(self._CACHECONFIG_TEMPL)

    def init_by_file(self, filepath: Path) -> None:
        self._json_obj = read_json(filepath)

    def save_as_cacheconfig(self, filepath: Path) -> None:
        save_as_json(self._json_obj, filepath)

    # Meta.

    def set_meta_key(self, key: str, value: Any) -> None:
        self._json_obj["meta"][key] = value

    # Lib.
    def _ensure_lib(self, libfile: str) -> None:
        self._json_obj["libs"].setdefault(libfile, deepcopy(self._LIBDICT_TEMPL))

    # Collection.
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

    # Objs / Cameras.
    def _ensure_obj(self, obj_category: str, obj_name: str) -> None:
        self._json_obj[obj_category].setdefault(
            obj_name, deepcopy(self._OBJ_DICT_TEMPL)
        )

    def set_obj_key(
        self, obj_category: str, obj_name: str, key: str, value: Any
    ) -> None:

        self._ensure_obj(obj_category, obj_name)
        self._json_obj[obj_category][obj_name][key] = value

    def add_obj_data_path(
        self, obj_category: str, obj_name: str, data_path: str
    ) -> None:
        self._ensure_obj(obj_category, obj_name)
        self._json_obj[obj_category][obj_name]["data_paths"][data_path] = deepcopy(
            self._DATA_PATH_DICT
        )

    def append_value_to_data_path(
        self, obj_category: str, obj_name: str, data_path: str, value: Any
    ) -> None:
        # Otherwise json will throw an error, tuple is supported by blender.
        if type(value).__name__ == "bpy_prop_array":
            value = tuple(value)

        self._json_obj[obj_category][obj_name]["data_paths"][data_path]["value"].append(
            value
        )

    def get_data_path_dict_templ(self) -> Dict[str, Any]:
        return deepcopy(self._DRIVERDICT_TEMPL)


class CacheConfigProcessor:
    @classmethod
    def import_collections(
        cls, cacheconfig: CacheConfig, context: bpy.types.Context, link: bool = True
    ) -> List[bpy.types.Collection]:

        # Link collections in bpy.data of this blend file.
        cls._import_data_from_libfiles(cacheconfig, link=link)

        # Create.
        colls = cls._instance_colls_to_scene_and_override(cacheconfig, context)
        return colls

    @classmethod
    def _import_data_from_libfiles(
        cls, cacheconfig: CacheConfig, link: bool = True
    ) -> None:

        noun = "Appended"
        if link:
            noun = "Linked"

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
                        logger.error(
                            "Failed to import collection %s from %s. Doesn't exist in file.",
                            coll_name,
                            libpath.as_posix(),
                        )
                        continue

                    if coll_name in data_to.collections:
                        logger.info("Collection %s already in blendfile.", coll_name)
                        continue

                    data_to.collections.append(coll_name)
                    logger.info(
                        "%s collection: %s from library: %s",
                        noun,
                        coll_name,
                        libpath.as_posix(),
                    )

    @classmethod
    def _instance_colls_to_scene_and_override(
        cls, cacheconfig: CacheConfig, context: bpy.types.Context
    ) -> List[bpy.types.Collection]:
        # List of collections to track which ones got imported.
        colls: List[bpy.types.Collection] = []

        for libfile in cacheconfig.get_all_libfiles():

            # Link collections in current scene and add cm.cachfile property.
            for coll_name in cacheconfig.get_all_coll_ref_names(libfile):

                # For each variant add instance object.
                for variant_name in sorted(
                    cacheconfig.get_all_collvariants(libfile, coll_name)
                ):
                    if cls._is_coll_variant_in_blend(variant_name):
                        logger.info("Collection %s already exists. Skip.", variant_name)
                        continue

                    logger.info(
                        "Collection variant %s does not exist yet. Will create.",
                        variant_name,
                    )

                    # Get source collection and create collection instance of it.
                    source_collection = get_ref_coll_by_name(coll_name)
                    instance_obj = cls._create_collection_instance(
                        source_collection, variant_name
                    )

                    # Add library override to collection inst.
                    cls._make_library_override(instance_obj, context)

                    # Add collection properties.

                    coll = bpy.data.collections[variant_name, None]
                    # TODO: Super risky but I found no other way around this
                    # we have no influence on the naming of objects that will be created
                    # by bpy.ops.object.make_override_library() -> we can just hope here
                    # that there is not other object that would mess up the incrementation
                    # -> cache would not work anymore with wrong incrementation.
                    cachefile = cacheconfig.get_cachefile(
                        libfile, coll_name, variant_name
                    )

                    # Set cm.cachefile property.
                    coll.cm.cachefile = cachefile
                    opsdata.add_coll_to_cache_collections(context, coll, "IMPORT")
                    colls.append(coll)

                    logger.info(
                        "%s assigned cachefile: %s (variant: %s)",
                        coll.name,
                        cachefile,
                        variant_name,
                    )

        return sorted(colls, key=lambda x: x.name)

    @classmethod
    def _is_coll_variant_in_blend(cls, variant_name: str) -> bool:
        # Check if variant already in this blend file.
        try:
            coll = bpy.data.collections[variant_name, None]
        except KeyError:
            return False
        else:
            # Collection already exists, not continuing would add another
            # collection instance which then gets overwritten which results
            # in an increase of object inrementation > caches wont work.
            if coll.library:
                return False
            return True

    @classmethod
    def _create_collection_instance(
        cls, source_collection: bpy.types.Collection, variant_name: str
    ) -> bpy.types.Object:
        # Variant name has no effect how the overwritten library collection in the end
        # will be named is supplied here just for loggin purposes.

        # Use empty to instance source collection.
        instance_obj = bpy.data.objects.new(name=variant_name, object_data=None)
        instance_obj.instance_collection = source_collection
        instance_obj.instance_type = "COLLECTION"

        parent_collection = bpy.context.view_layer.active_layer_collection
        parent_collection.collection.objects.link(instance_obj)

        logger.info(
            "Instanced collection: %s as: %s (variant: %s)",
            source_collection.name,
            instance_obj.name,
            variant_name,
        )

        return instance_obj

    @classmethod
    def _make_library_override(
        cls, instance_obj: bpy.types.Object, context: bpy.types.Context
    ) -> None:
        log_name = instance_obj.name
        # Deselect all.
        bpy.ops.object.select_all(action="DESELECT")

        # Needs active object (coll instance).
        context.view_layer.objects.active = instance_obj
        instance_obj.select_set(True)

        # Add lib override.
        bpy.ops.object.make_override_library()

        logger.info(
            "%s make library override.",
            log_name,
        )

    @classmethod
    def import_animation_data(
        cls, cacheconfig: CacheConfig, colls: List[bpy.types.Collection]
    ) -> None:

        colls = sorted(colls, key=lambda x: x.name)
        frame_in = cacheconfig.get_meta_key("frame_start")
        frame_out = cacheconfig.get_meta_key("frame_end")

        log_new_lines(1)
        logger.info("-START- Importing Animation Data %i - %i", frame_in, frame_out)

        objs_load_anim: List[bpy.types.Object] = []
        cams_laod_anim: List[bpy.types.Camera] = []

        # Gather all objects to load anim on.
        for coll in colls:
            for obj in coll.all_objects:
                if not is_valid_cache_object(obj):
                    continue

                if obj.type == "CAMERA":
                    cams_laod_anim.append(obj.data)
                    continue

                objs_load_anim.append(obj)

        # Extend object list with cameras.
        objs_load_anim.extend(cams_laod_anim)

        # Import animation data for objects.
        cls._import_animation_data_objects(cacheconfig, objs_load_anim)

        log_new_lines(1)
        logger.info("-END- Importing Animation Data")

    @classmethod
    def _import_animation_data_objects(
        cls,
        cacheconfig: CacheConfig,
        objects: List[Union[bpy.types.Object, bpy.types.Camera]],
    ) -> None:

        frame_in = cacheconfig.get_meta_key("frame_start")
        frame_out = cacheconfig.get_meta_key("frame_end")

        # Check if obj in collection is in cacheconfig
        # if so key all data paths with the value from cacheconfig.

        for obj in objects:

            obj_category = "objects"
            if obj.type in cmglobals.CAMERA_TYPES:
                obj_category = "cameras"

            obj_name = obj.name
            obj_dict = cacheconfig.get_obj(obj_category, obj_name)

            if not obj_dict:
                continue

            anim_props_list = []  # for log
            muted_drivers = []  # for log

            # Get property that was driven and set keyframes.
            for data_path in cacheconfig.get_all_data_paths(obj_category, obj_name):

                # Disable drivers.
                muted_drivers.extend(
                    opsdata.disable_drivers_by_data_path([obj], data_path)
                )

                # For log.
                anim_props_list.append(data_path)

                # Insert keyframe for frames in json_obj.
                for frame in range(frame_in, frame_out + 1):

                    # Get value to set prop to.
                    prop_value = cacheconfig.get_data_path_value(
                        obj_category, obj_name, data_path, frame - frame_in
                    )

                    # Pack string prop in "" so exec works.
                    if type(prop_value) == str:
                        prop_value = f'"{prop_value}"'

                    # Get right delimeter.
                    deliminater = "."
                    if data_path.startswith("["):
                        deliminater = ""

                    # Get right data category.
                    command = f'bpy.data.{obj_category}["{obj_name}", None]{deliminater}{data_path}={prop_value}'

                    # Set property and insert keyframe.
                    exec(command)
                    obj.keyframe_insert(data_path=data_path, frame=frame)

            if muted_drivers:
                logger.info(
                    "%s disabled drivers: %s",
                    obj_name,
                    " ,".join([m.data_path for m in muted_drivers]),
                )
            if anim_props_list:
                logger.info(
                    "%s imported animation for data paths: %s",
                    obj_name,
                    " ,".join(anim_props_list),
                )


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

        # If cacheconfig already exists load it and update entries.
        if filepath.exists():
            logger.info(
                "Cacheconfig already exists: %s. Will update entries.",
                filepath.as_posix(),
            )
            blueprint.init_by_file(filepath)

        log_new_lines(2)
        noun = "Updating" if filepath.exists else "Creating"
        logger.info("-START- %s CacheConfig", noun)

        # Populate metadata.
        cls._populate_metadata(context, blueprint)

        # Populate cacheconfig with libs based on collections.
        cls._populate_libs(context, colls, blueprint)

        # Populate cacheconfig with animation data.
        objects_with_anim = cls._populate_with_objs(colls, blueprint)

        # Populate cacheconfig with cameras.
        cams_to_cache = cls._populate_with_cameras(colls, blueprint)

        # Add cameras to objects with anim list.
        objects_with_anim.extend(cams_to_cache)

        # Get drive values for each frame.
        cls._store_data_path_values(context, objects_with_anim, blueprint)

        # Save json obj to disk.
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

        # Get libraries.
        for coll in colls:

            libfile = opsdata.get_item_libfile(coll)
            coll_ref = get_ref_coll(coll)

            # Create collection dict based on this variant collection.
            _coll_dict = {
                "cachefile": propsdata.gen_cachepath_collection(
                    coll, context
                ).as_posix(),
            }

            # Set blueprint coll variant.
            blueprint.set_coll_variant(libfile, coll_ref.name, coll.name, _coll_dict)

        # Log.
        for libfile in blueprint.get_all_libfiles():
            logger.info(
                "Gathered libfile: %s with collections: %s",
                libfile,
                ", ".join(blueprint.get_all_coll_ref_names(libfile)),
            )

        return blueprint

    @classmethod
    def _populate_with_objs(
        cls,
        colls: List[bpy.types.Collection],
        blueprint: CacheConfigBlueprint,
    ) -> List[bpy.types.Object]:

        objects_with_anim: List[bpy.types.Object] = []

        for coll in colls:

            obj_category = "objects"

            # Loop over all objects in that collection.
            for obj in coll.all_objects:

                is_anim = False

                if not is_valid_cache_object(obj):
                    continue

                # Set abc_obj_path.
                blueprint.set_obj_key(
                    obj_category,
                    obj.name,
                    "abc_obj_path",
                    str(opsdata.gen_abc_object_path(obj)),
                )

                # Set type.
                blueprint.set_obj_key(obj_category, obj.name, "type", str(obj.type))

                if not obj.animation_data:
                    continue

                if not obj.animation_data.drivers:
                    continue

                # For now we only write data paths that are driven,
                # TODO: detect properties that have an animation or are driven.
                for driver in obj.animation_data.drivers:

                    # Seems to be an override resync issue that old datapaths are sill in .drivers
                    # even tough they don't exist anymore, filter them out like this:.
                    try:
                        obj.path_resolve(driver.data_path)
                    except ValueError:
                        continue

                    # Don't export animation for vis of modifiers.
                    data_path = driver.data_path.split(".")

                    if len(data_path) > 1:
                        if data_path[0].startswith("modifiers"):
                            if data_path[-1] in cmglobals.DRIVER_VIS_DATA_PATHS:
                                continue

                    # Add data path of driver to obj data pats dict.
                    blueprint.add_obj_data_path(
                        obj_category, obj.name, driver.data_path
                    )

                    if not is_anim:
                        is_anim = True

                if is_anim:
                    objects_with_anim.append(obj)
        # Log.
        logger.info("Populated CacheConfig with animated properties.")

        return objects_with_anim

    @classmethod
    def _populate_with_cameras(
        cls,
        colls: List[bpy.types.Collection],
        blueprint: CacheConfigBlueprint,
    ) -> List[bpy.types.Camera]:

        obj_category = "cameras"
        cams_to_cache: List[bpy.types.Camera] = []

        for cam in bpy.data.cameras:

            if opsdata.is_item_local(cam) and not bpy.data.filepath:
                logger.error(
                    "Failed to add local camera %s to cacheconfig. Blend files needs to be saved.",
                    cam.name,
                )
                continue

            if opsdata.is_item_lib_source(cam):
                logger.error(
                    "Failed to add library data camera %s to cacheconfig. Skip.",
                    cam.name,
                )
                continue

            libfile = opsdata.get_item_libfile(cam)

            # Make sure to only export cams that are in current cache collections.
            if libfile not in blueprint.get_all_libfiles():
                continue

            # Set type.
            blueprint.set_obj_key(obj_category, cam.name, "type", str(cam.type))

            cams_to_cache.append(cam)

            for data_path in cmglobals.CAM_DATA_PATHS:
                blueprint.add_obj_data_path(obj_category, cam.name, data_path)

        logger.info("Populated CacheConfig with cameras.")

        return cams_to_cache

    @classmethod
    def _store_data_path_values(
        cls,
        context: bpy.types.Context,
        objects: List[bpy.types.Object],
        blueprint: CacheConfigBlueprint,
    ) -> CacheConfigBlueprint:

        # Get driver values for each frame.
        fin = context.scene.frame_start
        fout = context.scene.frame_end
        frame_range = range(fin, fout + 1)

        with temporary_current_frame(context) as original_curframe:
            for frame in frame_range:
                context.scene.frame_set(frame)
                logger.info("Storing animation data for frame %i", frame)

                for obj in objects:
                    obj_category = "objects"
                    if obj.type in cmglobals.CAMERA_TYPES:
                        obj_category = "cameras"

                    for data_path in blueprint.get_all_data_paths(
                        obj_category, obj.name
                    ):
                        data_path_value = obj.path_resolve(data_path)
                        blueprint.append_value_to_data_path(
                            obj_category, obj.name, data_path, data_path_value
                        )

        # Log.
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
