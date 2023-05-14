# SPDX-License-Identifier: GPL-2.0-or-later
# (c) 2022, Blender Foundation - Demeter Dzadik

from . import wheels
# This will load the xmltodict wheel file.
wheels.preload_dependencies()

import subprocess
import bpy
from .background_process import BackgroundProcess, process_in_background, processes
from . import constants
from .util import get_addon_prefs, redraw_viewport
from .execute_subprocess import execute_svn_command, execute_command
from bpy.props import StringProperty
from typing import List, Dict, Union, Any, Set, Optional, Tuple
from pathlib import Path
from datetime import datetime
import xmltodict



class SVN_explain_status(bpy.types.Operator):
    bl_idname = "svn.explain_status"
    bl_label = ""  # Don't want the first line of the tooltip on mouse hover.
    bl_description = "Show an explanation of this status, using a dynamic tooltip"
    bl_options = {'INTERNAL'}

    status: StringProperty(
        description="Identifier of the status to show an explanation for"
    )
    file_rel_path: StringProperty(
        description="Path of the file to select in the list when clicking this explanation, to act as if it was click-through-able"
    )

    @staticmethod
    def get_explanation(status: str):
        return constants.SVN_STATUS_DATA[status][1]

    @classmethod
    def description(cls, context, properties):
        return cls.get_explanation(properties.status)

    def draw(self, context):
        self.layout.label(text=self.get_explanation(self.status))

    def execute(self, context):
        """Set the index on click, to act as if this operator button was 
        click-through in the UIList."""
        if not self.file_rel_path:
            return {'FINISHED'}
        file_entry_idx = context.scene.svn.get_file_by_svn_path(
            self.file_rel_path, get_index=True)
        context.scene.svn.external_files_active_index = file_entry_idx
        return {'FINISHED'}


def get_svn_info(context, dirpath: Path) -> Optional[str]:
    try:
        path = dirpath.as_posix()
        return execute_command(path, ["svn", "info"])
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.decode()
        if "is not a working copy" in error_msg:
            return
        elif "E200009" in error_msg:
            # If we're in a folder that wasn't yet added to the repo,
            # try again one folder higher.
            parent = dirpath.parent
            if parent == dirpath:
                return
            return get_svn_info(context, dirpath.parent)
        else:
            raise e


def set_svn_info(context) -> bool:
    """Check if the current .blend file is in an SVN repository.
    If it is, use `svn info` to initialize basic info like the SVN URL.
    Return whether initialization was successful or not.
    """
    svn = context.scene.svn
    svn.svn_directory = ""
    dirpath = Path(bpy.data.filepath).parent
    output = get_svn_info(context, dirpath)
    if not output:
        svn.is_in_repo = False
        return False

    lines = output.split("\n")
    # Populate the addon prefs with svn info.
    svn.is_in_repo = True
    dir_path = lines[1].split("Working Copy Root Path: ")[1]
    # On Windows, for some reason the path has a \r character at the end,
    # which breaks absolutely everything.
    dir_path = dir_path.replace("\r", "")
    svn.svn_directory = dir_path

    full_url = lines[2].split("URL: ")[1]
    relative_url = lines[3].split("Relative URL: ")[1][1:]
    base_url = full_url.replace(relative_url, "")
    svn.svn_url = base_url
    # _relative_filepath = lines[3].split("Relative URL: ^")[1]
    # _revision_number = int(lines[6].split("Revision: ")[1])

    # datetime_str = lines[-3].split("Last Changed Date: ")[1]
    # _revision_date = svn_date_simple(datetime_str)
    # _revision_author = lines[-5].split("Last Changed Author: ")[1]
    return True


