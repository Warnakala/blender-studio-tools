# SPDX-License-Identifier: GPL-2.0-or-later
# (c) 2022, Blender Foundation - Demeter Dzadik

from typing import List, Dict, Union, Any, Set, Optional, Tuple

import subprocess

import bpy
from bpy.props import StringProperty

from .background_process import processes, BackgroundProcess, process_in_background
from .simple_commands import SVN_Operator, Popup_Operator
from .execute_subprocess import execute_svn_command
from ..util import get_addon_prefs

# Hacks upon hacks! All for a tiny bit of nice UX...
active_commit_operator = None

class SVN_commit_msg_clear(bpy.types.Operator):
    bl_idname = "svn.clear_commit_message"
    bl_label = "Clear SVN Commit Message"
    bl_description = "Clear the commit message"
    bl_options = {'INTERNAL'}

    def execute(self, context):
        context.scene.svn.get_repo(context).commit_message = ""
        global active_commit_operator
        active_commit_operator.first_line = ""
        return {'FINISHED'}


class SVN_commit(SVN_Operator, Popup_Operator, bpy.types.Operator):
    bl_idname = "svn.commit"
    bl_label = "SVN Commit"
    bl_description = "Commit a selection of files to the remote repository"
    bl_options = {'INTERNAL'}
    bl_property = "first_line"  # Focus the text input box

    # The first line of the commit message needs to be an operator property in order
    # for us to be able to focus the input box automatically when the window pops up
    # (see bl_property above)
    def update_first_line(self, context):
        repo = context.scene.svn.get_repo(context)
        repo.commit_lines[0].line = self.first_line

    first_line: StringProperty(
        name="First Line",
        description="First line of the commit message",
        update=update_first_line
    )

    @staticmethod
    def get_committable_files(context) -> List["SVN_file"]:
        """Return the list of file entries whose status allows committing"""
        svn_file_list = context.scene.svn.get_repo(context).external_files
        committable_statuses = ['modified', 'added', 'deleted']
        files_to_commit = [
            f for f in svn_file_list if f.status in committable_statuses]
        return files_to_commit

    @classmethod
    def poll(cls, context):
        prefs = get_addon_prefs(context)
        if prefs.is_busy:
            # Don't allow attempting to Update/Commit while either is still running.
            return False

        return cls.get_committable_files(context)

    def invoke(self, context, event):
        prefs = get_addon_prefs(context)
        repo = prefs.get_current_repo(context)
        if repo.commit_message == "":
            repo.commit_message = ""

        global active_commit_operator
        active_commit_operator = self

        self.first_line = repo.commit_lines[0].line

        for f in repo.external_files:
            f.include_in_commit = False
        for f in self.get_committable_files(context):
            f.include_in_commit = True

        return super().invoke(context, event)

    def draw(self, context):
        """Draws the boolean toggle list with a list of strings for the button texts."""
        layout = self.layout
        files = self.get_committable_files(context)
        layout.label(
            text="These files will be pushed to the remote repository:")
        repo = context.scene.svn.get_repo(context)
        row = layout.row()
        row.label(text="Filename")
        row.label(text="Status")
        for file in files:
            row = layout.row()
            row.prop(file, "include_in_commit", text=file.name)
            text = file.status_name
            icon = file.status_icon
            if file == repo.current_blend_file and bpy.data.is_dirty:
                split = row.split(factor=0.7)
                row = split.row()
                row.alert = True
                text += " but not saved!"
                icon = 'ERROR'
                op_row = split.row()
                op_row.alignment = 'LEFT'
                op_row.operator('wm.save_mainfile', icon='FILE_BLEND', text="Save")
            row.label(text=text, icon=icon)

        row = layout.row()
        row.label(text="Commit message:")
        # Draw input box for first line, which is special because we want it to
        # get focused automatically for smooth UX. (see `bl_property` above)
        row = layout.row()
        row.prop(self, 'first_line', text="")
        row.operator(SVN_commit_msg_clear.bl_idname, text="", icon='TRASH')
        for i in range(1, len(repo.commit_lines)):
            # Draw input boxes until the last one that has text, plus two, minimum three.
            # Why two after the last line? Because then you can use Tab to go to the next line.
            # Why at least 3 lines? Because then you can write a one-liner without
            # the OK button jumping away.
            layout.prop(
                repo.commit_lines[i], 'line', index=i, text="")
            continue

    def execute(self, context: bpy.types.Context) -> Set[str]:
        committable_files = self.get_committable_files(context)
        files_to_commit = [f for f in committable_files if f.include_in_commit]
        prefs = get_addon_prefs(context)
        repo = context.scene.svn.get_repo(context)

        if not files_to_commit:
            self.report({'ERROR'},
                        "No files were selected, nothing to commit.")
            return {'CANCELLED'}

        if len(repo.commit_message) < 2:
            self.report({'ERROR'},
                        "Please describe your changes in the commit message.")
            return {'CANCELLED'}

        filepaths = [f.svn_path for f in files_to_commit]

        self.set_predicted_file_statuses(files_to_commit)
        process_in_background(
            BGP_SVN_Commit,
            commit_msg=repo.commit_message,
            file_list=filepaths
        )
        processes['Status'].stop()
        prefs.is_busy = True

        report = f"{(len(files_to_commit))} files"
        if len(files_to_commit) == 1:
            report = files_to_commit[0].svn_path
        self.report({'INFO'},
                    f"Started committing {report}. See console for when it's finished.")

        return {"FINISHED"}

    def set_predicted_file_statuses(self, file_entries):
        for f in file_entries:
            if f.status != 'deleted':
                if f.repos_status == 'none':
                    # We modified the file, and it was not modified on the repo,
                    # predict the status to be "normal".
                    f.status = 'normal'
                else:
                    # If we modified the file, but it was modified on the repo:
                    f.status = 'conflicted'
            # TODO: What happens if we DID delete the file, AND it was modified on the repo?
            # Should probably also predict a conflict.
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
        filepaths_str = " ".join(self.file_list)

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
            processes['Status'].start()

    def process_output(self, context, prefs):
        print(self.output)
        for f in context.scene.svn.get_repo(context).external_files:
            if f.status_predicted_flag == 'COMMIT':
                f.status_predicted_flag = 'SINGLE'
        processes['Log'].start()
        processes['Status'].start()

        self.commit_msg = ""
        repo.commit_message = ""
        prefs.is_busy = False
        self.file_list = []


registry = [
    SVN_commit_msg_clear,
    SVN_commit
]
