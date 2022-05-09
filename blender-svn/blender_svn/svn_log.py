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
import threading, subprocess

import bpy
from bpy.props import IntProperty, BoolProperty

from .util import get_addon_prefs, svn_date_simple
from . import constants
from .execute_subprocess import execute_svn_command


################################################################################
################################ UI / UX #######################################
################################################################################

def layout_log_split(layout):
    main = layout.split(factor=0.4)
    num_and_auth = main.row()
    date_and_msg = main.row()
    
    num_and_auth_split = num_and_auth.split(factor=0.3)
    num = num_and_auth_split.row()
    auth = num_and_auth_split.row()

    date_and_msg_split = date_and_msg.split(factor=0.3)
    date = date_and_msg_split.row()
    msg = date_and_msg_split.row()

    return num, auth, date, msg


class SVN_UL_log(bpy.types.UIList):
    show_all_logs: BoolProperty(
        name = 'Show All Logs',
        description = 'Show the complete SVN Log, instead of only entries that affected the currently selected file',
        default = False
    )

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        if self.layout_type != 'DEFAULT':
            raise NotImplemented

        svn = data
        log_entry = item

        num, auth, date, msg = layout_log_split(layout.row())

        active_file = svn.active_file
        num.label(text=str(log_entry.revision_number))
        if item.revision_number == active_file.revision:
            num.operator('svn.tooltip_log', text="", icon='LAYER_ACTIVE', emboss=False).log_rev=log_entry.revision_number
        elif log_entry.changed_file(active_file.svn_path):
            get_older = num.operator('svn.download_file_revision', text="", icon='IMPORT', emboss=False)
            get_older.revision = log_entry.revision_number
            get_older.file_rel_path = active_file.svn_path
        auth.label(text=log_entry.revision_author)
        date.label(text=log_entry.revision_date.split(" ")[0][5:])

        commit_msg = log_entry.commit_message
        commit_msg = commit_msg.split("\n")[0] if "\n" in commit_msg else commit_msg
        commit_msg = commit_msg[:50]+"..." if len(commit_msg) > 52 else commit_msg
        msg.alignment = 'LEFT'
        msg.operator("svn.display_commit_message", text=commit_msg, emboss=False).log_rev=log_entry.revision_number

    def filter_items(self, context, data, propname):
        """Custom filtering functionality:
        - Always sort by descending revision number
        - Allow searching for various criteria
        """
        svn = data
        log_entries = getattr(data, propname)

        # Start off with all entries flagged as visible.
        flt_flags = [self.bitflag_filter_item] * len(log_entries)
        # Always sort by descending revision number
        flt_neworder = sorted(range(len(log_entries)), key=lambda i: log_entries[i].revision_number)
        flt_neworder.reverse()

        active_file = svn.active_file

        if not self.show_all_logs:
            # Filter out log entries that did not affect the selected file.
            for idx, log_entry in enumerate(log_entries):
                for affected_file in log_entry.changed_files:
                    if affected_file.svn_path == "/"+active_file.svn_path:
                        # If the active file is one of the files affected by this log
                        # entry, break the for loop and skip the else block.
                        break
                else:
                    flt_flags[idx] = 0

        if self.filter_name:
            # Simple search:
            # Filter out log entries that don't match anything in the string search.
            for idx, log_entry in enumerate(log_entries):
                if self.filter_name not in " ".join(
                    [
                        "r"+str(log_entry.revision_number),
                        log_entry.revision_author,
                        " ".join([f.svn_path for f in log_entry.changed_files]),
                        log_entry.commit_message,
                    ]
                ):
                    flt_flags[idx] = 0

        return flt_flags, flt_neworder

    def draw_filter(self, context, layout):
        """Custom filtering UI.
        """
        main_row = layout.row()
        main_row.prop(self, 'filter_name', text="")
        main_row.prop(self, 'show_all_logs', text="", toggle=True, icon='ALIGN_JUSTIFY')


