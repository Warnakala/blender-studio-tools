# Issues and show-stoppers in Blender

::: warning Legacy Documentation
This is a legacy document originally written by Andy in 2019 as part of the Spring production retrospective.
:::

- Materials need to exist (appended or linked) in blend file before alembic import so names can be matched (could also be an automated post process)
    - *Sybrens idea: have some way to automatically (re)map materials based on name, and/or auto-create dummy materials otherwise. Still TBD.*
- Hair curves support of intercept and UV maps not clear (or non-existent)
- Particle hair currently lags one frame behind playback (and render)
- Blender’s hair simulation system does not support sim from alembic cache
    - We have to find a workaround for simulating hair, alembic curves (result of anim export) cannot be simulated
- No support for caching animated values (camera cache, driven material values)
    - *Design task in [T69046](https://developer.blender.org/T69046)*

