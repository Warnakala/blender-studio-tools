# SPDX-License-Identifier: GPL-2.0-or-later
# (c) 2023, Blender Foundation - Demeter Dzadik

import bpy
from typing import List, Dict, Union, Any, Set, Optional, Tuple

import subprocess

from ..util import redraw_viewport
from .execute_subprocess import execute_svn_command
from .background_process import BackgroundProcess, Processes
from ..util import get_addon_prefs


class BGP_SVN_Update(BackgroundProcess):
    name = "Update"
    needs_authentication = True
    timeout = 5*60
    repeat_delay = 0
    debug = False

    def tick(self, context, prefs):
        redraw_viewport()

    def acquire_output(self, context, prefs):
        try:
            self.output = execute_svn_command(
                context, 
                ["svn", "up", "--accept", "postpone"],
                use_cred=True
            )
        except subprocess.CalledProcessError as error:
            self.error = error.stderr.decode()
            prefs.is_busy = False
            Processes.start('Status')

    def process_output(self, context, prefs):
        print("SVN Update complete:")
        print("\n".join(self.output.split("\n")[1:]))
        for f in context.scene.svn.get_repo(context).external_files:
            if f.status_predicted_flag == 'UPDATE':
                f.status_predicted_flag = 'SINGLE'

        prefs.is_busy = False
        Processes.start('Log')
        Processes.start('Status')

    def stop(self):
        get_addon_prefs(bpy.context).is_busy = False
        super().stop()
