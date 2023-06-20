# Workstation System Maintenance

## How to Update Build Server & Clients
The script will pull all of the latest changes from the main gentoo repository and initiate a system update. When done, it will ask if you want to push out the changes to the clients. The clients checks for updates every five minutes. If the server signals that there are updates, they will perform a sync with the build server and download and install all updated packages.

1. `ssh user@build-server-addr` connect to your build server via ssh
2. Use `su` to Login as root or login as root directly
3. Use `cd` to enter root home folder
4. Run `update_build_server.sh`


## Update addons on `/shared/software/addons`

 The software inside the `shared/software/addons` directory are Live Packages. Live Packages are packages that tracks the source-code repository directly and is not tied to a specific release. 

::: warning Temporary Solution
This is a temporary solution that will be depreciated and replace with project based addons.
::: 

1. `ssh user@build-server-addr` connect to your build server via ssh
2. Use `su` to Login as root or login as root directly
3. Run `emerge -1 {package-name}` to update a live package.
    - Run `emerge -1 flamenco` to update the flamenco client/addon
    - Run `emerge -1 blender-studio-tools` to update the studio addons
4. Run `date -R > /var/cache/update_info/timestamp.chk` to mark this update as the latest

## Wake on LAN
Wake on LAN use the hardware information provided by the clients to wake up all that are currently offline. If this is used in combination with a system update, the client computers will turn off after the system update has completed. (Unless any users are logged into the system when the update finishes).

1. `ssh user@build-server-addr` connect to your build server via ssh
2. Use `su` to Login as root or login as root directly
3. `cd` to change directory to the root home folder
4. `mkdir comps` To create a folder to store parsed client hardware info if none exists
5. `parse_output.py /var/studio_scripts/hw_data/* comps/` to parse client hardware info 
6. Run  `./wol_shared_comps.py comps/*` to wake any computers that are asleep
