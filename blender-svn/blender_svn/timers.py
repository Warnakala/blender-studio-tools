import bpy
from pathlib import Path
import subprocess

from .ops import execute_svn_command_nofreeze
from .util import get_addon_prefs

SVN_LOG_POPEN = None


def is_log_up_to_date(context) -> bool:
    """Return whether the latest SVN Log entry loaded in storage is at least
    as recent as the latest commit in the working copy."""
    svn = context.scene.svn
    prefs = get_addon_prefs(context)
    current_rev = prefs.revision_number
    latest_log_rev = 0
    if len(svn.log) > 0:
        latest_log_rev = svn.log[-1].revision_number

    return latest_log_rev >= current_rev


def get_subprocess_output(popen: subprocess.Popen) -> str:
    """Return the output of a subprocess if it's finished."""
    if popen.poll() is not None:
        stdout_data, _stderr_data = popen.communicate()
        return stdout_data.decode()


def write_to_svn_log_file_and_storage(context, data_str: str):
    prefs = get_addon_prefs(context)
    svn = context.scene.svn
    log_file_path = Path(prefs.svn_directory+"/.svn/svn.log")

    file_existed = False
    if log_file_path.exists():
        file_existed = True
        svn.update_log_from_file(log_file_path)

    with open(log_file_path, 'a+') as f:
        # Append to the file, create it if necessary.
        if file_existed:
            # We want to skip the first line of the svn log when continuing,
            # to avoid duplicate dashed lines, which would also mess up our
            # parsing logic.
            data_str = data_str[73:] # 72 dashes and a newline

        f.write(data_str)

    svn.update_log_from_file(log_file_path)

    print(f"SVN Log now at r{context.scene.svn.log[-1].revision_number}")


@bpy.app.handlers.persistent
def timer_update_svn_log():
    REVISIONS_PER_SUBPROCESS = 10
    global SVN_LOG_POPEN
    context = bpy.context
    svn = context.scene.svn
    prefs = get_addon_prefs(context)

    if not prefs.is_in_repo:
        return

    if not prefs.log_update_in_background:
        svn_log_background_fetch_stop()
        return

    if is_log_up_to_date(context):
        print("SVN Log is up to date with current revision.")
        svn_log_background_fetch_stop()
        return

    if SVN_LOG_POPEN:
        output = get_subprocess_output(SVN_LOG_POPEN)
        if not output:
            # Process is still running, so we just gotta wait. Let's try again in 3 seconds.
            return 3.0
        write_to_svn_log_file_and_storage(context, output)

    latest_log_rev = 0
    if len(svn.log) > 0:
        latest_log_rev = svn.log[-1].revision_number

    current_rev = prefs.revision_number
    # Start a sub-process.
    num_logs_to_get = current_rev - latest_log_rev
    if num_logs_to_get > REVISIONS_PER_SUBPROCESS:
        num_logs_to_get = REVISIONS_PER_SUBPROCESS

    goal_rev = latest_log_rev + num_logs_to_get
    SVN_LOG_POPEN = execute_svn_command_nofreeze(prefs.svn_directory, f"svn log --verbose -r {latest_log_rev+1}:{goal_rev}")

    return 3.0

@bpy.app.handlers.persistent
def svn_log_background_fetch_start(_dummy1, _dummy2):
    bpy.app.timers.register(timer_update_svn_log, persistent=True)

def svn_log_background_fetch_stop():
    if bpy.app.timers.is_registered(timer_update_svn_log):
        bpy.app.timers.unregister(timer_update_svn_log)
    global SVN_LOG_POPEN
    SVN_LOG_POPEN = None

def register():
    bpy.app.handlers.load_post.append(svn_log_background_fetch_start)

def unregister():
    bpy.app.handlers.load_post.remove(svn_log_background_fetch_start)
    svn_log_background_fetch_stop()