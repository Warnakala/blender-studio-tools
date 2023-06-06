import bpy
from blender_kitsu.shot_builder.hooks import hook, Wildcard
from blender_kitsu.shot_builder.asset import Asset
from blender_kitsu.shot_builder.shot import Shot
from blender_kitsu.shot_builder.project import Production

import logging

logger = logging.getLogger(__name__)

# ---------- Global Hook ----------


@hook()
def set_cycles_render_engine(scene: bpy.types.Scene, **kwargs):
    """
    By default we set Cycles as the renderer.
    """
    scene.render.engine = 'CYCLES'


# ---------- Overrides for animation files ----------

@hook(match_task_type='anim')
def task_type_anim_set_workbench(scene: bpy.types.Scene, **kwargs):
    """
    Override of the render engine to Workbench when building animation files.
    """
    scene.render.engine = 'BLENDER_WORKBENCH'

# ---------- Create output collection for animation files ----------


def _add_camera_rig(
    scene: bpy.types.Scene,
    production: Production,
    shot: Shot,
):
    """
    Function to load the camera rig. The rig will be added to the output collection
    of the shot and the camera will be set as active camera.
    """
    # Load camera rig.
    path = f"{production.path}/lib/cam/camera_rig.blend"
    collection_name = "CA-camera_rig"
    bpy.ops.wm.link(
        filepath=path,
        directory=path + "/Collection",
        filename=collection_name,
    )
    # Keep the active object name as this would also be the name of the collection after enabling library override.
    active_object_name = bpy.context.active_object.name

    # Make library override.
    bpy.ops.object.make_override_library()

    # Add camera collection to the output collection
    asset_collection = bpy.data.collections[active_object_name]
    shot.output_collection.children.link(asset_collection)

    # Set the camera of the camera rig as active scene camera.
    camera = bpy.data.objects['CAM-camera']
    scene.camera = camera


@hook(match_task_type='anim')
def task_type_anim_output_collection(scene: bpy.types.Scene, production: Production, shot: Shot, task_type: str, **kwargs):
    """
    Animations are stored in an output collection. This collection will be linked
    by the lighting file.

    Also loads the camera rig.
    """
    output_collection = bpy.data.collections.new(
        name=shot.get_output_collection_name(shot=shot, task_type=task_type))
    shot.output_collection = output_collection
    output_collection.use_fake_user = True

    _add_camera_rig(scene, production, shot)


@hook(match_task_type='lighting')
def link_anim_output_collection(scene: bpy.types.Scene, production: Production, shot: Shot, **kwargs):
    """
    Link in the animation output collection from the animation file.
    """
    anim_collection = bpy.data.collections.new(name="animation")
    scene.collection.children.link(anim_collection)
    anim_file_path = shot.get_anim_file_path(production, shot)
    anim_output_collection_name = shot.get_output_collection_name(
        shot=shot, task_type="anim")
    result = bpy.ops.wm.link(
        filepath=anim_file_path,
        directory=anim_file_path + "/Collection",
        filename=anim_output_collection_name,
    )
    assert (result == {'FINISHED'})

    # Move the anim output collection from scene collection to the animation collection.
    anim_output_collection = bpy.data.objects[anim_output_collection_name]
    anim_collection.objects.link(anim_output_collection)
    scene.collection.objects.unlink(anim_output_collection)

    # Use animation camera as active scene camera.
    camera = bpy.data.objects['CAM-camera']
    scene.camera = camera


# ---------- Asset loading and linking ----------


@hook(match_task_type='anim', match_asset_type=['char', 'props'])
def link_char_prop_for_anim(scene: bpy.types.Scene, shot: Shot, asset: Asset, **kwargs):
    """
    Loading a character or prop for an animation file.
    """
    collection_names = []
    if asset.code == 'notepad_pencil':
        collection_names.append("PR-pencil")
        collection_names.append("PR-notepad")
    else:
        collection_names.append(asset.collection)

    for collection_name in collection_names:
        logger.info("link asset")
        bpy.ops.wm.link(
            filepath=str(asset.path),
            directory=str(asset.path) + "/Collection",
            filename=collection_name,
        )
        # Keep the active object name as this would also be the name of the collection after enabling library override.
        active_object_name = bpy.context.active_object.name

        # Make library override.
        bpy.ops.object.make_override_library()

        # Add overridden collection to the output collection.
        asset_collection = bpy.data.collections[active_object_name]
        shot.output_collection.children.link(asset_collection)


@hook(match_task_type=Wildcard, match_asset_type='sets')
def link_set(asset: Asset, **kwargs):
    """
    Load the set of the shot.
    """
    bpy.ops.wm.link(
        filepath=str(asset.path),
        directory=str(asset.path) + "/Collection",
        filename=asset.collection,
    )
