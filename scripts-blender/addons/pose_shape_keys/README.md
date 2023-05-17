# Pose Shake Keys

## Table of Contents
- [Installation](#installation)
- [Basic Workflow](#basic-workflow)
- [Example Use Cases](#example-use-cases)


This addon lets you create shape keys that blend already deformed meshes into a previously stored shape.
It also lets you manage multiple copies of a shape key together. Each copy can have a different vertex group mask, or be applied mirrored around the X axis.

You can find a detailed video tutorial on how to download, install and use the addon [here](https://studio.blender.org/training/blender-studio-rigging-tools/pose-shape-keys/).

## Installation
1. Clone repository `git clone https://projects.blender.org/studio/blender-studio-pipeline.git`
2. From the root of the repository navigate to `/scripts-blender/addons/` 
3. Find the the `pose_shape_keys` folder. Place this folder in your Blender addons directory or create a sym link to it.


## Basic Workflow:
- Create a pose whose deformation you want to correct. A pose is defined as an Action and a frame number.
- Create a Pose Key on the deformed mesh. Assign the action and the frame number.
- Press "Store Evaluated Mesh". This will create a copy of your mesh with all deformations applied.
- Sculpt this mesh into the desired shape.
- Go back to the deformed mesh, and assign one or more Shape Keys to the Pose Key.
- Press "Set Pose" to ensure that the rig is in the pose you created and specified earlier.
- Press "Overwrite Shape Keys".
- When you activate your shape key, your deformed mesh should now look identical to your sculpted shape.
- If you have more than one shape key, the same data will be pushed into each. 
The purpose of this is that each copy of the shape key have a different mask assigned to it.
This can streamline symmetrical workflows, since you can push to a left and a right-side shape key in a single click.

# Example use cases:

### 1. Sculpted facial expressions applied directly on top of a bone deformation based rig:
- A character artist can sculpt facial expressions to great quality and detail
- You pose the rig to be as close to this sculpted shape as possible, and create
a rig control that blends into this pose using Action Constraints.
- Using the addon, create corrective shape keys that blend your posed mesh into 
the shape of the sculpt.
- Hook up those corrective shape keys to the rig via drivers
- You now have the precise result of the sculpted facial expression, while retaining
the freedom of bone-based controls that can move, scale and rotate!

### 2. Author finger correctives 24 at a time:
- Create a pose where all fingers are bent by 90 degrees at the first joint.
- Create a Pose Key and a storage object, and sculpt the desired deformation result.
- On the rigged mesh, create 24 shape keys within the PoseKey; One for each section of each finger.
- Assign vertex groups to them that mask each finger.
- Normalize the vertex masks.
- Now you can push the sculpted hand shape into all 24 shape keys at the same time.
- Create drivers so each shape key is driven by the corresponding finger bone.
- You can now tweak and iterate on the sculpted shape, and update all 24 shape keys
with the click of a single button.

