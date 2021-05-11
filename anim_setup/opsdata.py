import re
from pathlib import Path
from typing import Optional, Dict, Union, Any
import bpy

from . import prefs


from .log import LoggerFactory

logger = LoggerFactory.getLogger()


def get_shot_name_from_file() -> Optional[str]:
    if not bpy.data.filepath:
        return None

    # default 110_0030_A.anim.blend
    return Path(bpy.data.filepath).name.split(".")[0]


def get_seqeunce_from_shot_name(shotname: str) -> str:
    return shotname.split("_")[0]


def get_cam_action_name_from_shot(shotname: str) -> str:
    # ANI-camera.070_0010_A
    return f"ANI-camera.{shotname}"


def get_cam_action_name_from_lib(shotname: str, libpath: Path) -> Optional[str]:

    with bpy.data.libraries.load(libpath.as_posix(), relative=True) as (
        data_from,
        data_to,
    ):
        for action in data_from.actions:
            if action.startswith(get_cam_action_name_from_shot(shotname)):
                return action
    return None


def get_previs_file(context: bpy.types.Context) -> Optional[Path]:

    addon_prefs = prefs.addon_prefs_get(context)

    shotname = get_shot_name_from_file()
    if not shotname:
        return None

    seqname = get_seqeunce_from_shot_name(shotname)
    previs_path = Path(addon_prefs.previs_root_path)

    for f in previs_path.iterdir():
        if f.is_file() and f.suffix == ".blend" and f.name.startswith(seqname):
            return f
    return None


def import_data_from_lib(
    data_category: str,
    data_name: str,
    libpath: Path,
    link: bool = True,
):

    noun = "Appended"
    if link:
        noun = "Linked"

    with bpy.data.libraries.load(libpath.as_posix(), relative=True, link=link) as (
        data_from,
        data_to,
    ):

        if data_name not in eval(f"data_from.{data_category}"):
            logger.error(
                "Failed to import %s %s from %s. Doesn't exist in file.",
                data_category,
                data_name,
                libpath.as_posix(),
            )
            return None

        if data_name in eval(f"data_to.{data_category}"):
            logger.info("%s %s already in blendfile.", data_category, data_name)

        else:
            eval(f"data_to.{data_category}.append('{data_name}')")
            logger.info(
                "%s: %s from library: %s",
                noun,
                data_name,
                libpath.as_posix(),
            )
    if link:
        return eval(
            f"bpy.data.{data_category}['{data_name}', '{bpy.path.relpath(libpath.as_posix())}']"
        )

    return eval(f"bpy.data.{data_category}['{data_name}']")


def instance_coll_to_scene_and_override(
    context: bpy.types.Context, source_collection: bpy.types.Collection
) -> bpy.types.Collection:
    instance_obj = _create_collection_instance(source_collection)
    _make_library_override(context, instance_obj)
    return bpy.data.collections[source_collection.name, None]


def _create_collection_instance(
    source_collection: bpy.types.Collection,
) -> bpy.types.Object:

    # name has no effect how the overwritten library collection in the end
    # use empty to instance source collection
    instance_obj = bpy.data.objects.new(name="", object_data=None)
    instance_obj.instance_collection = source_collection
    instance_obj.instance_type = "COLLECTION"

    parent_collection = bpy.context.view_layer.active_layer_collection
    parent_collection.collection.objects.link(instance_obj)

    logger.info(
        "Instanced collection: %s as: %s",
        source_collection.name,
        instance_obj.name,
    )

    return instance_obj


def _make_library_override(
    context: bpy.types.Context,
    instance_obj: bpy.types.Object,
) -> None:
    log_name = instance_obj.name
    # deselect all
    bpy.ops.object.select_all(action="DESELECT")

    # needs active object (coll instance)
    context.view_layer.objects.active = instance_obj
    instance_obj.select_set(True)

    # add lib override
    bpy.ops.object.make_override_library()

    logger.info(
        "%s make library override.",
        log_name,
    )


def find_asset_name(name: str) -> str:

    if name.endswith("_rig"):
        name = name[:-4]
    return name.split("-")[-1]  # CH-rex -> 'rex'


def find_rig(coll: bpy.types.Collection) -> Optional[bpy.types.Armature]:

    coll_suffix = find_asset_name(coll.name)

    for obj in coll.all_objects:
        # default rig name: 'RIG-rex' / 'RIG-Rex'
        if obj.type != "ARMATURE":
            continue

        if not obj.name.startswith("RIG"):
            continue

        if obj.name.lower() == f"rig-{coll_suffix.lower()}":
            logger.info("Found rig: %s", obj.name)
            return obj

    return None


def ensure_name_version_suffix(datablock: Any) -> Any:
    version_pattern = r"v\d\d\d"
    match = re.search(version_pattern, datablock.name)

    if not match:
        datablock.name = datablock.name + ".v001"

    return datablock
