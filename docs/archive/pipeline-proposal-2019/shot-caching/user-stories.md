# Caching workflow user stories

::: warning Legacy Documentation
This is a legacy document originally written by Andy in 2019 as part of the Spring production retrospective.
:::

This is a list of potential ways of caching an animation to Alembic and then reading it back from another file.

## Without hair cache

### Anim file

1. Animator chooses which characters or props to cache
2. Subsurf is disabled on all objects in the asset
3. For each asset (char, prop), one cache file is created per shot
4. Farm generates playblast of the shot together with cache and puts each into the right directory

![Anim](/media/archive/pipeline-proposal-2019/01_02_01_D2.anim_contact.mp4)

### Lighting File

1. Lighting file is set up and is aware what assets are associated with its shot
2. Materials from assets get linked in from original asset files so they get applied correctly on objects
3. Caches get imported into lighting file
4. Restore collection hierarchy from asset files
5. Restore object cycles visibility from asset files
6. Restore Subsurf modifiers
7. Lighting artist can choose whether they want to see low res preview or final render resolution assets

![Lighting](/media/archive/pipeline-proposal-2019/01_02_01_D2.lighting1.mp4)

### Sim File

1. Simulation file loads sim interaction cache (for example to let hair collide with head. Or smoke collide with character)
2. Sim artist defines influence of cache objects in scene
3. Export sim cache to shot folder location

![Sim](/media/archive/pipeline-proposal-2019/01_02_01_D2.sim1.mp4)

### Lighting File

1. Import sim cache into lighting file.

*Note that this example does not include hair simulation. This cannot be done with alembic currently. In order to enable hair sim, emitters need to be cached, then the particle data has to be transferred back. After that, blender can simulate the hair to its own internal cache system. The resulting sim can be linked to lighting as a collection.*

---

## Alternate solution for using simulated hair in the lighting stage

### Sim File

- Link character collection from the animation file
- make hair particle emitters local (on object level) and enable hair dynamics
- add force fields and effectors and do the simulation
- bake the sim into blender's hair sim cache

---

## Very Adventurous Cache Method That Might Work ™

This is the short version without putting objects into collections. All the steps can be automated for more convenience. Needs further research to see if particles deform correctly with subsurf cache objects.

### Anim file

1. Cache is written from anim file as usual (select objects to cache, export ABC) all on subsurf 0

### Sim File

1. sim file links in hair emitter meshes that need to be simulated
2. hair emitters get stripped of all deforming modifiers
3. subsurf modifier is retained, has to be at the same resolution as render level for sim bake (!)
4. Do hair dynamics bake, perform to disk cache (to render), results in a directory full of bphys files.

### Lighting File

1. lighting file links all objects that were originally cached in anim file
2. make all objects local (only objects, material updates should thus be still reflected in the file)
3. strip objects of all deforming modifiers
4. add mesh sequence cache on all objects before subsurf, hair particles should still be intact
5. on hair systems that were simulated, check 'hair dynamics' and load the bphys cache from render
6. this should result in the render meshes following the abc cache and particle systems following the bpys cache.

![Sim](/media/archive/pipeline-proposal-2019/01_02_01_D2.lighting.adventurous_cache.mp4)

