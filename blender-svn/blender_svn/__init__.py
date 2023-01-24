# SPDX-License-Identifier: GPL-2.0-or-later
# (c) 2021, Blender Foundation - Paul Golter
# (c) 2022, Blender Foundation - Demeter Dzadik

# TODO:
# - Updating of local file statuses should be de-coupled from updating of online file statuses, so it can be significantly more responsive.

import bpy
import importlib

from . import prefs, props, ops, ui, svn_log, svn_status, svn_update, svn_commit, filebrowser

bl_info = {
    "name": "Blender SVN",
    "author": "Demeter Dzadik, Paul Golter",
    "description": "Blender Add-on to interact with Subversion.",
    "blender": (3, 1, 0),
    "version": (0, 1, 0),
    "location": "View3D",
    "warning": "",
    "doc_url": "",
    "tracker_url": "",
    "category": "Generic",
}

modules = [
    prefs,
    ops,
    ui,
    svn_log,
    svn_status,
    props,
    svn_update,
    svn_commit,
    filebrowser
]


def reload() -> None:
    global modules

    for m in modules:
        importlib.reload(m)


_need_reload = "prefs" in locals()
if _need_reload:
    reload()

# ----------------REGISTER--------------.


def register() -> None:
    if bpy.app.background:
        return
    for m in modules:
        if hasattr(m, 'registry'):
            for c in m.registry:
                bpy.utils.register_class(c)
        if hasattr(m, 'register'):
            m.register()


def unregister() -> None:
    if bpy.app.background:
        return
    for m in modules:
        if hasattr(m, 'registry'):
            for c in m.registry:
                bpy.utils.unregister_class(c)
        if hasattr(m, 'unregister'):
            m.unregister()
