# SPDX-License-Identifier: GPL-2.0-or-later
# (c) 2021, Blender Foundation - Paul Golter
# (c) 2022, Blender Foundation - Demeter Dzadik

from typing import Optional, Any, Set, Tuple, List

import bpy
from bpy.props import IntProperty, CollectionProperty, BoolProperty
from bpy.types import AddonPreferences

from .ui import ui_prefs
from .util import get_addon_prefs
from .repository import SVN_repository
import json
from pathlib import Path

class SVN_addon_preferences(AddonPreferences):
    bl_idname = __package__

    repositories: CollectionProperty(type=SVN_repository)
    active_repo_idx: IntProperty(
        name="SVN Repositories",
        options=set()
    )

    def get_current_repo(self, context) -> Optional[SVN_repository]:
        scene_svn = context.scene.svn
        if not scene_svn.svn_url or not scene_svn.svn_directory:
            return

        for repo in self.repositories:
            if (repo.url == scene_svn.svn_url) and (repo.directory == scene_svn.svn_directory):
                return repo

    debug_mode: BoolProperty(
        name = "Debug Mode",
        description = "Enable some debug UI",
        default = False
    )
    is_busy: BoolProperty(
        name="Is Busy",
        description="Indicates whether there is an ongoing SVN Update or Commit. For internal use only, to prevent both processes from trying to run at the same time, which is not allowed by SVN",
        default=False
    )
    loading: BoolProperty(
        name="Loading",
        description="Disable the credential update callbacks while loading repo data to avoid infinite loops",
        default=False
    )

    def save_repo_info_to_file(self):
        saved_props = {'url', 'directory', 'name', 'username', 'password', 'display_name'}
        repo_data = {}
        for repo in self['repositories']:
            directory = repo.get('directory', '')
            
            repo_data[directory] = {key:value for key, value in repo.to_dict().items() if key in saved_props}
        
        filepath = Path(bpy.utils.user_resource('CONFIG')) / Path("blender_svn.txt")
        with open(filepath, "w") as f:
            json.dump(repo_data, f, indent=4)

    def load_repo_info_from_file(self):
        self.loading = True
        try:
            filepath = Path(bpy.utils.user_resource('CONFIG')) / Path("blender_svn.txt")
            if not filepath.exists():
                return

            with open(filepath, "r") as f:
                repo_data = json.load(f)

            for directory, repo_data in repo_data.items():
                repo = self.repositories.get(directory)
                if not repo:
                    repo = self.repositories.add()
                    repo.directory = directory
                    for key, value in repo_data.items():
                        setattr(repo, key, value)
        finally:
            self.loading = False

    draw = ui_prefs.draw_prefs

registry = [
    SVN_addon_preferences
]
