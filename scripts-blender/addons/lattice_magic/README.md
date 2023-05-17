# Lattice Magic
This addon adds some Lattice-based utilities to Blender. 

![Lattice Magic UI](/media/addons/lattice_magic/lattice_magic.png)

## Table of Contents

- [Installation](#installation)
- [Tweak Lattice](#tweak-lattice)
    - [Parenting](#parenting)
    - [Deletion](#deletion)
    - [Adding/Removing meshes](#addingremoving-meshes)
    - [Going under the hood](#going-under-the-hood)
- [Camera Lattice](#camera-lattice)
    - [Creation](#creation)
    - [Parenting](#parenting-1)
    - [Animation](#animation)
    - [Deletion](#deletion-1)


### Installation
1. Clone repository `git clone https://projects.blender.org/studio/blender-studio-pipeline.git`
2. From the root of the repository navigate to `/scripts-blender/addons/`
3. Find the the `lattice_magic` folder. Place this folder in your Blender addons directory or create a symlink to it.
4. After that, you can find the Lattice Magic panel in the 3D Viewport's Sidebar, which you can bring up by pressing the N key.  


## Tweak Lattice
Tweak Lattice lets you create a lattice setup at the 3D cursor to make deformation adjustments to the selected objects.  

![How to Tweak Lattice](/media/addons/lattice_magic/tweak_lattice.gif)

### Parenting
This is meant to be possible to be used in conjunction with a character rig: Before pressing the "Create Tweak Lattice" button, simply select the desired parent rig object and bone in the UI.

### Deletion
If you want to delete a lattice, don't just delete the empty object that was created for you. This would leave behind a big mess of broken modifiers and drivers which will cause tremendous error printing spam in your console/terminal. Instead, use the "Delete Tweak Lattice" button.

### Adding/Removing meshes
When creating a lattice, it will affect all mesh objects which were selected at the moment of its creation.  

If you want more meshes to be influenced by a lattice, you don't need to delete it and re-create it with a different selection. Just select the objects you want to add to or remove from the lattice's influence, then finally select the lattice control. There will now be an "Add Selected Objects" and "Remove Selected Objects" button.  

### Going under the hood
With the lattice control selected, you can see a "Helper Objects" section in the UI. This lists two objects which are taking care of things under the hood. If you want, you can enable them with the screen icon, which will let you mess with them. This should rarely be necessary though, and you should only do it at your own risk, since there's no way to get these back to their original states once modified.


## Camera Lattice
Camera Lattice lets you create a lattice in a camera's view frame and deform a character (or any collection) with the lattice.

![Camera Lattice Demo](/media/addons/lattice_magic/camera_lattice.gif)

### Creation
Add an entry to the Camera Lattice list with the + icon. Each entry corresponds to deforming a single collection with a single lattice object from the perspective of a single camera.  

You must select a collection and a camera, then hit Generate Lattice. Note that you cannot change the resolution after the fact, so find a resolution that you're happy with, as you will be locked into that.  

### Parenting
On creation, the lattice is parented to the camera. You can feel free to remove or change this parenting to your heart's desire, it shouldn't cause any issues. The lattice object also has a Damped Track constraint, the same applies there: You can remove it if you want.  

Just remember, there's no reset button for these sort of things.

### Animation
Feel free to animate the lattice in object mode as you wish, although unless the above mentioned Damped Track constraint is enabled, you will only be able to rotate it on one axis.  

Animating the lattice's vertices is possible using shape keys. The addon provides some UI and helper operators for this, but at the end of the day it's up to you how you organize and keyframe these shape keys.
The intended workflow is that a shape key should only be active for a single frame. To help with this, shape keys are named when they are added, according to the current frame. There are also some buttons above the list:
- Zero All Shape Keys: Operator to set all shape key values to 0.0. This does not insert a keyframe!  
- Keyframe All Shape Keys: Operator to insert a keyframe for all shape keys on the current frame with their current value.  
- Update Active Shape Key: Toggle to automatically change the active shape key based on the current frame. Useful when switching into edit mode quickly on different frames.  

Note that Blender is not capable of displaying the effect of multiple shape keys on a lattice at the same time, which is another reason to go with the intended workflow, since that will always only have one shape key active at a time.


### Deletion  
Similar to Tweak Lattice, never ever delete a lattice setup by simply pressing the X or Del keys, as this will leave behind a huge mess. Instead, use the "Delete Lattice" button, or the "-" button in the top list.  


### TODO
Some ideas that could be implemented for Camera Lattice:
- Automatically inserting new shape key in the correct place in the list. Eg., when Frame 1 and Frame 10 already exist, creating a shape key on Frame 5 should insert it in between them.  
- Adding or removing objects to the influence of the lattice is not currently possible.  