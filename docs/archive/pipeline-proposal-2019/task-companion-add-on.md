# Task companion add-on

::: warning Legacy Documentation
This is a legacy document originally written by Andy in 2019 as part of the Spring production retrospective.
:::

We need an add-on that adapts to the current task an artist has to work on. On *Spring* and *Agent* this used to be called *Shot Tool,* it was only used for building shot files and for automation during lighting.

For the near future we should have a more general **tool that assists artist during their task.** The tool needs to be aware of what the purpose of the currently opened file is, and which task it is associated with. For this purpose it has to connect to Attract like the Blender Cloud add-on (it  could also be included in it).

**Task awareness:**

- Asset editing, animation and lighting require slightly different working methods
- Is the current file a library asset file or a shot file
- File paths associated with the task
- Naming and collection hierarchy conventions

**Shot awareness:**

- Which shot is this file associated with
- Which assets are currently used/needed in this shot
- Which assets need to be cached (and where they go to)
- What is the output of the specific shot task (cache, collection, etc) and where does it go.

# Task context

This is how the helper add-on can change based on the context.

## Asset editing

- Conform objects to naming conventions
- Create collections to set up asset variations/LODs
- Push latest render to Attract asset page for feedback.
- Publishing of the asset.
- File integrity check

## General shot context

- Fetch frame start and end updates from Attract if they have changed
- check correct file naming and output paths
- Quick access to assets that need to be linked in manually.
- Provide interface for manual switching of assets (variations/LODs)
- File cleanup

## Animation

- Creating a playblast for review.
    
    → Renders animation with eevee on the farm. Puts output to shot footage directory and posts it on task page in Attract for review)
    
- Shot publish
    
    → Cache animation to Alembic. Create Eevee render and put into shot footage directory.
    

## Simulation

- Set output directories based on type of simulation and cache

## Lighting

- loading animation caches.
- updating to newer publish of caches
- Setting render defaults
- Push latest render to contact sheet in Attract

## Editorial

- Current Blender Cloud add-on functionality (managing and sending shot definitions to Attract)
- Load shots as new clips from shared directory
- Replace shots/versions/iterations

## Shot review

- Load animation to be reviewed from Attract
- Send rendered clip (with annotations) as attachment to the relevant task page on Attract
