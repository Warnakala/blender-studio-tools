# Infrastructure

::: warning Work in Progress
30 Apr. 2023 - The content of this page is currently being edited/updated.
:::


## Workstations
Artists at Blender Studio use Linux workstations, running Gentoo Linux. While the infrastructure is meant to support other Operating Systems, it's primarily designed to work in an eterogeneous enviroment, where every machine is setup in a similar way.

Artist workstations double as clients for the render farm.

* **Link to reference manual**
* **Link to setup guide**

## Shared storage
We use two shared drives

* `/render` to store render farm output
* `/shared` to store project and shared data

**Link to setup guide**

## Version Control System
We use SVN. While providing a higher barrier of entry, it provides a robust and efficient way to store and version large binary files during the course of a production.

This means we need an SVN service (can be in the LAN, or online)

## Network/Web Services

* Syncthing (needs access to /shared)
* Flamenco (**render farm** needs access to /shared and /render)
* Kitsu (**production tracker** can be hosted anywhere)
* Watchtower (needs access to Kitsu)

## Other Dependencies

We rely on the [Blender Buildbot](https://builder.blender.org) infrastructure to provide Blender builds to the workstations.
