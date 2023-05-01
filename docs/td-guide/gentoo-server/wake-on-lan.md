# Wake on LAN

To wake up client computers if they are offline, run the `wol_shared_comps.py` in the root home folder of the Build server.

It will use the hardware information provided by the clients to wake up all that are currently offline.

If this is used in combination with a system update, the client computers will turn off after the system update has completed. (Unless any users are logged into the system when the update finishes).