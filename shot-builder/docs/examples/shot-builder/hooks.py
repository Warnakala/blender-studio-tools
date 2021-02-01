import bpy
from shot_builder.hooks import hook, Wildcard
from shot_builder.asset import Asset
from shot_builder.shot import Shot


@hook()
def set_cycles_render_engine(scene: bpy.types.Scene, **kwargs):
    scene.render.engine = 'CYCLES'


@hook(match_task_type='anim')
def task_type_anim_set_workbench(scene: bpy.types.Scene, **kwargs):
    scene.render.engine = 'BLENDER_WORKBENCH'


@hook(match_task_type='anim')
def task_type_anim_output_collection(shot: Shot, task_type: str, **kwargs):
    """
    Animations are stored in an output collection. This collection will be linked
    by the lighting file.
    """
    output_collection = bpy.data.collections.new(
        name=f"{shot.sequence_code}_{shot.code}.{task_type}.output")
    shot.output_collection = output_collection


@hook(match_task_type='anim', match_asset_type=['char', 'props'])
def link_char_prop_for_anim(shot: Shot, asset: Asset, **kwargs):
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
    bpy.ops.wm.link(
        filepath=str(asset.path),
        directory=str(asset.path) + "/Collection",
        filename=asset.collection,
    )
