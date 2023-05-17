# Easy Weights


Easy Weight is an addon focused on quality of life improvements for weight painting in Blender.

## Table of Contents

- [Installation](#installation)
- [How to Use](#how-to-use)
    - [Entering Weight Paint Mode](#entering-weight-paint-mode)
    - [Weight Paint Context Menu](#weight-paint-context-menu)
    - [Hunting Rogue Weights](#hunting-rogue-weights)
    - [Vertex Group Operators](#vertex-group-operators)
    - [Force Apply Mirror Modifier](#force-apply-mirror-modifier)
- [Previous Features](#previous-features)

## Installation
1. Clone repository `git clone https://projects.blender.org/studio/blender-studio-pipeline.git`
2. From the root of the repository navigate to `/scripts-blender/addons/` 
3. Find the the `easy_weights` Place this folder in your Blender addons directory or create a symlink to it.

## How to Use
Easy Weight is an addon focused on quality of life improvements for weight painting in Blender.

### Entering Weight Paint Mode
The Toggle Weight Paint Mode operator lets you switch into weight paint mode easier.
Simply select your mesh object and run the operator. The armature will be un-hidden and put into pose mode if necessary.
Run the operator again to reset the armature object's visibility states to what they were before you entered weight paint mode.

I recommend setting up a keybind for this, eg.:  
![toggle_wp_shortcut](/media/addons/easy_weights/toggle_wp_shortcut.png)
If you don't want to use the hotkey editor, you can also just find the operator in the "Object" or "Weights" menus, and simply Right Click->Assign Shortcut.

### Weight Paint Context Menu
The default context menu (accessed via W key or Right Click) for weight paint mode is not very useful.
The Custom Weight Paint Context Menu operator is intended as a replacement for it.  
![custom_wp_context_menu](/media/addons/easy_weights/custom_wp_context_menu.png)
_(The "OK" button is not needed, I just can't avoid it)_  

This panel provides quick access to commonly needed tools, whether they are part of core Blender or the addon:
- Global toggles for the Accumulate, Front Faces Only and Falloff Shape brush options.
- Weight Paint mode settings including a new "Clean Weights" option to run the Clean Weights operator after every brush stroke.
- Commonly used Overlay and Armature display settings.
- Commonly used or [new](#vertex-group-operators) operators.
It lets you change the brush falloff type (Sphere/Projected) and the Front Faces Only option. These will affect ALL brushes.  
Also, the color of your brushes will be darker when you're using Sphere falloff.  

I recommend to overwrite the shortcut of the default weight paint context menu like so:  
![wp_context_menu_shortcut](/media/addons/easy_weights/wp_context_menu_shortcut.png) 

### Hunting Rogue Weights
The addon provides a super sleek workflow for hunting down rogue weights efficiently but safely, with just the right amount of automation. This functionality can be found in the Sidebar->EasyWeight->Weight Islands panel.
![weight_islands](/media/addons/easy_weights/weight_islands.png) 

- After pressing Calculate Weight Islands and waiting a few seconds, you will see a list of all vertex groups which consist of more than a single island. 
- Clicking the magnifying glass icon will focus the smallest island in the group, so you can decide what to do with it.
- If the island is rogue weights, you can subtract them and go back to the previous step. If not, you can press the checkmark icon next to the magnifying glass, and the vertex group will be hidden from the list.
- Continue with this process until all entries are gone from the list.
- In the end, you can be 100% sure that you have no rogue weights anywhere on your mesh.

### Vertex Group Operators
The Vertex Groups context menu is re-organized with more icons and better labels, as well as some additional operators:
![vg_context_menu](/media/addons/easy_weights/vg_context_menu.png)
- **Delete Empty Deform Groups**: Delete deforming groups that don't have any weights.  
- **Delete Unused Non-Deform Groups**: Delete non-deforming groups that aren't used anywhere, even if they do have weights.  
- **Delete Unselected Deform Groups**: Delete all deforming groups that don't correspond to a selected pose bone. Only in Weight Paint mode.  
- **Ensure Mirror Groups**: If your object has a Mirror modifier, this will create any missing vertex groups.  
- **Focus Deforming Bones**: Reveal and select all bones deforming this mesh. Only in Weight Paint mode.  
If you have any more suggestions, feel free to open an Issue with a feature request.
- **Symmetrize Vertex Groups**: Symmetrizes vertex groups from left to right side, creating missing groups as needed.

### Force Apply Mirror Modifier
In Blender, you cannot apply a mirror modifier to meshes that have shape keys.  
This operator tries to anyways, by duplicating your mesh, flipping it on the X axis and merging into the original. It will also flip vertex groups, shape keys, shape key masks, and even (attempt) shape key drivers, assuming everything is named with .L/.R suffixes.  

## Previous Features
Over time as more things have been fixed on Blender's side, some features have been removed. To avoid confusion, these are listed here:
- As of [Blender 3.1](https://developer.blender.org/rBa215d7e230d3286abbed0108a46359ce57104bc1), holding the Ctrl and Shift buttons in weight painting will use the Subtract and Blur brushes respectively, removing the need for the shortcuts on the 1, 2, 3 keys this addon used to add to provide quick brush switching.
- As of [Blender 3.0](https://developer.blender.org/rBSc0f600cad1d2d107d189b15b12e2fcc6bba0985c), the weight paint overlay is no longer multiplied on top of the underlying colors, removing the need for this addon to change shading or object display settings when using the Toggle Weight Paint mode operator.