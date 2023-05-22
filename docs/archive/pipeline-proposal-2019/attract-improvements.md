# Attract improvements

::: warning Legacy Documentation
This is a legacy document originally written by Andy in 2019 as part of the Spring production retrospective.
:::

# General goals of Attract

- Define and manage shots and film assets
- Create the relationships between shots, assets and tasks
- Task status tracking and communication both with internal and external entities
- Scheduling of tasks
- Assist with communication of external and internal team members (Review, feedback)

# During project pre-production and set-up

Attract is a communication tool. It holds and displays information relevant to production, its core elements and tasks people have to accomplish. 

The following section tries to break down the usage of Attract in production, roughly in chronological order.

![Pre Production Timeline](/media/archive/pipeline-proposal-2019/pre_production_timeline.png)

### Project definition

At the top in the hierarchy lies the project that needs to be managed. It contains relevant information which trickles down to each individual component such as:

- Frames per second
- Resolution
- Start frame (preroll) of each shot file.
- Frame Handles of each shot file.
- Viewport render presets
- Render presets
- Other Pipeline definitions
    - file paths relative to project root
    - absolute file paths
    - naming conventions
    - more

![Project Structure](/media/archive/pipeline-proposal-2019/project_structure.png)

*A project contains these items. Shots are associated with sequences. Assets are specific to each project. Tasks can be completely separate or be associated with a shot (layout, animation, lighting, etc.) or an asset (modeling, shading, rigging, etc.)*

### Editorial

While the movie is in its early stages, we already set up the **edit.blend** file. This is the starting point for Attract to know which sequences and shots are in the project. The edit defines order of shots and their length. This already works in the Blender Cloud add-on.

**We know:**

- Shot numbers
- Length or each shot
- Order of shots
- Sequences associated with shots.

### Breakdown

Once the **edit** is live, more items in the project can be defined in the web interface of Attract:

- What assets do we need
    - Tasks for each asset
    - People associated with the tasks
    - Time-frame for tasks
- Shot details
    - Which shot is associated with which assets
    - Tasks for each shot
    - Time estimation of each shot task

### Asset Creation

Once we have a list of assets, the asset itself can become a 'real' file within our production repository. Also the asset definition on Attract can communicate more details:

- Which files (collections, objects, materials) are associated with an asset.
- Variations, revisions and views

### Shot file building

Attract could provide a simple interface for creating shot files in an automated fashion. This file can be derived from predetermined templates (e.g. blend files) which can differ based on the sequence and task type.

![Shot Builder](/media/archive/pipeline-proposal-2019/shot_builder_flow.png)

### Sequence template

Typically, movie sequences differ on their environment and which characters are in them. On Spring we tried to split up the film sequences roughly based on locations. In practice, sequence templates don't define how the file is set up, but **what** can be in it.

- They define a set of assets that are needed in each shot of the sequence
- If needed there can be more than one template for a sequence.
- Two sequences can also use the same template (e.g. in *Spring,* shots from *06-stampede* started out from the same assets as *07-rescue*)
- shots can take sequence definitions as preset but are not tied to them. In the above mock up, they would just define which checks are set when the template is loaded, but users can add or remove assets.

### Task template

Files can be configured differently depending on a task. The task template defines **how** it is set up exactly. Some examples:

**Animation**

- Flatter collection hierarchy for more (and faster) control over what is visible. Each character has their own collection to control visibility. Props are split into their own collections. Rigs have their own collections as well.
- Sequence editor is set up with the latest layout render of the shot.
- Scene is set to use eevee as render engine for viewport renders on the farm.
- Lighting setup for playblasting

**Lighting**

- More generalized collection layout (characters, props, set elements, lighting, cache, etc)
- Cycles as render engine with general render presets already set as a starting point.
- Master lighting from sequence is already linked in.

# During production cycles

![Shot Builder](/media/archive/pipeline-proposal-2019/production_timeline_2.png)

During production Attract becomes the main landing page relevant information. The artists have to see at a glance:

- Which tasks are assigned to them
- What is their status?
- Overview of the deadlines
- What other tasks depend on their work
- What are crucial notes and requested changes
- Easy access to review process

Some initial ideas for organizing the interface better to help with people's day-to-day work. We have to make more detailed research on what artists need from Attract that can benefit their workflow. A big criteria is that filtering and searching of tasks should be possible with a range of customization.

## User dashboard
The landing page for the user. Displays a list of the user's current tasks and notifications. It should be possible to filter at least by type, due date and status.

![Attract Dashboard](/media/archive/pipeline-proposal-2019/attract_dashboard.png)

## Shot list
This is currently the main view of Attract: A list of all the shots in a film and their associated tasks. In the future they should be further grouped by sequences, the grouping can be collapsed. Once shots get more tasks the overview becomes very cluttered in the current layout. Hence, details of tasks and discussions should be moved to their own page. 

![Attract Shot List](/media/archive/pipeline-proposal-2019/attract_shot_list.png)

## Asset list
List of all the assets and their associated tasks, grouped by asset type.

![Attract Shot List](/media/archive/pipeline-proposal-2019/attract_asset_list.png)

## Task page
Detailed info on the task. Discussion and task related dependencies (what tasks does a shot depend on for finalizing).

![Attract Shot List](/media/archive/pipeline-proposal-2019/attract_task_page.png)


## Contact sheet
A very simple page that shows a current rendered thumbnail for each individual shot in front of dark grey background. This helps the lighting team to improve the continuity of their work.

![Attract Shot List](/media/archive/pipeline-proposal-2019/attract_contact_sheet.png)

