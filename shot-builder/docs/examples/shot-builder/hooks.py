import bpy
from shot_builder.hooks import hook, Wildcard
from shot_builder.asset import Asset
from shot_builder.shot import Shot
from shot_builder.project import Production


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
    Helper Function to load the camera rig.
    """
    # Load camera rig.
    path = f"{production.path}/lib/cam/camera_rig.blend"
    collection_name = "CA-camera_rig"
    bpy.ops.wm.link(
        filepath=path,
        directory=path + "/Collection",
        filename=collection_name,
    )
    # Add camera collection to the output collection
    asset_collection = bpy.data.collections[collection_name]
    shot.output_collection.children.link(asset_collection)
    # Set the camera of the camera rig as active scene camera.
    scene.camera = bpy.data.objects['CAM-camera']


@hook(match_task_type='anim')
def task_type_anim_output_collection(scene: bpy.types.Scene, production: Production, shot: Shot, task_type: str, **kwargs):
    """
    Animations are stored in an output collection. This collection will be linked
    by the lighting file.

    Also loads the camera rig.
    """
    output_collection = bpy.data.collections.new(
        name=f"{shot.sequence_code}_{shot.code}.{task_type}.output")
    shot.output_collection = output_collection

    _add_camera_rig(scene, production, shot)

# ---------- Asset loading and linking ----------


@hook(match_task_type='anim', match_asset_type=['char', 'props'])
def link_char_prop_for_anim(shot: Shot, asset: Asset, **kwargs):
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
        if collection_name not in bpy.data.collections:
            bpy.ops.wm.link(
                filepath=str(asset.path),
                directory=str(asset.path) + "/Collection",
                filename=collection_name,
            )
        asset_collection = bpy.data.collections[collection_name]
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
