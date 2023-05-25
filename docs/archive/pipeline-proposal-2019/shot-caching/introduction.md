# Shot caching

::: warning Legacy Documentation
This is a legacy document originally written by Andy in 2019 as part of the Spring production retrospective.
:::

Currently Alembic caching is limited to deformed meshes and position of objects. Hair is not fully implemented as the resulting hair curves cannot be handled by Blender's particle system. That means, it's not possible to simulate or use the more advanced shading parameters of particle hair geometry in Cycles.

This is a proposal of how to handle caching of animated characters, while at the same time enabling us to simulate the hair in the conventional way.

![Shot Builder](/media/archive/pipeline-proposal-2019/shot_caching.png)


### Animation file

1. Animator chooses which characters or props to cache
2. Subsurf is disabled on all objects in the asset
3. For each asset (char, prop), one cache file is created per shot
4. in the caching options, hair curves should be disabled.
5. The renderfarm generates a play-blast of the shot together with cache and puts each into the right directory.

### Simulation file

1. Sim-file links in hair emitter meshes that need to be simulated
2. Hair emitters get stripped of all deforming modifiers
3. Add mesh sequence cache modifier on hair emitter mesh in place of the previous deforming modifiers and load the animation cache into it.
4. Subsurf modifier is retained, has to be at the same resolution as render level for sim bake (!)
5. Do hair dynamics bake, perform to disk cache (to /render), results in a directory full of bphys files.

### Lighting file

1. Link all assets that were originally cached in anim file as full collection hierarchies
2. Make all objects local (only objects, material updates should thus be still reflected in the file). (Or use Overrides once possible).
3. Strip objects of all deforming modifiers.
4. Add mesh sequence cache on all objects before subsurf, hair particles should still be intact
5. On hair systems that were simulated, check 'hair dynamics' and load the bphys cache from render
6. This should result in the render meshes following the abc cache and particle systems following the bpys cache.

More notes and research on how we can do caching currently:

[Proof of concept Add-on](https://www.notion.so/Proof-of-concept-Add-on-7f7b3686ab234c6f9daa54ff1db07c48)

[Issues and show-stoppers in Blender](https://www.notion.so/Issues-and-show-stoppers-in-Blender-de90bbaed4cc4580a4462cfd2f7f6c4c)
