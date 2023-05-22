# Pipeline proposal 2019

::: warning Legacy Documentation
This is a legacy document originally written by Andy in 2019 as part of the Spring production retrospective.
:::

This is a proposal of what we can do in the near future to make film production in our studio smoother. It's clear that with our limited resources we cannot implement absolutely every method. Hence, we are first going to focus on optimizing our main production cycles.

Everything noted here should be possible with the current version (with minor improvements and fixes). To handle the complexities of a production, some development needs to happen in the override system.

The graphic below simplifies the production timeline significantly for the sake of clearer communication. We can separate production into two parts: **Asset creation** (chars, props, libs and sets) and **Shot production cycles** (layout, shot building, animation, lighting, etc). 

![Production Timeline](/media/archive/pipeline-proposal-2019/production_timeline.png)

Layout and story-boarding are currently left out as a target of this proposal*,* developing a robust layout workflow requires additional work. We currently assume that layout is done per-sequence like in *Spring* and delivered as a series of edited shots or grease-pencil files. 

This document aims to improve our efficiency during shot cycles by also addressing issues during set-up during pre-production and asset creation. 

# The main issues

Here are the main problems we faced in the past in the most generalized way possible. 

## Too much manual work

Artists should focus on the quality and the artistic goals of their everyday work, not the technical aspects. Manual naming and set-up of files have in the past left a lot of room for human errors that trickle down the process. Since our staff is limited, this manual work has been responsible for numerous bottlenecks. Manual labour currently includes (but isn't limited to):

- Shot creation
- Naming of assets, scenes, shots, takes
- Play-blasting of animation to multiple locations for approval and passing-along
- Setting names for directories
- Keeping track of assets statuses
- Browsing assets and linking
- Passing animation data along to lighting
- Keeping layout cameras synchronized with sets and shots
- Synchronizing constraints and relationships between objects in animation, simulation and lighting.

## Unclear communication and approval process

There has not been a single place to track the planning of production related tasks. Attract is meant to fill in that role, but still has limited functionality that needs the be expanded. For projects with around 8 people on-site it is already vital to have a communication tool to keep track of each person's jobs, reviewing work and pushing it further into the next department. It gets more tricky once people are off-site, on different time zones and cannot communicate in real-time.

- pushing tasks to next line of the process depends on direct communication
- extra overhead with external team members
- review is not streamlined for quick access
- order of production steps is not clearly defined and optimized (see Spring anim post mortem)
- There should be a clear responsibility per task. (see Coffee Run 2K issue)

## Work files and results are mixed together

For the past 10 years, Open Movie productions have heavily relied on linking rigged characters and assets directly into shots. Updates in the process always trickle down instantly. This make changes more immediate, but can also break files very often. A change in an asset can make partial re-renders of shots impossible. If the rigger breaks the rig with a commit, the animator cannot work and is interrupted until the file is either reverted or fixed. The question is whether the benefits of direct linking outweigh the delays caused by broken files.

## Scaling up

As a result of the points mentioned above, it is very difficult to scale up our current production methods to accommodate for productions larger than 50 shots. This proposal aims for letting us handle multiple productions with more than 100 shots each. We should aim to make it robust enough to handle a feature film production. 

# Proposed solutions

Here are some of the possible improvements. Jump to the sub-pages to read more.

## Improved production tracking

Communication is the most important task during a production. By improving our task tracking tool *Attract* we can make sure that there is a basic tool set for people to know what they have to do, how much time they have for it, and what the context of their work is. 

Sharing our production tools is the main business model of the Blender Cloud, it is very important that we give this goal a higher priority. 

[Attract improvements](attract-improvements)

## Automation

We have to make clearer steps towards automating tasks that require a higher degree of precision. Also repetitive jobs like creating files for people to edit (e.g. anim prep) or cleaning up scenes can easily be done by scripts and add-ons. 

We should also strive to automate communication tools like reviewing rendered media; an animator should not have to worry about where to save a play-blast (or create the location if necessary), they only have to initiate it, but then the system takes care of storing it and notifying the reviewers. 

[Task Companion Add-on](task-companion-addon)

## Caching animation

In the past we have exclusively relied on Blender's linking system to bring animated characters into a file where they can be lit and rendered. Linking of data-blocks in and between scene files is one of the strengths of Blender and should still be used to its full potential in the future. However, when everything is linked, everything can change and break at once. At some point the links have to be broken to produce repeatable operations. 

Using either Alembic or USD to write animation data to caches means we can keep shading and grooming linked, but we do not rely on the rig or constraints set up by the animator. Once animation in a shot has been approved, it can be cached to be reliably repeatable during rendering. 

[Shot caching](shot-caching/introduction)

## Publishing

It's a common concept in the industry and means more than just committing your changes to SVN. We should still keep our files version controlled, but introduce an additional step at the end to 'publish' the changes made. 

Published assets exist next to version controlled working files. This makes it easier to **pinpoint outputs of tasks**. The artist clearly defines when their work is pushed forward in the process.

[Asset Publishing](asset-publishing/introduction))
