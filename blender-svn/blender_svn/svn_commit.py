from typing import List, Dict, Union, Any, Set, Optional, Tuple

import threading, subprocess

import bpy
from bpy.props import StringProperty, BoolVectorProperty

from .background_process import processes, BackgroundProcess, process_in_background
from .props import SVN_file
from .ops import SVN_Operator, Popup_Operator
from .execute_subprocess import execute_svn_command


commit_message = StringProperty(
    name = "Commit Message",
    description = "Describe the changes being committed",
    options={'SKIP_SAVE'}
)


class SVN_commit(SVN_Operator, Popup_Operator, bpy.types.Operator):
    bl_idname = "svn.commit"
    bl_label = "SVN Commit"
    bl_description = "Commit a selection of files to the remote repository"
    bl_options = {'INTERNAL'}
    bl_property = "commit_message_0"  # Focus the text input box

    MAX_LINES = 32
    __annotations__ = {f'commit_message_{i}' : commit_message for i in range(MAX_LINES)}

    selection: BoolVectorProperty(
        size = 32,
        options = {'SKIP_SAVE'},
        default = [True] * 32
    )

    @staticmethod
    def get_committable_files(context) -> List[SVN_file]:
        """Return the list of file entries whose status allows committing"""
        svn_file_list = context.scene.svn.external_files
        committable_statuses = ['modified', 'added', 'deleted']
        files_to_commit = [f for f in svn_file_list if f.status in committable_statuses]
        return files_to_commit

    @classmethod
    def poll(cls, context):
        if 'Commit' in processes and processes['Commit'].is_running:
            # Don't allow starting a new commit if the previous one isn't finished yet.
            return False
        return cls.get_committable_files(context)

    def draw(self, context):
        """Draws the boolean toggle list with a list of strings for the button texts."""
        layout = self.layout
        files = self.get_committable_files(context)
        layout.label(text="These files will be pushed to the remote repository:")
        svn = context.scene.svn
        row = layout.row()
        row.label(text="Filename")
        row.label(text="Status")
        for idx, file in enumerate(files[:32]):
            row = layout.row()
            row.prop(self, "selection", index=idx, text=file.name)
            text = file.status_name
            icon = file.status_icon
            if file == svn.current_blend_file and bpy.data.is_dirty:
                text += " but not saved!"
                icon = 'ERROR'
                row.alert = True
            row.label(text=text, icon=icon)

        row = layout.row()
        row.label(text="Commit message:")
        self.last_idx = 0
        for i in range(type(self).MAX_LINES):
            if getattr(self, f'commit_message_{i}') != "":
                self.last_idx = min(i+1, self.MAX_LINES)
        for i in range(0, max(3, self.last_idx+2)):
            # Draw input boxes until the last one that has text, plus two, minimum three.
            # Why two after the last line? Because then you can use Tab to go to the next line.
            # Why at least 3 lines? Because then you can write a one-liner without
            # the OK button jumping away.
            layout.prop(self, f'commit_message_{i}', text="")
            continue

    def execute(self, context: bpy.types.Context) -> Set[str]:
        committable_files = self.get_committable_files(context)
        files_to_commit = [f for i, f in enumerate(committable_files[:32]) if self.selection[i]]

        if not files_to_commit:
            self.report({'ERROR'}, "No files were selected, nothing to commit.")
            return {'CANCELLED'}

        if len(self.commit_message_0) < 2:
            self.report({'ERROR'}, "Please describe your changes in the commit message.")
            return {'CANCELLED'}

        commit_message_lines = [getattr(self, f'commit_message_{i}') for i in range(self.last_idx)]
        commit_message = "\n".join(commit_message_lines)

        filepaths = [f.svn_path for f in files_to_commit]

        self.set_predicted_file_statuses(context, filepaths)
        process_in_background(BGP_SVN_Commit, commit_msg=commit_message, file_list = filepaths)

        report = f"{(len(files_to_commit))} files"
        if len(files_to_commit) == 1:
            report = files_to_commit[0].svn_path
        self.report({'INFO'}, f"Started committing {report}. See console for when it's finished.")

        return {"FINISHED"}

    def set_predicted_file_statuses(self, context, filepaths):
        for filepath in filepaths:
            f = context.scene.svn.get_file_by_svn_path(filepath)
            if f.status != 'deleted':
                if f.repos_status == 'none':
                    f.status = 'normal'
                else:
                    f.status = 'conflicted'
            f.status_predicted_flag = "COMMIT"


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
        filepaths = " ".join(self.file_list)

        if not self.commit_msg:
            self.stop()
            return

        try:
            sanitized_commit_msg = self.commit_msg.replace('"', "'")
            self.output = execute_svn_command(context, f'svn commit -m "{sanitized_commit_msg}" {filepaths}', use_cred=True)
        except subprocess.CalledProcessError as error:
            print("Commit failed.")
            self.error = error.stderr.decode()

    def process_output(self, context, prefs):
        print(self.output)
        for f in context.scene.svn.external_files:
            if f.status_predicted_flag == 'COMMIT':
                f.status_predicted_flag = 'SINGLE'
        processes['Log'].start()

        self.commit_msg = ""
        self.file_list = []

registry = [
    SVN_commit
]
