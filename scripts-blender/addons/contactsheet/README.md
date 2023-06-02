# Contact Sheet
Blender Add-on to create a contactsheet from sequence editor strips.

[Contact Sheet Blogpost](https://studio.blender.org/blog/contact-sheet-addon/)
## Table of Contents

- [Installation](#installation)
- [Features](#features)
## Installation
1. Download [latest release](../addons/overview) 
2. Launch Blender, navigate to `Edit > Preferences` select `Addons` and then `Install`, 
3. Navigate to the downloaded add-on and select `Install Add-on` 

## Features
After the addon is enabled you will find a `Contactsheet` tab in the Sequence Editor Toolbar.
The 'Make Contactsheet' operator creates a temporary scene and arranges the previously selected sequences in a grid.
If no sequences were selected it takes a continuous row of the top most sequences.
The operator name always shows you how many sequences will be used.
You can overwrite the resolution of the contactsheet by adjusting the X and Y sliders.
The number of rows and columns is automatically calculated. It can also be overwritten by toggling the lock button.
Check the addon preferences there you find some options to customize the contactsheet even more.


Create a sym link in your Blender addons directory to the contactsheet/contactsheet folder.
