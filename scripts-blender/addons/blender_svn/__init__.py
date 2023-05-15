# SPDX-License-Identifier: GPL-2.0-or-later
# (c) 2021, Blender Foundation - Paul Golter
# (c) 2022, Blender Foundation - Demeter Dzadik

bl_info = {
    "name": "Blender SVN",
    "author": "Demeter Dzadik, Paul Golter",
    "description": "Blender Add-on to interact with Subversion.",
    "blender": (3, 1, 0),
    "version": (0, 2, 0),
    "location": "View3D",
    "warning": "",
    "doc_url": "",
    "tracker_url": "",
    "category": "Generic",
}

from bpy.utils import register_class, unregister_class
import importlib

from . import (
    props,
    repository,
    commands,
    ui,
    prefs,
)

modules = [
    props,
    repository,
    commands,
    ui,
    prefs,
]

def register_unregister_modules(modules: list, register: bool):
    """Recursively register or unregister modules by looking for either
    un/register() functions or lists named `registry` which should be a list of 
    registerable classes.
    """
    register_func = register_class if register else unregister_class

    for m in modules:
        if register:
            importlib.reload(m)
        if hasattr(m, 'registry'):
            for c in m.registry:
                try:
                    register_func(c)
                except Exception as e:
                    un = 'un' if not register else ''
                    print(f"Warning: SVN failed to {un}register class: {c.__name__}")
                    print(e)

        if hasattr(m, 'modules'):
            register_unregister_modules(m.modules, register)

        if register and hasattr(m, 'register'):
            m.register()
        elif hasattr(m, 'unregister'):
            m.unregister()

def register():
    register_unregister_modules(modules, True)

def unregister():
    register_unregister_modules(modules, False)
