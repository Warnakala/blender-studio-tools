# SPDX-License-Identifier: GPL-2.0-or-later
# (c) 2022, Blender Foundation - Demeter Dzadik

import bpy
from typing import List, Dict, Union, Any, Set, Optional, Tuple

import subprocess

from .simple_commands import May_Modifiy_Current_Blend
from .execute_subprocess import execute_svn_command
from .background_process import BackgroundProcess, process_in_background, processes
from ..util import redraw_viewport, get_addon_prefs


class SVN_update_all(May_Modifiy_Current_Blend, bpy.types.Operator):
    bl_idname = "svn.update_all"
    bl_label = "SVN Update All"
    bl_description = "Download all the latest updates from the remote repository"
    bl_options = {'INTERNAL'}

    @classmethod
    def poll(cls, context):
        prefs = get_addon_prefs(context)
        if prefs.is_busy:
            # Don't allow attempting to Update/Commit while either is still running.
            return False

        for f in prefs.get_current_repo(context).external_files:
            if f.repos_status != 'none':
                return True

        return True

    def invoke(self, context, event):
        repo = context.scene.svn.get_repo(context)
        current_blend = repo.current_blend_file
        if current_blend and current_blend.repos_status != 'none':
            self.file_rel_path = current_blend.svn_path
            return context.window_manager.invoke_props_dialog(self, width=500)
        return self.execute(context)

    def execute(self, context: bpy.types.Context) -> Set[str]:
        self.set_predicted_file_statuses(context)
        processes['Status'].stop()
        if self.reload_file:
            self.execute_svn_command(
                context, 
                ["svn", "up", "--accept", "postpone"],
                use_cred=True
            )
            bpy.ops.wm.open_mainfile(filepath=bpy.data.filepath, load_ui=False)
            processes['Log'].start()
        else:
            process_in_background(BGP_SVN_Update)
            get_addon_prefs(context).is_busy = True

        return {"FINISHED"}

    def set_predicted_file_statuses(self, context):
        repo = context.scene.svn.get_repo(context)
        for f in repo.external_files:
            status_predict_flag_bkp = f.status_predicted_flag
            f.status_predicted_flag = "UPDATE"
            if f.repos_status == 'modified' and f.status == 'normal':
                # Modified on remote, exists on local.
                f.repos_status = 'none'
            elif f.repos_status == 'added' and f.status == 'none':
                # Added on remote, doesn't exist on local.
                f.status = 'normal'
            elif f.repos_status == 'deleted' and f.status == 'normal':
                # Deleted on remote, exists on local.
                # NOTE: File entry should just be deleted.
                f.status = 'none'
                f.repos_status = 'none'
            elif f.repos_status == 'none':
                f.status_predicted_flag = status_predict_flag_bkp
            else:
                f.status = 'conflicted'


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
            processes['Status'].start()

    def process_output(self, context, prefs):
        print("SVN Update complete:")
        print("\n".join(self.output.split("\n")[1:]))
        for f in context.scene.svn.get_repo(context).external_files:
            if f.status_predicted_flag == 'UPDATE':
                f.status_predicted_flag = 'SINGLE'

        prefs.is_busy = False
        processes['Log'].start()
        processes['Status'].start()


registry = [
    SVN_update_all
]