@bpy.app.handlers.persistent
def init_svn(_context, _dummy):
    """Initialize SVN info when opening a .blend file that is in a repo."""

    context = bpy.context   # Without this, context is sometimes a string containing the current filepath??

    svn = context.scene.svn
    if not bpy.data.filepath:
        svn.reset_info()
        return
    svn.is_busy = False

    in_repo = set_svn_info(context)

    if svn.external_files_active_index > len(svn.external_files):
        svn.external_files_active_index = 0
    svn.log_active_index = len(svn.log)-1
    if not in_repo:
        svn.external_files.clear()
        svn.log.clear()
        print("SVN: Initialization cancelled: This .blend is not in an SVN repository.")
        return

    svn.reload_svn_log(context)

    current_blend_file = svn.current_blend_file
    if not current_blend_file:
        f = svn.external_files.add()
        svn_path = svn.absolute_to_svn_path(bpy.data.filepath)
        f['svn_path'] = str(svn_path)
        f['name'] = svn_path.name
        f.status = 'unversioned'

    prefs = get_addon_prefs(context)
    cred = prefs.get_credentials()
    if not cred:
        cred = prefs.svn_credentials.add()
        cred.url = svn.svn_url
        cred.name = Path(svn.svn_directory).name
        print("SVN: Initialization failed. Try entering credentials.")
        return 1

    process_in_background(BGP_SVN_Status)
    processes['Log'].start()

    print("SVN: Initialization successful.")


################################################################################
############## AUTOMATICALLY KEEPING FILE STATUSES UP TO DATE ##################
################################################################################

class BGP_SVN_Status(BackgroundProcess):
    name = "Status"
    needs_authentication = True
    timeout = 10
    repeat_delay = 15
    debug = False

    def tick(self, context, prefs):
        if context.scene.svn.seconds_since_last_update > 30:
            redraw_viewport()

    def acquire_output(self, context, prefs):
        try:
            svn_status_str = execute_svn_command(
                context, 
                ["svn", "status", "--show-updates", "--verbose", "--xml"],
                use_cred=True
            )
            self.output = get_repo_file_statuses(svn_status_str)
        except subprocess.CalledProcessError as error:
            # TODO: If this is an authentication error, we should set cred.authenticated=False.
            # This could happen if the user's password has changed while Blender was running.
            self.error = error.stderr.decode()

    def process_output(self, context, prefs):
        update_file_list(context, self.output)

    def get_ui_message(self, context):
        # Calculate time since last status update
        svn = context.scene.svn
        if svn.seconds_since_last_update > 30:
            return "Updating file statuses..."


def update_file_list(context, file_statuses: Dict[str, Tuple[str, str, int]]):
    """Update the file list based on data from get_svn_file_statuses().
    (See timer_update_svn_status)"""
    svn = context.scene.svn
    svn.timestamp_last_status_update = datetime.strftime(
        datetime.now(), "%Y/%m/%d %H:%M:%S")

    posix_paths = []
    new_files_on_repo = set()
    for filepath_str, status_info in file_statuses.items():
        svn_path = Path(filepath_str)
        suffix = svn_path.suffix
        if (suffix.startswith(".r") and suffix[2:].isdecimal()) \
                or (suffix.startswith(".blend") and suffix[6:].isdecimal()) \
                or suffix.endswith("blend@"):
            # Do not add certain file extensions, ever:
            # .r### files are from SVN conflicts waiting to be resolved.
            # .blend@ is the Blender filesave temp file.
            # .blend### are Blender backup files.
            continue

        posix_paths.append(svn_path.as_posix())
        wc_status, repos_status, revision = status_info

        file_entry = svn.get_file_by_svn_path(svn_path)
        entry_existed = True
        if not file_entry:
            file_entry = svn.external_files.add()
            # NOTE: For some reason, if this posix is not explicitly converted to
            # str, accessing svn_path can cause a segfault.
            file_entry['svn_path'] = str(svn_path.as_posix())
            file_entry['name'] = svn_path.name
            entry_existed = False
            if not file_entry.exists:
                new_files_on_repo.add((file_entry, repos_status))

        if file_entry.status_predicted_flag == 'SINGLE':
            # File status was predicted by a local svn file operation,
            # so we should ignore this status update and reset the flag.
            # The file status will be updated on the next status update.
            # This is because this status update was initiated before the file's
            # status was predicted, so the prediction is likely to be correct,
            # and the status we have here is likely to be outdated.
            file_entry.status_predicted_flag = 'WAITING'
            continue
        elif file_entry.status_predicted_flag not in {'NONE', 'WAITING'}:
            # We wait for `svn up/commit` background processes to finish and
            # set the predicted flag to SINGLE. Until then, we ignore status
            # updates on files that are being updated or committed.
            continue

        if entry_existed and (file_entry.repos_status == 'none' and repos_status != 'none'):
            new_files_on_repo.add((file_entry, repos_status))

        file_entry.revision = revision
        file_entry.status = wc_status
        file_entry.repos_status = repos_status
        file_entry.status_predicted_flag = 'NONE'

    if new_files_on_repo:
        # File entry status has changed between local and repo.
        file_strings = []
        for file_entry, repos_status in new_files_on_repo:
            try:
                file_string = constants.SVN_STATUS_NAME_TO_CHAR[repos_status] + \
                    "    " + file_entry.svn_path
            except KeyError:
                print(
                    f"No status character for this status: {file_entry.svn_path} - {repos_status}")
                continue
            file_strings.append(file_string)
        print(
            "SVN: Detected file changes on remote:\n",
            "\n".join(file_strings),
            "\nUpdating log...\n"
        )
        processes['Log'].start()

    # Remove file entries who no longer seem to have an SVN status.
    # This can happen if an unversioned file was removed from the filesystem,
    # Or sub-folders whose parent was Un-Added to the SVN.
    for file_entry in svn.external_files[:]:
        if file_entry.svn_path not in posix_paths:
            svn.remove_file_entry(file_entry)

    svn.force_good_active_index(context)