class VIEW3D_PT_svn_log(bpy.types.Panel):
    """Display the revision history of the selected file."""
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'SVN'
    bl_label = 'Revision History'
    bl_parent_id = "VIEW3D_PT_svn_files"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        svn = context.scene.svn
        any_visible = svn.get_visible_indicies(context)
        if not any_visible:
            return False
        active_file = context.scene.svn.active_file
        if active_file.status in ['unversioned', 'added']:
            return False
        
        if svn.time_since_last_update > 30:
            return False
        return True

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        if SVN_LOG_THREAD:
            layout.label(text="Recent log entries may be missing, updating in progress...", icon='ERROR')

        num, auth, date, msg = layout_log_split(layout.row())
        num.label(text="r#")
        auth.label(text="Author")
        date.label(text="Date")
        msg.label(text="Message")
        layout.template_list(
            "SVN_UL_log",
            "svn_log",
            context.scene.svn,
            "log",
            context.scene.svn,
            "log_active_index",
        )

        active_log = context.scene.svn.active_log
        layout.label(text=f"Files changed in revision `r{active_log.revision_number}`:")

        col = layout.column(align=True)
        row = col.row()
        split = row.split(factor=0.80)
        split.label(text="          Filepath")
        row = split.row()
        row.alignment='RIGHT'
        row.label(text="Action")
        for f in active_log.changed_files:
            row = col.row()
            split = row.split(factor=0.90)
            split.prop(f, 'svn_path', emboss=False, text="", icon=f.file_icon)
            row = split.row()
            row.alignment='RIGHT'
            row.operator('svn.explain_status', text="", icon=f.status_icon, emboss=False).status = f.status


def execute_tooltip_log(self, context):
    """Set the index on click, to act as if this operator button was 
    click-through in the UIList."""
    tup = context.scene.svn.get_log_by_revision(self.log_rev)
    if tup:
        context.scene.svn.log_active_index = tup[0]
    return {'FINISHED'}


class SVN_tooltip_log(bpy.types.Operator):
    bl_idname = "svn.tooltip_log"
    bl_label = "" # Don't want the first line of the tooltip on mouse hover.
    # bl_description = "An operator to be drawn in the log list, that can display a dynamic tooltip"
    bl_options = {'INTERNAL'}

    log_rev: IntProperty(
        description = "Revision number of the log entry to show in the tooltip"
    )

    @classmethod
    def description(cls, context, properties):
        return "This is the currently checked out version of the file"

    execute = execute_tooltip_log


class SVN_show_commit_message(bpy.types.Operator):
    bl_idname = "svn.display_commit_message"
    bl_label = "" # Don't want the first line of the tooltip on mouse hover.
    # bl_description = "Show the currently active commit, using a dynamic tooltip"
    bl_options = {'INTERNAL'}

    log_rev: IntProperty(
        description = "Revision number of the log entry to show in the tooltip"
    )

    @classmethod
    def description(cls, context, properties):
        log_entry = context.scene.svn.get_log_by_revision(properties.log_rev)[1]
        return log_entry.commit_message

    execute = execute_tooltip_log



################################################################################
################# AUTOMATICALLY KEEPING SVN LOG UP TO DATE #####################
################################################################################

def get_log_file_path(context) -> Path:
    return Path(context.scene.svn.svn_directory+"/.svn/svn.log")


def reload_svn_log(self, context):
    """Read the svn.log file (written by this addon) into the log entry list."""

    svn = self
    svn.log.clear()

    # Read file into lists of lines where each list is one log entry
    filepath = get_log_file_path(context)
    if not filepath.exists():
        # Nothing to read!
        return

    chunks = []
    with open(filepath, 'r') as f:
        next(f) # Skip the first line of dashes.
        chunk = []
        for line in f:
            line = line.replace("\n", "")
            if line == "-" * 72:
                # Line of dashes indicates the log entry is over.
                chunks.append(chunk)
                chunk = []
                continue
            if not line:
                # Ignore empty lines.
                continue
            chunk.append(line)

    previous_rev_number = 0
    for chunk in chunks:
        # Read the first line of the svn log containing revision number, author,
        # date and commit message length.
        r_number, r_author, r_date, r_msg_length = chunk[0].split(" | ")
        r_number = int(r_number[1:])
        if r_number != previous_rev_number+1:
            # print(f"SVN: Warning: Revision order seems wrong at r{r_number}")
            # TODO: Currently this can happen when multiple Blender instances are running and end up writing the same log entry to the .log file multiple times.
            # This is not very ideal!
            continue
        previous_rev_number = r_number

        r_msg_length = int(r_msg_length.split(" ")[0])

        log_entry = svn.log.add()
        log_entry.revision_number = r_number
        log_entry.revision_author = r_author

        log_entry.revision_date = svn_date_simple(r_date)

        # File change set is on line 3 until the commit message begins...
        file_change_lines = chunk[2:-(r_msg_length)]
        for line in file_change_lines:
            if not line:
                print(chunk)
            line = line.strip()
            status_char = line[0]
            file_path = line[2:]
            if ' (from ' in file_path:
                # If the file was moved, let's just ignore that information for now.
                # TODO: This can be improved later if neccessary.
                file_path = file_path.split(" (from ")[0]

            log_file_entry = log_entry.changed_files.add()
            log_file_entry['name'] = Path(file_path).name
            log_file_entry['svn_path'] = Path(file_path).as_posix()
            log_file_entry.revision = r_number
            log_file_entry.status = constants.SVN_STATUS_CHAR[status_char]

        log_entry['commit_message'] = "\n".join(chunk[-r_msg_length:])


