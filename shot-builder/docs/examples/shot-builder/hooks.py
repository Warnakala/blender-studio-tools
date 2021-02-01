import bpy
from shot_builder.hooks import hook, global_hook, Wildcard
from shot_builder.asset import Asset


@hook()
def set_cycles_render_engine(scene: bpy.types.Scene, **kwargs):
    scene.render.engine = 'CYCLES'


@hook(match_task_type='anim')
def task_type_anim_set_workbench(scene: bpy.types.Scene, **kwargs):
    scene.render.engine = 'BLENDER_WORKBENCH'


@hook(match_task_type='anim', match_asset_type="char,props")
def link_char_prop_for_anim(scene: bpy.types.Scene, asset: Asset, **kwargs):
    bpy.ops.wm.link(
        filepath=str(asset.path),
        directory=str(asset.path) + "/Collection",
        filename=asset.collection,
    )


@hook(match_task_type=Wildcard, match_asset_type='sets')
def link_set(scene: bpy.types.Scene, asset: Asset, **kwargs):
    bpy.ops.wm.link(
        filepath=str(asset.path),
        directory=str(asset.path) + "/Collection",
        filename=asset.collection,
    )
