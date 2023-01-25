# SPDX-License-Identifier: GPL-2.0-or-later
# (c) 2022, Blender Foundation - Demeter Dzadik

from typing import List, Dict, Union, Any, Set, Optional, Tuple

import subprocess

import bpy

from .ops import May_Modifiy_Current_Blend
from .execute_subprocess import execute_svn_command
from .background_process import BackgroundProcess, process_in_background, processes
from .util import redraw_viewport


class SVN_update_all(May_Modifiy_Current_Blend, bpy.types.Operator):
    bl_idname = "svn.update_all"
    bl_label = "SVN Update All"
    bl_description = "Download all the latest updates from the remote repository"
    bl_options = {'INTERNAL'}

    @classmethod
    def poll(cls, context):
        if context.scene.svn.is_busy:
            # Don't allow attempting to Update/Commit while either is still running.
            return False

        for f in context.scene.svn.external_files:
            if f.repos_status != 'none':
                return True

        return True

    def invoke(self, context, event):
        svn = context.scene.svn
        current_blend = svn.current_blend_file
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
            context.scene.svn.is_busy = True

        return {"FINISHED"}

    def set_predicted_file_statuses(self, context):
        for f in context.scene.svn.external_files:
            if f.repos_status in ['modified', 'added']:
                # This case seemed to be triggering on false-positives
                # if f.repos_status == 'added' and f.exists:
                #     f.status = 'conflicted'
                if f.status == 'normal':
                    f.status = 'normal'
                    f.repos_status = 'none'
                elif f.exists:
                    f.status = 'conflicted'
                f.status_predicted_flag = "UPDATE"


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
            context.scene.svn.is_busy = False
            processes['Status'].start()

    def process_output(self, context, prefs):
        print("SVN Update complete:")
        print("\n".join(self.output.split("\n")[1:]))
        for f in context.scene.svn.external_files:
            if f.status_predicted_flag == 'UPDATE':
                f.status_predicted_flag = 'SINGLE'

        context.scene.svn.is_busy = False
        processes['Log'].start()
        processes['Status'].start()


registry = [
    SVN_update_all
]
