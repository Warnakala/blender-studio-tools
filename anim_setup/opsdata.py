import re
from pathlib import Path
from typing import Optional, Dict, Union, Any, List
import bpy
from bpy.types import Key

from . import prefs


from .log import LoggerFactory

logger = LoggerFactory.getLogger()


def get_shot_name_from_file() -> Optional[str]:
    if not bpy.data.filepath:
        return None

    # default 110_0030_A.anim.blend
    return Path(bpy.data.filepath).name.split(".")[0]


def get_sequence_from_file() -> Optional[str]:
    if not bpy.data.filepath:
        return None

    # ./spritefright/pro/shots/110_rextoria/110_0010_A/110_0010_A.anim.blend
    return Path(bpy.data.filepath).parents[1].name


def get_seqeunce_short_from_shot_name(shotname: str) -> str:
    return shotname.split("_")[0]


def get_cam_action_name_from_shot(shotname: str) -> str:
    # ANI-camera.070_0010_A
    return f"ANI-camera.{shotname}"


def get_cam_action_name_from_lib(shotname: str, libpath: Path) -> Optional[str]:

    valid_actions = []

    with bpy.data.libraries.load(libpath.as_posix(), relative=True) as (
        data_from,
        data_to,
    ):

        for action in data_from.actions:
            if action.startswith(get_cam_action_name_from_shot(shotname)):
                valid_actions.append(action)

    if not valid_actions:
        return None

    return sorted(valid_actions, reverse=True)[0]


def get_previs_file(context: bpy.types.Context) -> Optional[Path]:

    addon_prefs = prefs.addon_prefs_get(context)

    shotname = get_shot_name_from_file()
    if not shotname:
        return None

    seqname = get_seqeunce_short_from_shot_name(shotname)
    previs_path = Path(addon_prefs.previs_root_path)

    for f in previs_path.iterdir():
        if f.is_file() and f.suffix == ".blend" and f.name.startswith(seqname):
            if len(f.name.split(".")) > 2:
                continue
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

        #check if datablock with same name already exists in blend file
        try:
            eval(f"bpy.data.{data_category}['{data_name}']")
        except KeyError:
            pass
        else:
            logger.info("%s already in bpy.data.%s of this blendfile.", data_name, data_category)
            return None

        #link appen data block
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

    valid_rigs = []

    for obj in coll.all_objects:
        # default rig name: 'RIG-rex' / 'RIG-Rex'
        if obj.type != "ARMATURE":
            continue

        if not obj.name.startswith("RIG"):
            continue

        valid_rigs.append(obj)

    if not valid_rigs:
        return None

    elif len(valid_rigs) == 1:
        logger.info("Found rig: %s", valid_rigs[0].name)
        return valid_rigs[0]
    else:
        logger.error("%s found multiple rigs %s", coll.name, str(valid_rigs))
        return None


def ensure_name_version_suffix(datablock: Any) -> Any:
    version_pattern = r"v\d\d\d"
    match = re.search(version_pattern, datablock.name)

    if not match:
        datablock.name = datablock.name + ".v001"

    return datablock


def get_valid_collections(context: bpy.types.Context) -> List[bpy.types.Collection]:
    valid_prefixes = ["CH-", "PR-"]
    valid_colls: List[bpy.types.Collection] = []

    for coll in context.scene.collection.children:
        if coll.name[:3] not in valid_prefixes:
            continue
        valid_colls.append(coll)

    return valid_colls

def is_multi_asset(asset_name: str) -> bool:
    if asset_name.startswith('thorn'):
        return True
    multi_assets = ["sprite", "snail", "spider"]
    if asset_name.lower() in multi_assets:
        return True
    return False

def gen_action_name(coll: bpy.types.Collection):
    action_prefix = "ANI"
    asset_name = find_asset_name(coll.name).lower()
    asset_name = asset_name.replace(".", "_")
    version = "v001"
    shot_name = get_shot_name_from_file()

    action_name_new = f"{action_prefix}-{asset_name}.{shot_name}.{version}"

    if is_multi_asset(asset_name):
        action_name_new = f"{action_prefix}-{asset_name}_A.{shot_name}.{version}"

    return action_name_new