def get_repo_file_statuses(svn_status_str: str) -> Dict[str, Tuple[str, str, int]]:
    svn_status_xml = xmltodict.parse(svn_status_str)
    file_infos = svn_status_xml['status']['target']['entry']
    # print(json.dumps(file_infos, indent=4))

    file_statuses = {}
    for file_info in file_infos:
        filepath = file_info['@path']

        repos_status = "none"
        if 'repos-status' in file_info:
            repos_status_block = file_info['repos-status']
            repos_status = repos_status_block['@item']
            _repo_props = repos_status_block['@props']
        # else:
            # TODO: I commented this out for now, but it may be a necessary optimization
            # if Blender starts stuttering due to the SVN status updates.
            # continue

        wc_status_block = file_info.get('wc-status')
        wc_status = wc_status_block['@item']
        _revision = int(wc_status_block.get('@revision', 0))
        _props = wc_status_block['@props']

        if 'commit' in wc_status_block:
            commit_block = wc_status_block['commit']
            commit_revision = int(commit_block['@revision'])
            _commit_author = commit_block['author']
            _commit_date = commit_block['date']
        else:
            commit_revision = 0

        file_statuses[filepath] = (wc_status, repos_status, commit_revision)

    return file_statuses


@bpy.app.handlers.persistent
def mark_current_file_as_modified(_dummy1=None, _dummy2=None):
    context = bpy.context
    svn = context.scene.svn
    if not svn.svn_directory:
        return
    current_blend = svn.current_blend_file
    if current_blend:
        current_blend.status = 'modified'
        current_blend.status_predicted_flag = 'SINGLE'


################################################################################
############################# REGISTER #########################################
################################################################################

def timer_init_svn(_dummy1=None, _dummy2=None):
    print("SVN: Initializing with some delay after file load...")
    return init_svn(bpy.context, None)


def register():
    bpy.app.handlers.load_post.append(init_svn)

    bpy.app.handlers.save_post.append(init_svn)
    bpy.app.handlers.save_post.append(mark_current_file_as_modified)

    bpy.app.timers.register(timer_init_svn, first_interval=1)


def unregister():
    bpy.app.handlers.load_post.remove(init_svn)

    bpy.app.handlers.save_post.remove(init_svn)
    bpy.app.handlers.save_post.remove(mark_current_file_as_modified)


registry = [SVN_explain_status]
