# SPDX-License-Identifier: GPL-2.0-or-later
# (c) 2021, Blender Foundation - Paul Golter
# (c) 2022, Blender Foundation - Demeter Dzadik

from typing import Optional, Any, Set, Tuple, List

import bpy
from bpy.props import IntProperty, CollectionProperty, BoolProperty
from bpy.types import PropertyGroup, AddonPreferences

from .util import get_addon_prefs
from .repository import SVN_repository

class SVN_addon_preferences(AddonPreferences):
    bl_idname = __package__

    svn_repositories: CollectionProperty(type=SVN_repository)
    svn_repo_active_idx: IntProperty(
        name="SVN Repositories",
        options=set()
    )

    def get_current_repo(self, context) -> Optional[SVN_repository]:
        scene_svn = context.scene.svn
        if not scene_svn.svn_url or not scene_svn.svn_directory:
            return

        for repo in self.svn_repositories:
            if repo.url == scene_svn.svn_url and repo.directory == scene_svn.svn_directory:
                return repo

    is_busy: BoolProperty(
        name="Is Busy",
        description="Indicates whether there is an ongoing SVN Update or Commit. For internal use only, to prevent both processes from trying to run at the same time, which is not allowed by SVN",
        default=False
    )

    def draw(self, context) -> None:
        layout = self.layout

        layout.label(text="SVN Repositories:")
        col = layout.column()
        col.enabled = False
        col.template_list(
            "SVN_UL_repositories",
            "svn_repo_list",
            self,
            "svn_repositories",
            self,
            "svn_repo_active_idx",
        )


@bpy.app.handlers.persistent
def try_authenticating_on_file_load(_dummy1, _dummy2):
    context = bpy.context
    prefs = get_addon_prefs(context)
    repo = prefs.get_current_repo(context)
    if repo and repo.is_cred_entered:
        print("SVN: Credentials found. Try authenticating on file load...")
        # Don't assume that a previously saved password is still correct.
        repo.authenticated = False
        # Trigger the update callback.
        repo.password = repo.password


# ----------------REGISTER--------------.

registry = [
    SVN_addon_preferences
]


def register():
    bpy.app.handlers.load_post.append(try_authenticating_on_file_load)


def unregister():
    bpy.app.handlers.load_post.remove(try_authenticating_on_file_load)
