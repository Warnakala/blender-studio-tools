# Anim Cupboard

Miscellaneous operators and tools requested by Blender Studio Animators.

## Table of Contents
- [Installation](#installation)
- [Features](#features)
    - [Select Similar Curves](#select-similar-curves)
    - [Lock Curves](#lock-curves)
    - [Easy Constraints](#easy-constraints)

## Installation
1. Download [latest release](../addons/overview) 
2. Launch Blender, navigate to `Edit > Preferences` select `Addons` and then `Install`, 
3. Navigate to the downloaded add-on and select `Install Add-on` 

## Features
### Select Similar Curves

Location: Graph Editor -> Select -> Select Similar Curves  
This will set the selection state of all selected bones' curves based on whether they match the transform channel of the active curve. For example, if the active curve is a Y Rotation curve, all Y Rotation curves will be selected, and all others de-selected.

### Lock Curves

Location: Graph Editor -> Channels -> Lock  
This operator lets you set the lock state of selected, un-selected or all curves.

### Easy Constraints

Location: 3D Viewport -> Sidebar -> Animation -> Easy Constraints  
This UI panel lets animators easily create and manage Copy Transforms constraint set-ups with a VERY minimalistic UI.  
In future, other constraint types can be added as well.  
