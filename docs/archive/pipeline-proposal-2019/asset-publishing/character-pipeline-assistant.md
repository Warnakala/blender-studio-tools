# Character Pipeline Assistant

::: warning Legacy Documentation
This is a legacy document originally written by Andy in 2019 as part of the Spring production retrospective.
:::

![Character Pipeline](/media/archive/pipeline-proposal-2019/char_pipeline_01.png)

Jan 2021

# Proposal for updated version for 'Sprite Fright' (August 2020)

With the Sprite Fright project starting to get into a phase where the characters are being designed and tested for shading, rigging and animation, a solid character pipeline will become necessary soon.

So we (Demeter and Simon) re-evaluated the character update tool made for the Settlers project on how applicable it is and how it can be adapted to be more flexible and stable.

So we came up with the following proposal:

## Idea

The idea is the same as was implemented for Settlers but allowing an additional step of adjusting the mesh. For this an additional publishing step is introduced to export the model in a way that makes it easily mergeable with the rig (merging objects, applying mirror modifiers etc).

## File Structure

Character folder including:

- char.modeling.blend (working file)
- char.geometry.blend (source file) → published from char.modeling.blend
- char.rigging.blend (working file/ source file) → sourcing char.geometry.blend
- char.shading.blend (working file/ source file) → sourcing char.geometry.blend
- char.blend (master file) → published from char.rigging.blend and char.shading.blend

![Character Pipeline](/media/archive/pipeline-proposal-2019/char_pipeline_02.png)


(Green Blocks are working files, grey files are not worked in, but only procedurally updated)

## Data Flow

### Geometry

The model of the character is appended from char.modeling.blend as a collection into char.geometry.blend, where all adjustments to the mesh, that have to be made for rigging, are reproducibly automated.

This automation has to be manually revised depending on the rig and can be specified as a script in the char.geometry.blend file.

Rigging and Shading file take the geometry directly from the published model version in char.geometry.blend.

The master file takes...

...from the geometry file (option A):

- mesh data / multires data / displacement maps

...from the rigging file:

- mesh data / multires data / displacement maps (option B)
- armature
- modifier stack
- weight paint layers
- shape keys
- drivers
- physics properties
- support objects

...from the shading file:

- material slots
- shaders
- UV layers
- vertex color layers

However, the master file can also source the data from itself, as to only use published states of shading/rigging, without drawing from work-in-progress states of the respective files.

That way every department has an individual control over publishing their updates.

## Scripts

For the automation of updating the different versions of a character in the respective files a couple of scripts are necessary, that can largely be based on the first version implemented for 'Settlers'.

The necessary scripts are:

- publish geometry + support adjustable script to specify necessary changes (merging objects, applying modifers, etc.)
- import geometry and merge with rigging file
- import geometry and merge with shading file
- import and merge all  into master file

To be able to easily update the individual scripts across multiple characters, we are proposing to create an add-on that includes all the functionality and can be maintained and pulled via git.

## Example workflow:

- Julien makes a change in the modeling file that is not significant to the vertex order of the mesh
- Demeter and Simon can work in their respective files simultaneously with no restrictions
- Julien publishes his changes to the geometry by pressing the update button in the geometry file
- To import the changes into their working files, Demeter and Simon press the update buttons in their respective files and
- Once a significant change has been made that should be passed to the animation department, Julien, Demeter, Simon (or whoever) updates the master file and commits it to the SVN

## Benefits

- Flexible, simultaneous work to a certain degree
- High level of automation
- Publishing steps for individual version control per department

## Potential Issues

This pipeline relies heavily on the fact that object names and vertex order don't change. But the additional publishing step of the geometry allow manual interference when something goes wrong and optionally the data-transfer modifier can be used to prevent data from breaking due to vertex order.

However, to avoid issues like that, this pipeline should only be picked up after major geometry changes likes adding or removing vertices in the base mesh.

This pipeline is assuming that there are no driver dependencies on the rig in the shader. However, if that should be the case (as it was for 'Settlers'), it can be adjusted to retain that dependency.

## Alternatives

A potential alternative could be using library overrides to link between files instead of appending and only using one single publishing step in the master file. However, this is not feasible with the current, early state of library overrides, as a high level of functionality would be required.

---

# First version from Settlers (April 2020)

This proof of concept for publishing was created by Simon Thommes during the settlers project. It merges rigging and shading files into a final asset blend file.

![Character Pipeline](/media/archive/pipeline-proposal-2019/3-character_pipeline_tool.mp4)


### Target **Workflow**

Separate working files for modelling, rigging and shading that are automatically merged in a single character.blend asset file. This allows for working in parallel and introduces an additional publishing step for each module.

## **Current state (Settlers)**

Video breakdown of functionality for version 1 (Not the latest iteration):

[https://cloud.blender.org/p/settlers/5ea02055cc64ecf31415351c](https://cloud.blender.org/p/settlers/5ea02055cc64ecf31415351c)

## Features

- merging .rig.blend and .shading.blend files
- updating either [rig + geometry] or [shading] separately
- merging the following data by object name
    - From the .rig file:
        - Mesh, Armature, Weight Paint, Modifiers, Constraints, etc.
    - From the .shading file:
        - Materials by slot
        - UVs by layer name and vertex order
        - VCols by layer name and vertex order
- updating shading drivers pointing to rig objects
*(all drivers within nodegroups using the naming convention DR-'object_name' get repointed to the object 'object_name')*

## Shortcomings

- system is fragile regarding name changes
- data-blocks worked on by multiple modules are not easily mergeable
- python scripts are accumulated with .### notation

## Potential features

- Outsourcing the mesh data to the .modeling file and transferring rigging data by vertex order
- Overwriting modifier settings relevant for shading from the .shading file (e.g. mirrored UVs)
