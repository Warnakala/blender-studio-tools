from typing import List, Dict, Union, Any, Set, Optional, Tuple

import threading

import bpy

from .svn_log import svn_log_background_fetch_start
from .ops import May_Modifiy_Current_Blend
from .execute_subprocess import execute_svn_command

SVN_UPDATE_THREAD = None
SVN_UPDATE_OUTPUT = ""


class SVN_update_all(May_Modifiy_Current_Blend, bpy.types.Operator):
    bl_idname = "svn.update_all"
    bl_label = "SVN Update All"
    bl_description = "Download all the latest updates from the remote repository"
    bl_options = {'INTERNAL'}

    @classmethod
    def poll(cls, context):
        if SVN_UPDATE_THREAD:
            # Don't allow creating another thread while the previous one is still running.
            return False
        for f in context.scene.svn.external_files:
            if f.repos_status != 'none':
                return True
        return False

    def invoke(self, context, event):
        svn = context.scene.svn
        current_blend = svn.current_blend_file
        if current_blend.repos_status != 'none':
            self.file_rel_path = current_blend.svn_path
            return context.window_manager.invoke_props_dialog(self, width=500)
        return self.execute(context)

    def execute(self, context: bpy.types.Context) -> Set[str]:
        self.set_predicted_file_statuses(context)
        if self.reload_file:
            context.scene.svn.ignore_next_status_update = True
            self.execute_svn_command(context, 'svn up --accept "postpone"', use_cred=True)
            bpy.ops.wm.open_mainfile(filepath=bpy.data.filepath, load_ui=False)
            svn_log_background_fetch_start()
        else:
            svn_update_background_start()

        return {"FINISHED"}

    def set_predicted_file_statuses(self, context):
        for f in context.scene.svn.external_files:
            if f.repos_status == 'modified':
                if f.status == 'normal':
                    f.status = 'normal'
                    f.repos_status = 'none'
                    print("Predict file status to be normal/none due to svn up on ", f.svn_path)
                else:
                    f.status = 'conflicted'
                f.status_predicted_flag = "UPDATE"

def async_svn_update():
    """This function should be executed from a separate thread to avoid freezing 
    Blender's UI during execute_svn_command().
    """
    global SVN_UPDATE_OUTPUT
    SVN_UPDATE_OUTPUT = ""

    context = bpy.context
    print("Updating SVN files in background...")
    SVN_UPDATE_OUTPUT = execute_svn_command(context, 'svn up --accept "postpone"', use_cred=True)


def timer_svn_update():
    global SVN_UPDATE_OUTPUT
    global SVN_UPDATE_THREAD
    context = bpy.context

    if SVN_UPDATE_THREAD and SVN_UPDATE_THREAD.is_alive():
        # Process is still running, so we just gotta wait. Let's try again in 1s.
        return 1.0
    elif SVN_UPDATE_OUTPUT:
        print("SVN Update complete:")
        print(SVN_UPDATE_OUTPUT)
        for f in context.scene.svn.external_files:
            if f.status_predicted_flag == 'UPDATE':
                f.status_predicted_flag = 'SINGLE'
        svn_update_background_stop()
        svn_log_background_fetch_start()
        SVN_UPDATE_OUTPUT = ""
        SVN_UPDATE_THREAD = None
        return

    SVN_UPDATE_THREAD = threading.Thread(target=async_svn_update, args=())
    SVN_UPDATE_THREAD.start()

    return 1.0


def svn_update_background_start(_dummy1=None, _dummy2=None):
    if not bpy.app.timers.is_registered(timer_svn_update):
        bpy.app.timers.register(timer_svn_update, persistent=True)


def svn_update_background_stop(_dummy1=None, _dummy2=None):
    if bpy.app.timers.is_registered(timer_svn_update):
        bpy.app.timers.unregister(timer_svn_update)
    global SVN_UPDATE_THREAD
    SVN_UPDATE_THREAD = None

registry = [
    SVN_update_all
]
