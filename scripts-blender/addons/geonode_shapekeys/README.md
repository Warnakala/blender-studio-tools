# GeoNode Shape Keys
GeoNode Shape Keys is a Blender Add-on that lets you deform linked and overridden meshes using sculpt mode in a roundabout way using a geometry node set-up. While the current override system doesn't support adding or editing shape keys on overridden meshes, it does allow you to add modifiers, so this add-on leverages that.
## Table of Contents

- [Installation](#installation)
- [How to Use](#how-to-use)

## Installation
1. Download [latest release](../addons/overview) 
2. Launch Blender, navigate to `Edit > Preferences` select `Addons` and then `Install`, 
3. Navigate to the downloaded add-on and select `Install Add-on` 

# How to use
The add-on's UI is only visible on linked and overridden meshes.  
It can be found under Properties->Object Data->Shape Keys->GeoNode Shape Keys.  
The add button will do the following:  
- Create a local version of the evaluated object that you can sculpt on  
- Create a modifier on the linked object, that will apply your sculpted changes to it  

After creating a set-up, you get a button to conveniently swap between the two objects.

Removing a list entry should also remove the relevant modifier and object. Otherwise, it will throw a warning.  

The node set-up that applies the deformation relies on a UV map.