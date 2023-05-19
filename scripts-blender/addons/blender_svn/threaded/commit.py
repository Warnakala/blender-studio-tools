# SPDX-License-Identifier: GPL-2.0-or-later
# (c) 2023, Blender Foundation - Demeter Dzadik

import bpy
from typing import List, Dict, Union, Any, Set, Optional, Tuple

import subprocess

from .background_process import Processes, BackgroundProcess
from .execute_subprocess import execute_svn_command
from ..util import get_addon_prefs

class BGP_SVN_Commit(BackgroundProcess):
    name = "Commit"
    needs_authentication = True
    timeout = 5*60
    repeat_delay = 0
    debug = False

    def __init__(self, commit_msg: str, file_list: List[str]):
        super().__init__()

        self.commit_msg = commit_msg
        self.file_list = file_list

    def acquire_output(self, context, prefs):
        """This function should be executed from a separate thread to avoid freezing 
        Blender's UI during execute_svn_command().
        """
        if not self.commit_msg:
            self.stop()
            return

        Processes.kill('Status')
        sanitized_commit_msg = self.commit_msg.replace('"', "'")
        command = ["svn", "commit", "-m", f"{sanitized_commit_msg}"] + self.file_list
        self.output = execute_svn_command(
            context,
            command,
            use_cred=True
        )

    def handle_error(self, context, error):
        print("Commit failed.")
        Processes.start('Status')
        super().handle_error(context, error)

    def process_output(self, context, prefs):
        print(self.output)
        repo = context.scene.svn.get_repo(context)
        for f in repo.external_files:
            if f.status_prediction_type == 'SVN_COMMIT':
                f.status_prediction_type = 'SKIP_ONCE'
        Processes.start('Log')
        Processes.start('Status')
        repo.commit_message = ""
        Processes.kill('Commit')

    def get_ui_message(self, context) -> str:
        """Return a string that should be drawn in the UI for user feedback, 
        depending on the state of the process."""

        if self.is_running:
            plural = "s" if len(self.file_list) > 1 else ""
            return f"Committing {len(self.file_list)} file{plural}..."
        return ""

    def stop(self):
        super().stop()
    