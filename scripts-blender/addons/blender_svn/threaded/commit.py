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

        try:
            sanitized_commit_msg = self.commit_msg.replace('"', "'")
            command = ["svn", "commit", "-m", f"{sanitized_commit_msg}"] + self.file_list

            self.output = execute_svn_command(
                context,
                command,
                use_cred=True
            )
        except subprocess.CalledProcessError as error:
            print("Commit failed.")
            self.error = error.stderr.decode()
            prefs.is_busy = False
            Processes.start('Status')

    def process_output(self, context, prefs):
        print(self.output)
        repo = context.scene.svn.get_repo(context)
        for f in repo.external_files:
            if f.status_predicted_flag == 'COMMIT':
                f.status_predicted_flag = 'SINGLE'
        Processes.start('Log')
        Processes.start('Status')

        self.commit_msg = ""
        repo.commit_message = ""
        prefs.is_busy = False
        self.file_list = []

    def stop(self):
        get_addon_prefs(bpy.context).is_busy = False
        super().stop()
