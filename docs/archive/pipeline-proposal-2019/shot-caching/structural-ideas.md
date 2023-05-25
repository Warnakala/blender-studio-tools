# Structural Ideas

::: warning Legacy Documentation
This is a legacy document originally written by Andy in 2019 as part of the Spring production retrospective.
:::

![Anim](/media/archive/pipeline-proposal-2019/cosmos_shot_caching_notes.png)


**Anim.cache.view**: exactly what the animator sees during animation. Good for faster playblasts (e.g. when there are groups of chars in a shot) and verifying correct bake (debugging).

**Anim.cache.sim**: Only objects that are needed to create interaction during sim (collision, flow,..._)

**Anim.cache.lighting**: Similar to render but with less dense geo and less hair (faster viewport feedback during lighting)

**Anim.cache.render**: geometry used in final rendering. Hair particles at final density

- Could be possible to put this data all in one cache file, and only read certain parts of it. Or even create collections in import to manage their visibility.
- Alternatively there could only be .view and .render caches.
    - Lighting file then needs a way to simplify .render cache for faster viewport performance.
- Writing performance is important. We might not want to generate the entire high res cache when only sim interaction objects are needed for example.

### Ideas on structuring character assets

This time they may need to be structured in a certain way to allow for caching different parts of the asset.

Collection layout could be:

![Anim](/media/archive/pipeline-proposal-2019/image3.png)


### Anim file creation notes (unrelated to caching)

- How to handle collection visibility in anim file?
    - In the past animators found collection setup confusing, they need simplicity and less items in subcollections.
    - Char e.g. should only consist of 2 elements: geo and rig. Easier for animator to handle
- Is it possible to create automatic overrides without having to instance the collection
    - Select collection instance -> Make Library Override is currently the only way
- Caches should be linked to SVN revision or at least we should be able to identify where it came from in the history
- The animator is not allowed to move collections within the main asset hierarchy which is linked into the blend file. Otherwise the override fails to update in the future
- We have to be careful how overrides are made. If it happens without purging orphan data in the blend file, it can happen that objects get different names (numbering with .002, etc). In that case, alembic import will most likely fail to match names. (e.g. if an existing cache is re-exported but with different object naming)

### Lighting File and rendering notes

- How to put linked materials back on ABC import?
    - works: link in materials, import alembic
    - Hair material is left out
- Cycles visibility needs to be restored in imported objects
    - For example, victor’s corneas were set to only render in camera. This avoids shadow casting on the eyeball. On import victor’s eyes were black because visibility wasn’t set.
- Particles are currently still lagging one frame behind
- Are ABC curves rendered as cycles hair?
    - What about intercept, parent mesh UV, etc
- Render resolution is used by default, needs automation before export to cache different resolutions
- Vertex group and face sets should be on in export to make materials work properly
- Camera cache needs animation of properties
- How are material drivers (rig influences shading) handled?
- Hair curves do not get emitted from render resolution mesh if export caps subdivision at 0. This causes issues with dense, short fur for example. The origin of the particle has to be on the high res mesh
- Animation cache can exclude particle hair
    - Blender’s hair system does not work with cached hair
