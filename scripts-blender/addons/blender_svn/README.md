# Blender SVN
blender-svn is a Blender add-on to interact with the Subversion version control system from within Blender.

[Blender-SVN Demo Video](https://studio.blender.org/films/charge/gallery/?asset=5999)

## Installation
1. Download [latest release](../addons/overview) 
2. Launch Blender, navigate to `Edit > Preferences` select `Addons` and then `Install`, 
3. Navigate to the downloaded add-on and select `Install Add-on` 
4. Make sure you have an SVN client installed, such that typing `svn` in the command line gives a result.

## Features
- Open a .blend file that is in an SVN repository, and enter credentials.
- Download updates, commit changes, resolve conflicts, all from within Blender.
- You can also add repositories in the add-on preferences UI.

- A list shows all files in the repository that are outdated, modified, newly added, replaced, conflicted, etc, with the relevant available operations next to them.
- The file statuses automatically update every few seconds. If you do an SVN operation, the file statuses update immediately.
- Searching for a file name will also show files that aren't modified.
- You can right click on a file to open it. If it's a .blend file, it will open in the current Blender instance, without loading the UI.

- Entered credentials get saved to disk, so they get preserved even if the add-on gets disabled.
- SVN Log is saved to disk, so a full log is always available and searchable, and you can easily revert a file or the whole repo to an older version.
- If you're working in an outdated file, Blender will show a constant, very aggressive warning, since this could result in wasted work.

## Notes
- SVN Checkout is not supported due to limitations with giving progress feedback in the UI for such a long process. Do your checkouts via the command line.
- The speed at which your SVN server can answer requests will greatly affect your experience using the add-on, or any other SVN interface.
