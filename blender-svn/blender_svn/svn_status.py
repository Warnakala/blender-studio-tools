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
from collections import OrderedDict
from pathlib import Path

from . import wheels
# This will load the dateutil and svn wheel file.
wheels.preload_dependencies()

import xmltodict

import bpy
from bpy.props import StringProperty

from .execute_subprocess import execute_svn_command, execute_svn_command_nofreeze, subprocess_request_output
from .util import get_addon_prefs, svn_date_simple


SVN_STATUS_DATA = OrderedDict(
    [
        (
            "added",
            (
                "ADD",
                "This file was added",
            ),
        ),
        (
            "conflicted",
            (
                "ERROR",
                "This file was modified locally, and a newer version has appeared on the remote repository at the same time. To resolve the conflict, one of the changes must be discarded",
            ),
        ),
        (
            "deleted",
            (
                "TRASH",
                "This file was deleted",
            ),
        ),
        (
            "external",
            (
                "EXTERNAL_DRIVE",
                "This file is present because of an externals definition",
            ),
        ),
        (
            "ignored",
            (
                "RADIOBUT_OFF",
                "This file is being ignored (e.g., with the svn:ignore property)",
            ),
        ),
        (
            "incomplete",
            (
                "FOLDER_REDIRECT",
                "A directory is incomplete (a checkout or update was interrupted)",
            ),
        ),
        ("merged", ("AUTOMERGE_ON", "TODO")),
        (
            "missing",
            (
                "FILE_HIDDEN",
                "This file is missing (e.g., you moved or deleted it without using svn)",
            ),
        ),
        (
            "modified",
            (
                "MODIFIER",
                "This file was modified",
            ),
        ),
        (
            "none",
            (
                "TIME",
                "There is a newer version of this file available on the remote repository. You should update it",
            ),
        ),
        (
            "normal",
            (
                "CHECKMARK",
                "This file is in the repository. There are no local modifications to commit",
            ),
        ),
        ("obstructed", ("ERROR", "Something has gone horribly wrong. Try svn cleanup")),
        (
            "replaced",
            (
                "FILE_REFRESH",
                "This file has been moved",
            ),
        ),
        (
            "unversioned",
            (
                "FILE_NEW",
                "This file is new in file system, but not yet added to the local repository. It needs to be added before it can be committed to the remote repository",
            ),
        ),
    ]
)


# Based on PySVN/svn/constants.py/STATUS_TYPE_LOOKUP.
ENUM_SVN_STATUS = [
    (status, status.title(), SVN_STATUS_DATA[status][1], SVN_STATUS_DATA[status][0], i)
    for i, status in enumerate(SVN_STATUS_DATA.keys())
]


SVN_STATUS_CHAR = {
    '' : 'normal',
    'A' : 'added',
    'D' : 'deleted',
    'M' : 'modified',
    'R' : 'replaced',
    'C' : 'conflicted',
    'X' : 'external',
    'I' : 'ignored',
    '?' : 'unversioned',
    '!' : 'missing',
    '~' : 'replaced'
}


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
        return SVN_STATUS_DATA[status][1]

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
        i, _file = context.scene.svn.get_file_by_svn_path(self.file_rel_path)
        context.scene.svn.external_files_active_index = i
        return {'FINISHED'}


def set_svn_info(context) -> bool:
    prefs = get_addon_prefs(context)
    output = execute_svn_command(str(Path(bpy.data.filepath).parent), 'svn info')
    lines = output.split("\n")
    if len(lines) == 1:
        prefs.is_in_repo = False
        prefs.reset()
        return False

    # Populate the addon prefs with svn info.
    prefs.is_in_repo = True
    prefs['svn_directory'] = lines[1].split("Working Copy Root Path: ")[1]
    prefs['svn_url'] = lines[2].split("URL: ")[1]
    prefs['relative_filepath'] = lines[3].split("Relative URL: ^")[1]
    prefs['revision_number'] = int(lines[6].split("Revision: ")[1])

    datetime_str = lines[-3].split("Last Changed Date: ")[1]
    prefs['revision_date'] = svn_date_simple(datetime_str)
    prefs['revision_author'] = lines[-5].split("Last Changed Author: ")[1]
    return prefs


@bpy.app.handlers.persistent
def init_svn(context, dummy):
    """Initialize SVN info when opening a .blend file that is in a repo."""

    # We need to reset our global vars, otherwise with unlucky timing,
    # we can end up writing file entries of one repository to the .blend file
    # in another repository, when doing File->Open from one to the other.
    global SVN_STATUS_OUTPUT
    global SVN_STATUS_THREAD
    SVN_STATUS_OUTPUT = {}
    SVN_STATUS_THREAD = None

    if not context:
        context = bpy.context

    if not bpy.data.filepath:
        get_addon_prefs(context).reset()
        return

    svn_info = set_svn_info(context)
    if not svn_info:
        context.scene.svn.external_files.clear()
        context.scene.svn.log.clear()

    context.scene.svn.external_files_active_index = 0
    context.scene.svn.log_active_index = 0
    context.scene.svn.reload_svn_log(context)



