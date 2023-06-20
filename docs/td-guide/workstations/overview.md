# Overview of Operating System 

[Gentoo](https://www.gentoo.org/) is a source based distro, which means you download the source code for every package and compile it yourself. The advantage of Gentoo is that we can much more easily interact with the source code and upstream projects. To learn about how to work with Gentoo see the [Gentoo Handbook](https://wiki.gentoo.org/wiki/Handbook:AMD64)

The Gentoo package manager allows a single computer to compile and serve pre-built packages to a network of computers, this can be useful in a studio environment. This server is called the "Gentoo Build Server" which provides software to the client systems.

Here is an overview of how we deploy Gentoo at the Blender Studio:

![Gentoo Overview](/media/td-guide/server/gentoo_server_overview.png)
|Name|Description|
|---|---|
|**IPXE File Host**| This is simple a http server that hosts boot images. [IPXE](https://ipxe.org/) is a network based boot loader that can boot over the network|
|**Gentoo Build Server**|Server that serves pre-built packages to a network of computers. It also keeps track of client hardware info and client update error logs|
|**Client System**|Workstations for users within the studio that receive software & updates from Build Server|


Note that the clients do not strictly depend on the Build Server. The build server can be unavailable and all clients will still be able to install packages and work as normal. They will simply not receive any automatic updates or download any precompiled packages if the build server is down.

After the install process is done, the IPXE file host is only needed for reinstalls or if any of them wants to access it for running MemTest or any other utilities hosted there.
