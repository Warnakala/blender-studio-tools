import json
from pathlib import Path
from typing import Dict, List, Any, Union, Optional, Tuple

import bpy

from .logger import LoggerFactory

logger = LoggerFactory.getLogger(__name__)


class CacheConfig:
    def __init__(self):
        self.filepath: Path = Path()
        self.name = ""
        self.creation_date = ""
        # [{libpath: str, data_from: {collections: [(colname, cachefile_path), (colname, cachefile_path)]}]
        self.libraries: List[Dict[str, Any]] = []

    def load(self, filepath: Path) -> None:
        self.filepath = filepath

    def process(self, context: bpy.types.Context) -> None:
        if not self.filepath:
            logger.error("Failed to process cache config. Is not loaded.")
            return

        json_obj = self._read_json(self.filepath)

        for libdict in json_obj:
            colls = self._process_lib_dict(context, libdict)

    def _read_json(self, filepath: Path) -> Dict[Any, Any]:
        with open(filepath.as_posix(), "r") as file:
            json_obj = json.loads(file.read())
            return json_obj

    def _save_as_json(self, dictionary: Dict[Any, Any], filepath: Path) -> None:
        with open(filepath.as_posix(), "w+") as file:
            json.dump(dictionary, file, indent=4)

    def _process_lib_dict(
        self, context: bpy.types.Context, libdict: Dict[str, Any]
    ) -> List[bpy.types.Collection]:

        libpath = Path(libdict["libpath"])
        colls: List[bpy.types.Collection] = []

        with bpy.data.libraries.load(libpath.as_posix(), relative=True) as (
            data_from,
            data_to,
        ):
            for colldata in libdict["data_from"]["collections"]:
                coll_name = colldata["name"]
                cachefile = colldata["cachefile"]

                if coll_name not in data_from.collections:
                    logger.warning(
                        "Failed to import collection %s from %s. Doesn't exist in file.",
                        coll_name,
                        libpath,
                    )
                    continue

                if coll_name in data_to.collections:
                    logger.warning("Collection %s already in blendfile.", coll_name)
                    continue

                data_to.collections.append(coll_name)

        # link collections in current scene and add cm.cachfile property
        for colldata in libdict["data_from"]["collections"]:
            coll_name = colldata["name"]
            cachefile = colldata["cachefile"]

            coll = bpy.data.collections[coll_name]

            try:
                bpy.context.scene.collection.children.link(coll)
            except RuntimeError:
                logger.warning("Collection %s already in blendfile.", coll_name)

            # set cm.cachefile property
            coll.cm.cachefile = cachefile
            self._add_coll_to_cm_collections(context, coll)

        return colls

    def _add_coll_to_cm_collections(
        self, context: bpy.types.Context, coll: bpy.types.Collection
    ) -> bpy.types.Collection:
        scn = context.scene
        if coll.name in [c[1].name for c in scn.cm_collections.items()]:
            logger.info("%s already in the cache collections list", coll.name)

        else:
            item = scn.cm_collections.add()
            item.coll_ptr = coll
            item.name = item.coll_ptr.name
            scn.cm_collections_index = len(scn.cm_collections) - 1

            logger.info("%s added to cache collections list", item.name)

        return coll
