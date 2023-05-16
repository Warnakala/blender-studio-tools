# SPDX-License-Identifier: GPL-2.0-or-later
# (c) 2022, Blender Foundation - Demeter Dzadik

from pathlib import Path
import subprocess

from ..util import redraw_viewport
from .. import constants
from .execute_subprocess import execute_svn_command
from .background_process import BackgroundProcess


def reload_svn_log(self, context):
    """Read the svn.log file (written by this addon) into the log entry list."""

    repo = self
    repo.log.clear()

    # Read file into lists of lines where each list is one log entry
    filepath = self.log_file_path
    if not filepath.exists():
        # Nothing to read!
        return

    chunks = []
    with open(filepath, 'r') as f:
        next(f)  # Skip the first line of dashes.
        chunk = []
        for line in f:
            line = line.replace("\n", "")
            if line == "-" * 72:
                # Line of dashes indicates the log entry is over.
                chunks.append(chunk)
                chunk = []
                continue
            chunk.append(line)

    previous_rev_number = 0
    for chunk in chunks:
        if not chunk[0]:
            chunk.pop(0)
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

        log_entry = repo.log.add()
        log_entry.revision_number = r_number
        log_entry.revision_author = r_author

        log_entry.revision_date = r_date

        # File change set is on line 3 until the commit message begins...
        file_change_lines = chunk[2:-(r_msg_length+1)]
        for line in file_change_lines:
            line = line.strip()
            status_char = line[0]
            file_path = line[2:]
            if ' (from ' in file_path:
                # If the file was moved, let's just ignore that information for now.
                # TODO: This can be improved later if neccessary.
                file_path = file_path.split(" (from ")[0]

            file_path = Path(file_path)
            log_file_entry = log_entry.changed_files.add()
            log_file_entry.name = file_path.name
            log_file_entry.svn_path = str(file_path.as_posix())
            log_file_entry.absolute_path = str(repo.svn_to_absolute_path(file_path).as_posix())
            log_file_entry.revision = r_number
            log_file_entry.status = constants.SVN_STATUS_CHAR_TO_NAME[status_char]

        log_entry['commit_message'] = "\n".join(chunk[-r_msg_length:])


def write_to_svn_log_file_and_storage(context, data_str: str) -> int:
    """
    Get all SVN Log entries from the remote repo in the background,
    without freezing up the UI, by calling this function every 3 seconds.
    These are then stored in a file, so each log entry only needs to be fetched
    once per computer that runs the addon.

    Return how many SVN log entries were contained in data_str.
    """
    repo = context.scene.svn.get_repo(context)
    log_file_path = repo.log_file_path

    file_existed = False
    if log_file_path.exists():
        file_existed = True
        repo.reload_svn_log(context)
    num_entries = len(repo.log)

    with open(log_file_path, 'a+') as f:
        # Append to the file, create it if necessary.
        if file_existed:
            # We want to skip the first line of the svn log when continuing,
            # to avoid duplicate dashed lines, which would also mess up our
            # parsing logic.
            data_str = data_str[73:]  # 72 dashes and a newline
            data_str = "\n" + data_str  # TODO: This is untested on windows.

        # On Windows, the `svn log` command outputs lines with all sorts of \r and \n shennanigans.
        # TODO: For this reason, this should be implemented with the --xml arg.
        data_str = data_str.replace("\r", "")
        if data_str.endswith("\n"):
            data_str = data_str[:-1]
        f.write(data_str)

    repo.reload_svn_log(context)

    print(f"SVN Log now at r{repo.log[-1].revision_number}")
    return len(repo.log) - num_entries


class BGP_SVN_Log(BackgroundProcess):
    name = "Log"
    needs_authentication = True
    timeout = 10
    repeat_delay = 3
    debug = False

    def tick(self, context, prefs):
        redraw_viewport()

    def acquire_output(self, context, prefs):
        """This function should be executed from a separate thread to avoid freezing 
        Blender's UI during execute_svn_command().
        """
        repo = context.scene.svn.get_repo(context)

        latest_log_rev = 0
        if len(repo.log) > 0:
            latest_log_rev = repo.log[-1].revision_number

        self.debug_print("Acquire output...")

        # We have no way to know if latest_log_rev+1 will exist or not, but we
        # must check, and there is no safe way to check it, so let's just
        # catch and handle the potential error.
        try:
            self.output = execute_svn_command(
                context,
                ["svn", "log", "--verbose", f"-r{latest_log_rev+1}:HEAD", "--limit", "10"],
                print_errors=False,
                use_cred=True
            )
            self.debug_print("Output: \n" + self.output)
        except subprocess.CalledProcessError as error:
            error_msg = error.stderr.decode()
            if "No such revision" in error_msg:
                print("SVN: Log is now fully up to date.")
                self.stop()
            else:
                self.error = error_msg

    def process_output(self, context, prefs):
        num_logs = write_to_svn_log_file_and_storage(context, self.output)
        if num_logs < 10:
            self.stop()

    def get_ui_message(self, context):
        try:
            rev_no = context.scene.svn.get_repo(context).log[-1].revision_number
            return f"Updating. Current: {rev_no}..."
        except IndexError:
            return ""
