# Working with Blender

## Launch Blender from Taskbar/Start Menu
1. Search for Blender in your Application Launcher
2. The application with the exact name `blender` without any suffix is the latest build.
![Image of Blender Icon in KDE Taskbar/Start Menu](/media/user-guide/launch_blender.mp4)

## Launch Blender from Terminal
1. Open a new Terminal window
2. Type command `blender`
## Roll Back Blender Build
1. Login as ********root******** user using `su`
2. Run `rollback_blender.sh` from any folder
    
    ```powershell
    Available builds:
    
    ID:   1 (2023-03-30 06:10)
    ID:   2 (2023-03-30 17:13)
    ID:   3 (2023-03-30 17:40)
    ID:   4 (2023-04-02 22:07)
    ID:   5 (2023-04-03 20:12)
    ID:   6 (2023-04-11 20:12)
    ID:   7 (2023-04-20 20:12) <installed>
    
    Select which Blender build number to switch to. 
    (press ENTER to confirm): 
    ```
3. Select a build by enter a number and pressing Enter to confirm

## Build Blender Locallly

1. Download Git repo
    
    ```bash
    mkdir ~/blender-git
    cd ~/blender-git
    git clone https://projects.blender.org/blender/blender.git
    ```
    
2. Build Blender
    
    ```bash
    cd ~/blender-git/blender
    make update
    make
    ```
    
3. Find your built blender `cd ../build_linux`