################################################################################
############## AUTOMATICALLY KEEPING FILE STATUSES UP TO DATE ##################
################################################################################

import threading
SVN_STATUS_OUTPUT = {}
SVN_STATUS_THREAD = None

def async_get_verbose_svn_status():
    """The communicate() call blocks execution until the SVN command completes,
    so this function should be executed from a separate thread.
    """
    global SVN_STATUS_OUTPUT
    SVN_STATUS_OUTPUT = ""

    context = bpy.context
    prefs = get_addon_prefs(context)
    popen = execute_svn_command_nofreeze(prefs.svn_directory, 'svn status --show-updates --verbose --xml')
    svn_status_str = popen.communicate()[0].decode()
    SVN_STATUS_OUTPUT = get_repo_file_statuses(svn_status_str)

@bpy.app.handlers.persistent
def timer_update_svn_status():
    global SVN_STATUS_OUTPUT
    global SVN_STATUS_THREAD
    context = bpy.context
    prefs = get_addon_prefs(context)

    if not prefs.is_in_repo:
        return

    if not prefs.status_update_in_background:
        svn_status_background_fetch_stop()
        return

    if SVN_STATUS_THREAD and SVN_STATUS_THREAD.is_alive():
        # Process is still running, so we just gotta wait. Let's try again in 1s.
        return 1.0
    else:
        # print("Update file list...")
        update_file_list(context, SVN_STATUS_OUTPUT)

    # print("Starting thread...")
    SVN_STATUS_THREAD = threading.Thread(target=async_get_verbose_svn_status, args=())
    SVN_STATUS_THREAD.start()

    return 1.0


def update_file_list(context, file_statuses: Dict[str, Tuple[str, str, int]]):
    """Update the file list based on data from an svn command's output.
    (See timer_update_svn_status)"""
    svn = context.scene.svn

    svn.remove_unversioned_files()

    for filepath, status_info in file_statuses.items():
        wc_status, repos_status, revision = status_info

        tup_existing_file = svn.get_file_by_svn_path(filepath)
        if tup_existing_file:
            file_entry = tup_existing_file[1]
        else:
            file_entry = svn.external_files.add()
            file_entry['svn_path'] = filepath
            file_entry['name'] = Path(filepath).name

        file_entry['revision'] = revision
        file_entry.status = wc_status
        file_entry.repos_status = repos_status

    current_blend = svn.current_blend_file
    if current_blend:
        current_blend.is_referenced = True

    svn.force_good_active_index(context)
    # print("SVN: File statuses updated.")


@bpy.app.handlers.persistent
def update_file_is_referenced_flags(_dummy1, _dummy2):
    """Update the file list's is_referenced flags. This should only be called on
    file save, because it relies on BAT, which relies on reading a file from disk,
    so calling it any more frequently would be pointless."""
    context = bpy.context
    svn = context.scene.svn
    referenced_files: Set[Path] = set()#svn.get_referenced_filepaths()
    referenced_files.add(Path(bpy.data.filepath))
    referenced_files = [str(svn.absolute_to_svn_path(f)) for f in referenced_files]

    for file_entry in svn.external_files:
        file_entry.is_referenced = file_entry.svn_path in referenced_files


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
def svn_status_background_fetch_start(_dummy1, _dummy2):
    if not bpy.app.timers.is_registered(timer_update_svn_status):
        bpy.app.timers.register(timer_update_svn_status, persistent=True)


def svn_status_background_fetch_stop():
    if bpy.app.timers.is_registered(timer_update_svn_status):
        bpy.app.timers.unregister(timer_update_svn_status)
    global SVN_STATUS_POPEN
    SVN_STATUS_POPEN = None


################################################################################
############################# REGISTER #########################################
################################################################################

def register():
    bpy.app.handlers.load_post.append(init_svn)
    bpy.app.handlers.load_post.append(svn_status_background_fetch_start)

    bpy.app.handlers.load_post.append(update_file_is_referenced_flags)
    bpy.app.handlers.save_post.append(update_file_is_referenced_flags)

def unregister():
    bpy.app.handlers.load_post.remove(init_svn)
    bpy.app.handlers.load_post.remove(svn_status_background_fetch_start)

    bpy.app.handlers.load_post.remove(update_file_is_referenced_flags)
    bpy.app.handlers.save_post.remove(update_file_is_referenced_flags)

registry = [SVN_explain_status]
