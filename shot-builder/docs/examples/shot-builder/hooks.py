import bpy
from shot_builder.hooks import hook, global_hook


@global_hook()
def set_cycles_render_engine(scene: bpy.types.Scene, **kwargs):
    scene.render.engine = 'CYCLES'


@hook(match_task_type='anim')
def task_type_anim_set_workbench(scene: bpy.types.Scene, **kwargs):
    scene.render.engine = 'BLENDER_WORKBENCH'
