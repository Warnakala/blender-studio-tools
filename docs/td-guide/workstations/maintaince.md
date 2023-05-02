# Workstation System Maintenance

## How to Update Workstation Server
1. Use `su` to Login as root or login as root directly
2. Use `cd` to enter root home folder
3. Run `update_build_server.sh`

## Push Updates to Client Workstations

To perform system updates, switch to the **root** user ****on the build server and run the “update_build_server.sh” script in the home folder of the root user.

Note that this script is packaged, so no changes should be made to it locally as those will be overwritten when updating.

The script will pull all of the latest changes from the main gentoo repository and initiate a system update. When done, it will ask if you want to push out the changes to the clients.The clients checks for updates every five minutes. If the server signals that there are updates, they will perform a sync with the build server and download and install all updated packages.


## Update addons on `/shared/software/addons`

1. Use `su` to Login as root or login as root directly
2. Run `emerge -1 flamenco` to update the flamenco addon
3. Run `emerge -1 blender-studio-tools` to update the studio addons

## Wake on LAN

To wake up client computers if they are offline, run the `wol_shared_comps.py` in the root home folder of the Build server.

It will use the hardware information provided by the clients to wake up all that are currently offline.

If this is used in combination with a system update, the client computers will turn off after the system update has completed. (Unless any users are logged into the system when the update finishes).