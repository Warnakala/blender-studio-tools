# Push Updates to Client Workstations

To perform system updates, switch to the **root** user ****on the build server and run the “update_build_server.sh” script in the home folder of the root user.

Note that this script is packaged, so no changes should be made to it locally as those will be overwritten when updating.

The script will pull all of the latest changes from the main gentoo repository and initiate a system update. When done, it will ask if you want to push out the changes to the clients.The clients checks for updates every five minutes. If the server signals that there are updates, they will perform a sync with the build server and download and install all updated packages.