import subprocess
from .util import get_addon_prefs

def command_with_credential(context, command) -> str:
    prefs = get_addon_prefs(context)
    cred = prefs.get_credentials()
    assert (cred.username and cred.password), "No username and password entered for this repository. The UI shouldn't have allowed you to get into a state where you can press an SVN operation button without having your credentials entered, so this is a bug!"
    return command + f' --username "{cred.username}" --password "{cred.password}"'

def execute_command(path: str, command: str) -> str:
    return str(
        subprocess.check_output(
            (command), shell=True, cwd=path+"/", stderr=subprocess.PIPE
        ),
        'utf-8'
    )

def execute_command_safe(path: str, command: str) -> str or subprocess.CalledProcessError:
    try:
        return execute_command(path, command)
    except subprocess.CalledProcessError as error:
        print(f"Command returned error: {command}")
        err_msg = error.stderr.decode()
        print(err_msg)
        return error

def execute_svn_command(context, command: str) -> str:
    """Execute an svn command in the root of the current svn repository.
    So any file paths that are part of the command should be relative to the
    SVN root.
    """
    svn = context.scene.svn
    svn.svn_error = ""
    command = command_with_credential(context, command)
    output = execute_command_safe(svn.svn_directory, command)
    if type(output) == subprocess.CalledProcessError:
        svn.svn_error = output.stderr.decode()
        return ""
    return output
