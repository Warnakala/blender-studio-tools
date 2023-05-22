# Asset Publishing

::: warning Legacy Documentation
This is a legacy document originally written by Andy in 2019 as part of the Spring production retrospective.
:::

**In a nutshell, a publish is the outcome of a process or task.** We introduce publishing into our workflow for the following reasons:

- Formalizing what the output of a given task is.
- Separate working versions from used assets to keep files lighter and to remove confusing content that might be relevant to the working conditions in the file, but not for the next step in the production chain.
- File consistency checks to keep files cleaner

There are different possible scenarios to implement this in our work:

- Simplest way: Copy to new location with check and file cleanup for keeping file sizes to a minimum.
- For libraries: Push individual asset to larger collection file.
- More complicated way: Merge files which are associated with the same asset together into the final linkable asset.
    
![Pipeline](/media/archive/pipeline-proposal-2019/pipeline_proposal.png)

There is no direct link to files that are being worked on. 
    

# Possible Applications

Most studios use publishing as a form of version control. Since we currently use SVN for that (which does not scale well for larger productions) it's not immediately necessary to create a full fledged publishing system. 

To serve as a testing ground, we can limit this to the following tasks and find out where it can be useful in the future. This can also be limited to hero assets that have a more complicated creation process.

## Characters

Task result: link-able asset file with collections.

![Pipeline](/media/archive/pipeline-proposal-2019/publish_char.png)

## Pose library

Task result: Action datablock that can be referenced from animation files.

![Pipeline](/media/archive/pipeline-proposal-2019/publish_poselib.png)

## Props, envs and sets

Task result: link-able asset file with collections.

![Pipeline](/media/archive/pipeline-proposal-2019/publish_asset.png)


# File cleanup

The goal is to remove clutter from files and reduce file-size and loading time. Prevent missing textures and links to files which are not in the project.

- remove orphan data from file.
- remove lights and world.
- remove animation data not associated with drivers and pose libs.
- detect paths outside the project tree (and not /render). Links to /shared are cleaned as well.
- remove collections that are used as helpers, do not deform and are not rendered.
