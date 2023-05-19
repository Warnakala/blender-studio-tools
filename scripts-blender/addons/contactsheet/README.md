# Contact Sheet
Blender Add-on to create a contactsheet from sequence editor strips.

[Contact Sheet Blogpost](https://studio.blender.org/blog/contact-sheet-addon/)
## Table of Contents

- [Installation](#installation)
- [Features](#features)
## Installation
1. Clone repository `git clone https://projects.blender.org/studio/blender-studio-pipeline.git`
2. From the root of the repository navigate to `/scripts-blender/addons/` 
3. Find the the `contactsheet` folder. Copy this folder into your Blender addons directory or create a symlink to it.

## Features
After the addon is enabled you will find a `Contactsheet` tab in the Sequence Editor Toolbar.
The 'Make Contactsheet' operator creates a temporary scene and arranges the previously selected sequences in a grid.
If no sequences were selected it takes a continuous row of the top most sequences.
The operator name always shows you how many sequences will be used.
You can overwrite the resolution of the contactsheet by adjusting the X and Y sliders.
The number of rows and columns is automatically calculated. It can also be overwritten by toggling the lock button.
Check the addon preferences there you find some options to customize the contactsheet even more.


Create a sym link in your Blender addons directory to the contactsheet/contactsheet folder.
