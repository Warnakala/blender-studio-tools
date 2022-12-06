# GeoNode Shape Keys
GeoNode Shape Keys is a Blender Add-on that lets you deform linked and overridden meshes using sculpt mode in a roundabout way using a geometry node set-up. While the current override system doesn't support adding or editing shape keys on overridden meshes, it does allow you to add modifiers, so this add-on leverages that.

## Installation
Download or clone this repository.
In the root project folder you will find the 'geonode_shapekeys' (the one with the underscore, not the dash) folder. Place this folder in your Blender addons directory or create a symlink to it.

# How to use
The add-on's UI is only visible on linked and overridden meshes.  
It can be found under Properties->Object Data->Shape Keys->GeoNode Shape Keys.  
The add button will do the following:  
- Create a local version of the evaluated object that you can sculpt on  
- Create a modifier on the linked object, that will apply your sculpted changes to it  

After creating a set-up, you get a button to conveniently swap between the two objects.

Removing a list entry should also remove the relevant modifier and object. Otherwise, it will throw a warning.  

The node set-up that applies the deformation relies on a UV map.