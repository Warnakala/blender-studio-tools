# Overview: Workstation Server & Client 

![Gentoo Overview](/media/td-guide/server/gentoo_server_overview.png)

Note that the clients do not strictly depend on the Build Server.The build server can be unavailable and all clients will still be able to install packages and work as normal. They will simply not receive any automatic updates or download any precompiled packages if the build server is down.

After the install process is done, the IPXE file host is only needed for reinstalls or if any of them wants to access it for running MemTest or any other utilities hosted there.
