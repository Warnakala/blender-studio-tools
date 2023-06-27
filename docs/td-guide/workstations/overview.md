# Introduction

The workstation section will cover the setup/maintenance of workstations in the Blende Studio Pipeline. This section is intended for IT Professionals, Technical Directors or any technically inclined members of a studio's team. The following is a brief overview of the workstation eco-system.
# Overview

Blender Studio workstations use the [Gentoo](https://www.gentoo.org/) Operating system. It is a source based distribution, which means you download the source code for every package and compile it yourself. The advantage of Gentoo is that we can much more easily interact with source code and upstream projects. To learn about how to work with Gentoo see the [Gentoo Handbook](https://wiki.gentoo.org/wiki/Handbook:AMD64)

The Gentoo package manager allows a single computer to compile and serve pre-built packages to a network of computers, this can be useful in a studio environment. This server is called the "Build Server" which provides software to the client systems.

Here is an overview of how we deploy Gentoo at the Blender Studio:

![Gentoo Overview](/media/td-guide/server/gentoo_server_overview.png)
|Name|Description|
|---|---|
|**IPXE File Host**| This is simple a http server that hosts boot images. [IPXE](https://ipxe.org/) is a network based boot loader that can boot over the network|
|**Gentoo Build Server**|Server that serves pre-built packages to a network of computers. It also keeps track of client hardware info and client update error logs|
|**Client System**|Workstations for users within the studio that receive software & updates from Build Server|


::: info Note
Clients do not strictly depend on the Build Server. The build server can be unavailable and all clients will still be able to install packages and work as normal. They will simply not receive any automatic updates or download any precompiled packages if the build server is down.

After the install process is done, the IPXE file host is only needed for reinstalls or if any of them wants to access it for running MemTest or any other utilities hosted there.
:::