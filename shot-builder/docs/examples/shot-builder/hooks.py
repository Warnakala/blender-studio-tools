@shot_builder.production_settings_hook
def spring_production_settings(scene: bpy.types.Scene, **kwargs: dict) -> None:
    """
    This is an example for a `production_settings_hook`. A production
    hook contains global configuration that is applied to a shot as first.

    A production can only have a single `production_settings_hook`. When
    multiple `production_settings_hooks` are defined a configuration error
    will be given.
    """
    scene.render.resolution_x = 1920
    scene.render.resolution_y = 1080
    scene.render.resolution_percentage = 100
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = 1024


@shot_tools.hook(match_task_type='anim')
def anim_task(scene: bpy.types.Scene, **kwargs: dict) -> None:
    """
    This hook is called when animation task file is built.

    Task specific overrides to scene settings can be done.
    """
    scene.render.engine = 'WORKBENCH'
