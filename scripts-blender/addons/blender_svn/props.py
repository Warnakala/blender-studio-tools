# SPDX-License-Identifier: GPL-2.0-or-later
# (c) 2021, Blender Foundation - Paul Golter
# (c) 2022, Blender Foundation - Demeter Dzadik

from . import wheels
# This will load the dateutil and BAT wheel files.
wheels.preload_dependencies()

import bpy
from typing import Optional, Dict, Any, List, Tuple, Set
from bpy.props import StringProperty

class SVN_scene_properties(bpy.types.PropertyGroup):
    """Subversion properties and functions"""
    svn_url: StringProperty(
        name="Remote URL",
        default="",
        description="URL of the remote SVN repository of the current file, if any. Used to match to the SVN data stored in the user preferences",
    )
    svn_directory: StringProperty(
        name="Root Directory",
        default="",
        subtype="DIR_PATH",
        description="Absolute directory path of the SVN repository's root in the file system",
    )

    ### Basic SVN Info #########################################################

    def get_repo(self, context):
        prefs = context.preferences.addons[__package__].preferences
        return prefs.get_current_repo(context)

    ### SVN File List UIList filter properties #################################
    # These are normally stored on the UIList, but then they cannot be accessed
    # from anywhere else, since template_list() does not return the UIList instance.
    # We need to be able to access them outside of drawing code, to be able to
    # know which entries are visible and ensure that a filtered out entry can never
    # be the active one.

    def get_visible_indicies(self, context) -> List[int]:
        flt_flags, _flt_neworder = bpy.types.SVN_UL_file_list.cls_filter_items(
            context, self.get_repo(context), 'external_files')

        visible_indicies = [i for i, flag in enumerate(flt_flags) if flag != 0]
        return visible_indicies

    def force_good_active_index(self, context) -> bool:
        """
        We want to avoid having the active file entry be invisible due to filtering.
        If the active element is being filtered out, set the active element to 
        something that is visible.
        """
        visible_indicies = self.get_visible_indicies(context)
        repo = self.get_repo(context)
        if len(visible_indicies) == 0:
            repo.external_files_active_index = 0
        elif repo.external_files_active_index not in visible_indicies:
            repo.external_files_active_index = visible_indicies[0]

    def update_file_filter(dummy, context):
        """Should run when any of the SVN file list search filters are changed."""
        context.scene.svn.force_good_active_index(context)

    file_search_filter: StringProperty(
        name="Search Filter",
        description="Only show entries that contain this string",
        update=update_file_filter
    )


registry = [
    SVN_scene_properties,
]


def register() -> None:
    # Scene Properties.
    bpy.types.Scene.svn = bpy.props.PointerProperty(type=SVN_scene_properties)


def unregister() -> None:
    del bpy.types.Scene.svn
