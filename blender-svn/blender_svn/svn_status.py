# ***** BEGIN GPL LICENSE BLOCK *****
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
# ***** END GPL LICENCE BLOCK *****
#
# (c) 2022, Blender Foundation - Demeter Dzadik

from typing import List, Dict, Union, Any, Set, Optional, Tuple
from pathlib import Path
from datetime import datetime

from . import wheels
# This will load the dateutil and svn wheel file.
wheels.preload_dependencies()

import xmltodict

import bpy, subprocess
from bpy.props import StringProperty

from .execute_subprocess import execute_svn_command, execute_command
from .util import get_addon_prefs, svn_date_simple, redraw_viewport
from . import constants
from .svn_log import svn_log_background_fetch_start

class SVN_explain_status(bpy.types.Operator):
    bl_idname = "svn.explain_status"
    bl_label = "" # Don't want the first line of the tooltip on mouse hover.
    bl_description = "Show an explanation of this status, using a dynamic tooltip"
    bl_options = {'INTERNAL'}

    status: StringProperty(
        description = "Identifier of the status to show an explanation for"
    )
    file_rel_path: StringProperty(
        description = "Path of the file to select in the list when clicking this explanation, to act as if it was click-through-able"
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
        file_entry_idx = context.scene.svn.get_file_by_svn_path(self.file_rel_path, get_index=True)
        context.scene.svn.external_files_active_index = file_entry_idx
        return {'FINISHED'}


def get_svn_info(context, dirpath: Path) -> Optional[str]:
    try:
        path = dirpath.as_posix()
        return execute_command(path, 'svn info')
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
    _relative_filepath = lines[3].split("Relative URL: ^")[1]
    _revision_number = int(lines[6].split("Revision: ")[1])

    datetime_str = lines[-3].split("Last Changed Date: ")[1]
    _revision_date = svn_date_simple(datetime_str)
    _revision_author = lines[-5].split("Last Changed Author: ")[1]
    return True


@bpy.app.handlers.persistent
def init_svn(context, dummy):
    """Initialize SVN info when opening a .blend file that is in a repo."""

    # We need to reset our global vars, otherwise with unlucky timing,
    # we can end up writing file entries of one repository to the .blend file
    # in another repository, when doing File->Open from one to the other.
    global SVN_STATUS_OUTPUT
    global SVN_STATUS_THREAD
    global SVN_STATUS_NEWFILE
    SVN_STATUS_OUTPUT = {}
    SVN_STATUS_THREAD = None
    SVN_STATUS_NEWFILE = True

    if not context:
        context = bpy.context

    svn = context.scene.svn
    if not bpy.data.filepath:
        svn.reset_info()
        return

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
        f.is_referenced = True

    prefs = get_addon_prefs(context)
    svn_url = svn.svn_url
    cred = prefs.get_credentials()
    if not cred:
        cred = prefs.svn_credentials.add()
        cred.url = svn_url
        cred.name = Path(svn.svn_directory).name
        print("SVN: Initialization failed. Try entering credentials.")
        return

    svn_status_background_fetch_start()
    print("SVN: Initialization successful.")


################################################################################
############## AUTOMATICALLY KEEPING FILE STATUSES UP TO DATE ##################
################################################################################

import threading
SVN_STATUS_OUTPUT = {}
SVN_STATUS_THREAD = None
# Flag to let is_referenced flags be set only once on file open and file save.
# We need the flag because this needs to happen not immediately on file open,
# but after the first `svn status` call has finished in the background.
# Also we want it to run in the background even on file save, otherwise the UI
# lock-up from the file saving process is noticably longer.
SVN_STATUS_NEWFILE = True

def async_get_verbose_svn_status():
    """This function should be executed from a separate thread to avoid freezing 
    Blender's UI during execute_svn_command().
    """
    global SVN_STATUS_OUTPUT
    global SVN_STATUS_NEWFILE
    SVN_STATUS_OUTPUT = ""

    context = bpy.context
    prefs = get_addon_prefs(context)
    cred = prefs.get_credentials()
    if not cred.authenticated:
        return
    svn_status_str = execute_svn_command(context, 'svn status --show-updates --verbose --xml')
    SVN_STATUS_OUTPUT = get_repo_file_statuses(svn_status_str)

    if SVN_STATUS_NEWFILE:
        update_file_is_referenced_flags()
        SVN_STATUS_NEWFILE = False

@bpy.app.handlers.persistent
def timer_update_svn_status():
    context = bpy.context
    svn = context.scene.svn
    svn.update_time_since_last_update()
    redraw_viewport()
    prefs = get_addon_prefs(context)

    cred = prefs.get_credentials()

    if not svn.is_in_repo or not (cred.username and cred.password):
        svn_status_background_fetch_stop()
        return

    global SVN_STATUS_THREAD
    if SVN_STATUS_THREAD and SVN_STATUS_THREAD.is_alive():
        # Process is still running, so we just gotta wait. Let's try again in 1s.
        return 1.0
    elif SVN_STATUS_OUTPUT:
        update_file_list(context, SVN_STATUS_OUTPUT)
        context.scene.svn.timestamp_last_status_update = datetime.strftime(datetime.now(), "%Y/%m/%d %H:%M:%S")

    SVN_STATUS_THREAD = threading.Thread(target=async_get_verbose_svn_status, args=())
    SVN_STATUS_THREAD.start()

    return 1.0


def update_file_list(context, file_statuses: Dict[str, Tuple[str, str, int]]):
    """Update the file list based on data from get_svn_file_statuses().
    (See timer_update_svn_status)"""
    svn = context.scene.svn

    posix_paths = []
    new_files_on_repo = False
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
            file_entry['svn_path'] = svn_path.as_posix()
            file_entry['name'] = svn_path.name
            entry_existed = False
            if not file_entry.exists:
                new_files_on_repo = True

        if file_entry.status_predicted_flag == 'SINGLE':
            # File status was predicted by a local svn file operation, 
            # so we should ignore this status update and reset the flag.
            # The file status will be updated on the next status update.
            # This is because this status update was initiated before the file's
            # status was predicted, so the prediction is likely to be correct,
            # and the status we have here is likely to be outdated.
            file_entry.status_predicted_flag = 'NONE'
            continue
        elif file_entry.status_predicted_flag != 'NONE':
            # We wait for `svn up/commit` background processes to finish and
            # set the predicted flag to SINGLE. Until then, we ignore status 
            # updates on files that are being updated or committed.
            continue

        if not entry_existed and (file_entry.repos_status == 'none' and repos_status != 'none'):
            new_files_on_repo = True

        file_entry.revision = revision
        file_entry.status = wc_status
        file_entry.repos_status = repos_status

    if new_files_on_repo:
        # File entry status has changed between local and repo.
        print("SVN: Files have changed on the repository, updating log...")
        svn_log_background_fetch_start()


    # Remove file entries who no longer seem to have an SVN status.
    # This can happen if an unversioned file was removed from the filesystem,
    # Or sub-folders whose parent was Un-Added to the SVN.
    for file_entry in svn.external_files[:]:
        if file_entry.svn_path not in posix_paths:
            svn.remove_file_entry(file_entry)

    current_blend = svn.current_blend_file
    if current_blend:
        current_blend.is_referenced = True

    svn.force_good_active_index(context)


@bpy.app.handlers.persistent
def update_file_is_referenced_flags(_dummy1=None, _dummy2=None):
    """Update the file list's is_referenced flags. This should only be called on
    file save, because it relies on BAT, which relies on reading a file from disk,
    so calling it any more frequently would be pointless."""
    import sys
    if sys.platform == 'win32':
        # TODO: Apparently, calling BAT's trace.deps() on Windows on the
        # current .blend file makes us unable to save the file from that point on...
        return
    
    context = bpy.context
    svn = context.scene.svn
    referenced_files: Set[Path] = svn.get_referenced_filepaths()
    referenced_files.add(Path(bpy.data.filepath))

    referenced_svn_files = []
    for f in referenced_files:
        try:
            svn_path = str(svn.absolute_to_svn_path(f))
            referenced_svn_files.append(svn_path)
        except ValueError:
            # This happens when a file is referened that is not on the SVN.
            # Let's not display such files in the SVN file window,
            # Listing a complete list of dependencies is not the goal of this addon.
            # referenced_files.remove(f)
            pass

    for file_entry in svn.external_files:
        file_entry.is_referenced = file_entry.svn_path in referenced_svn_files


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
def svn_status_background_fetch_start(_dummy1=None, _dummy2=None):
    if not bpy.app.timers.is_registered(timer_update_svn_status):
        bpy.app.timers.register(timer_update_svn_status, persistent=True)


def svn_status_background_fetch_stop(_dummy1=None, _dummy2=None):
    if bpy.app.timers.is_registered(timer_update_svn_status):
        bpy.app.timers.unregister(timer_update_svn_status)
    global SVN_STATUS_THREAD
    SVN_STATUS_THREAD = None


@bpy.app.handlers.persistent
def mark_current_file_as_modified(_dummy1=None, _dummy2=None):
    context = bpy.context
    svn = context.scene.svn
    current_blend = svn.current_blend_file
    if current_blend:
        current_blend.status = 'modified'
        current_blend.status_predicted_flag = 'SINGLE'


################################################################################
############################# REGISTER #########################################
################################################################################

def register():
    bpy.app.handlers.load_post.append(init_svn)

    bpy.app.handlers.save_post.append(init_svn)
    bpy.app.handlers.save_post.append(mark_current_file_as_modified)
    svn_status_background_fetch_start()

    # bpy.app.handlers.load_post.append(update_file_is_referenced_flags)

def unregister():
    bpy.app.handlers.load_post.remove(init_svn)

    bpy.app.handlers.save_post.remove(init_svn)
    bpy.app.handlers.save_post.remove(mark_current_file_as_modified)
    svn_status_background_fetch_stop()

    # bpy.app.handlers.load_post.remove(update_file_is_referenced_flags)

registry = [SVN_explain_status]