def write_to_svn_log_file_and_storage(context, data_str: str) -> int:
    """Return how many SVN log entries were contained in data_str."""
    svn = context.scene.svn
    log_file_path = get_log_file_path(context)

    file_existed = False
    if log_file_path.exists():
        file_existed = True
        svn.reload_svn_log(context)
    num_entries = len(svn.log)

    with open(log_file_path, 'a+') as f:
        # Append to the file, create it if necessary.
        if file_existed:
            # We want to skip the first line of the svn log when continuing,
            # to avoid duplicate dashed lines, which would also mess up our
            # parsing logic.
            data_str = data_str[73:] # 72 dashes and a newline
            data_str = "\n" + data_str # TODO: This is untested on windows.

        # On Windows, the `svn log` command outputs lines with all sorts of \r and \n shennanigans.
        # TODO: For this reason, this should be implemented with the --xml arg.
        data_str = data_str.replace("\r", "")
        if data_str.endswith("\n"):
            data_str = data_str[:-1]
        f.write(data_str)

    svn.reload_svn_log(context)

    print(f"SVN Log now at r{context.scene.svn.log[-1].revision_number}")
    return len(svn.log) - num_entries

SVN_LOG_THREAD = None
SVN_LOG_OUTPUT = ""
def async_get_svn_log():
    """This function should be executed from a separate thread to avoid freezing 
    Blender's UI during execute_svn_command().
    """
    global SVN_LOG_OUTPUT
    SVN_LOG_OUTPUT = ""

    context = bpy.context
    svn = context.scene.svn

    latest_log_rev = 0
    if len(svn.log) > 0:
        latest_log_rev = svn.log[-1].revision_number

    # We have no way to know if latest_log_rev+1 will exist or not, but we 
    # must check, and there is no safe way to check it, so we let's just 
    # catch and handle the potential error.
    SVN_LOG_OUTPUT = execute_svn_command(
        context,
        f"svn log {svn.svn_url} --verbose -r{latest_log_rev+1}:HEAD --limit 10", 
        suppress_errors=True,
        use_cred = True
    )
    if SVN_LOG_OUTPUT == "":
        print("SVN: Log is now fully up to date.")
        svn_log_background_fetch_stop()


@bpy.app.handlers.persistent
def timer_update_svn_log():
    """Get all SVN Log entries from the remote repo in the background,
    without freezing up the UI, by calling this function every 3 seconds.
    These are then stored in a file, so each log entry only needs to be fetched
    once per computer that runs the addon.
    """
    global SVN_LOG_THREAD
    global SVN_LOG_OUTPUT
    context = bpy.context
    svn = context.scene.svn
    prefs = get_addon_prefs(context)
    cred = prefs.get_credentials()

    if not svn.is_in_repo or not cred.authenticated:
        return

    if SVN_LOG_THREAD and SVN_LOG_THREAD.is_alive():
        # Process is still running, so we just gotta wait. Let's try again in 3 seconds.
        return 3.0
    elif SVN_LOG_OUTPUT:
        num_logs = write_to_svn_log_file_and_storage(context, SVN_LOG_OUTPUT)
        SVN_LOG_OUTPUT = ""
        SVN_LOG_THREAD = None
        if num_logs < 10:
            svn_log_background_fetch_stop()
            return

    SVN_LOG_THREAD = threading.Thread(target=async_get_svn_log, args=())
    SVN_LOG_THREAD.start()
    return 3.0


@bpy.app.handlers.persistent
def svn_log_handler(_dummy1, _dummy2):
    # This damn thing needs 2 positional arguments even though neither of them get anything!
    svn_log_background_fetch_start()


def svn_log_background_fetch_start(_dummy1=None, _dummy2=None):
    if not bpy.app.timers.is_registered(timer_update_svn_log):
        print("Updating SVN Log...")
        bpy.app.timers.register(timer_update_svn_log, persistent=True)


def svn_log_background_fetch_stop(_dummy1=None, _dummy2=None):
    if bpy.app.timers.is_registered(timer_update_svn_log):
        bpy.app.timers.unregister(timer_update_svn_log)
    global SVN_LOG_THREAD
    SVN_LOG_THREAD = None


################################################################################
############################### REGISTER #######################################
################################################################################

registry = [
    VIEW3D_PT_svn_log, 
    SVN_UL_log, 
    SVN_tooltip_log, 
    SVN_show_commit_message
]

def register():
    bpy.app.handlers.load_post.append(svn_log_handler)
    svn_log_background_fetch_start()
    
def unregister():
    bpy.app.handlers.load_post.remove(svn_log_handler)
    svn_log_background_fetch_stop()
