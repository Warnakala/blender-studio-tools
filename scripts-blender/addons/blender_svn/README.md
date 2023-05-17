# Blender SVN
blender-svn is a Blender add-on to interact with Subversion from within Blender.

[Blender-SVN Demo Video](https://studio.blender.org/films/charge/gallery/?asset=5999)

## Table of Contents
- [Installation](#installation)
- [Features](#features)
## Installation
1. Clone repository `git clone https://projects.blender.org/studio/blender-studio-pipeline.git`
2. From the root of the repository navigate to `/scripts-blender/addons/` 
3. Find the the `blender_svn` folder. Place this folder in your Blender addons directory or create a sym link to it.

## Features
- UI appears when the currently opened .blend file is in an SVN repository.
- You can enter your SVN username and password to this repository, which will be stored until you disable the add-on.
- Display a list of all files in the repository that are outdated, modified, newly added, replaced, conflicted, etc, with the relevant available operations next to them.
- Saves the SVN log into a text file in the background, and displays it in the UI. This was important to us because normally, accessing the svn log has been very slow for us.
Download updates, commit changes, resolve conflicts, all from within Blender.
- If you're working in an outdated file, Blender will show you a very ugly and very aggressive warning.
