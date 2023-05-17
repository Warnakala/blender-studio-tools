# GeoNode Shape Keys
GeoNode Shape Keys is a Blender Add-on that lets you deform linked and overridden meshes using sculpt mode in a roundabout way using a geometry node set-up. While the current override system doesn't support adding or editing shape keys on overridden meshes, it does allow you to add modifiers, so this add-on leverages that.
## Table of Contents

- [Installation](#installation)
- [How to Use](#how-to-use)

## Installation
1. Clone repository `git clone https://projects.blender.org/studio/blender-studio-pipeline.git`
2. From the root of the repository navigate to `/scripts-blender/addons/` 
3. Find the the `geonode_shapekeys`a Place this folder in your Blender addons directory or create a symlink to it.

# How to use
The add-on's UI is only visible on linked and overridden meshes.  
It can be found under Properties->Object Data->Shape Keys->GeoNode Shape Keys.  
The add button will do the following:  
- Create a local version of the evaluated object that you can sculpt on  
- Create a modifier on the linked object, that will apply your sculpted changes to it  

After creating a set-up, you get a button to conveniently swap between the two objects.

Removing a list entry should also remove the relevant modifier and object. Otherwise, it will throw a warning.  

The node set-up that applies the deformation relies on a UV map.