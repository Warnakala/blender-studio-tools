# SPDX-License-Identifier: GPL-2.0-or-later
# (c) 2021, Blender Foundation - Paul Golter
# (c) 2022, Blender Foundation - Demeter Dzadik

from typing import Optional, Any, Set, Tuple, List

import bpy
from bpy.props import IntProperty, CollectionProperty, BoolProperty, EnumProperty
from bpy.types import AddonPreferences

from .ui import ui_prefs
from .repository import SVN_repository
from .svn_info import get_svn_info
import json
from pathlib import Path
from .threaded.background_process import Processes

class SVN_addon_preferences(AddonPreferences):
    bl_idname = __package__

    repositories: CollectionProperty(type=SVN_repository)

    def init_repo(self, context, repo_path: Path or str):
        """Attempt to initialize a repository based on a directory.
        This means executing `svn info` in the repo_path to get the URL and root dir.
        If we already have an SVN_repository instance with that root dir, just return it.
        Otherwise, initialize it by storing its directory, URL, and a display name, and then return it.
        """
        root_dir, base_url = get_svn_info(repo_path)
        if not root_dir:
            return
        existing_repo = self.repositories.get(root_dir)
        if existing_repo:
            if existing_repo.external_files_active_index > len(existing_repo.external_files):
                existing_repo.external_files_active_index = 0
            existing_repo.log_active_index = len(existing_repo.log)-1
            existing_repo.reload_svn_log(context)
            return existing_repo

        repo = self.repositories.add()
        repo.initialize(root_dir, base_url)

        return repo

    def update_active_repo_idx(self, context):
        if self.idx_updating or len(self.repositories) == 0:
            return
        self.idx_updating = True
        active_repo = self.active_repo
        if self.ui_mode == 'CURRENT_BLEND':
            scene_svn = context.scene.svn
            scene_svn_idx = self.repositories.find(scene_svn.svn_directory)
            if scene_svn_idx == -1:
                self.idx_updating = False
                return
            self.active_repo_idx = scene_svn_idx
            self.idx_updating = False
            return
            
        if not active_repo.authenticated and not active_repo.auth_failed and active_repo.is_cred_entered:
            active_repo.authenticate(context)

        self.idx_updating = False

    def update_ui_mode(self, context):
        if self.ui_mode == 'CURRENT_BLEND':
            scene_svn = context.scene.svn
            scene_svn_idx = self.repositories.find(scene_svn.svn_directory)
            self.active_repo_idx = scene_svn_idx

    ui_mode: EnumProperty(
        name = "Choose Repository",
        description = "Whether the add-on should communicate with the repository of the currently opened .blend file, or the repository selected in the list below",
        items = [
            ('CURRENT_BLEND', "Current Blend", "Check if the current .blend file is in an SVN repository, and communicate with that if that is the case. The file list will display only the files of the repository of the current .blend file. If the current .blend is not in a repository, do nothing"),
            ('SELECTED_REPO', "Selected Repo", "Communicate with the selected repository")
        ],
        default = 'CURRENT_BLEND',
        update = update_ui_mode
    )

    active_repo_idx: IntProperty(
        name="SVN Repositories",
        options=set(),
        update=update_active_repo_idx
    )
    idx_updating: BoolProperty(
        name="Index is Updating",
        description="Helper flag to avoid infinite looping update callbacks",
    )

    @property
    def active_repo(self) -> SVN_repository:
        if len(self.repositories) > 0:
            return self.repositories[self.active_repo_idx]

    debug_mode: BoolProperty(
        name = "Debug Mode",
        description = "Enable some debug UI",
        default = False
    )
    
    @property
    def is_busy(self):
        return Processes.is_running('Commit', 'Update')

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

    def sync_repo_info_file(self):
        self.load_repo_info_from_file()
        self.save_repo_info_to_file()

    draw = ui_prefs.draw_prefs

registry = [
    SVN_addon_preferences
]
