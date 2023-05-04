---
outline: deep
---

# Manage Software

There are two ways to install and uninstall software.

## Emerge

emerge is the default package manager, use emerge to install, update, and generally maintain software packages on Gentoo. emerge should always be your first option when searching for software. To learn more: https://wiki.gentoo.org/wiki/Emerge

### Open Terminal and Become Root

![Open Terminal from Taskbar](/media/user-guide/workstations/gentoo_workstation_open_terminal.mp4)

1.  From the Task Bar select the “KDE Logo” to open the Start Menu, and type “Terminal” in the search bar
2.  Become root via `su`


### Search & Install software via emerge

**emerge** provides commands to install packages onto your system including any dependencies. You must be **root** to make changes via **emerge**. _In this example package name is **spotify**._

1.  [Open Terminal and Become Root](/user-guide/workstations/installing-software.md#open-terminal-and-become-root)
2.  Find avaliable packages using the `eix` for example: `eix spotify`

```bash
* gnome-extra/gnome-integration-spotify
     Available versions:  20140907-r2 {PYTHON_TARGETS="python3_9 python3_10"}
     Homepage:            https://github.com/mrpdaemon/gnome-integration-spotify
     Description:         GNOME integration for Spotify

* media-sound/spotify
     Available versions:  1.2.8^ms {libnotify local-playback pax-kernel pulseaudio}
     Homepage:            https://www.spotify.com/download/linux/
     Description:         Spotify is a social music platform

* media-sound/spotify-tray
     Available versions:  ~1.3.2-r1
     Homepage:            https://github.com/tsmetana/spotify-tray
     Description:         Wrapper around the Spotify client that adds a tray icon

Found 3 matches
```

3.  Install a package via emerge: `emerge spotify`
4.  (Optionally) install a specific package version via `emerge ={package-name}-{version}` _Example:_ `emerge =spotify-1.2.8`

```bash
Calculating dependencies... done!
Dependency resolution took 8.40 s.

>>> Installing (1 of 2) dev-util/patchelf-0.17.0::gentoo
>>> Installing (2 of 2) media-sound/spotify-1.2.8::gentoo
>>> Recording media-sound/spotify in "world" favorites file...
* Messages for package media-sound/spotify-1.2.8:
* Install additional packages for optional runtime features:
*   media-sound/spotify-tray for systray integration on non-Gnome DEs

* GNU info directory index is up-to-date.
```


### Remove software via emerge

**emerge** provides commands to remove packages from your system, as well as to safely clean up any dependencies. **emerge** should not remove important packages that are needed for the system to function, without warning.

In this example package name is **spotify**.

1.  [Open Terminal and Become Root](/user-guide/workstations/installing-software.md#open-terminal-and-become-root)
2.  Remove a package and it’s dependacies safely.
    1.  `emerge --deselect spotify`
    2.  `emerge --depclean`

::: warning Warning

Do **not** use the `--unmerge`(`-C`) option. This option can remove important packages that are needed for the system to function, without warning. [`source`](https://wiki.gentoo.org/wiki/Emerge#:~:text=see%20warning%20below)
:::



## Discover Store

**Discover Store** is the alternative package manager. Only search for applications here if they are not found in **emerge**. **Discover Store** is a flatpack based package manager. This means applications are large and slow to install. *To learn more: [https://apps.kde.org/discover/](https://apps.kde.org/discover/)*

### Search & Install software via Discover Store

_Discover Store provides a GUI to install packages onto your system including any dependancies._

![How to Install via Discover Store](/media/user-guide/workstations/discover_store_install.mp4)

1. Open the Discover store via taskbar
2. Search for the name of the application in the top right corner
3. Select the Application and the `Install` button to install
4. Progress will appear in the button left of the window unders tasks

### Remove software via Discover Store

_Discover Store provides a GUI to view/remove the installed packages onto your system. Dependancies should be automatically be removed with removing software. You can optionally remove user settings/data._

![How to remove via Discover Store](/media/user-guide/workstations/discover_store_remove.mp4)

   1. Find the **Installed** Tab of the store window
   2. This will open a list of installed applications and it's dependancies
   3. Select an Application from the list, clicking the remove button will remove it
   4. Progress will appear in the button left of the window unders tasks
   5. Refreshing installed page shows the application and it’s dependacies have been automatically be removed
   6. The application will appear as avaliable to install once removal is complete
