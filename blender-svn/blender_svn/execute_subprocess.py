import subprocess
from .util import get_addon_prefs

def command_with_credential(context, command) -> str:
    prefs = get_addon_prefs(context)
    cred = prefs.get_credentials()
    assert (cred.username and cred.password), "No username and password entered for this repository. The UI shouldn't have allowed you to get into a state where you can press an SVN operation button without having your credentials entered, so this is a bug!"
    return command + f' --username "{cred.username}" --password "{cred.password}"'

def execute_command(path: str, command: str) -> str:
    output_bytes = subprocess.check_output(
        (command), shell=True, cwd=path+"/", stderr=subprocess.PIPE, start_new_session=True
    )
    
    return output_bytes.decode(encoding='utf-8', errors='replace')

def execute_svn_command(context, command: str, suppress_errors=False, print_errors=True, use_cred=False) -> str:
    """Execute an svn command in the root of the current svn repository.
    So any file paths that are part of the command should be relative to the
    SVN root.
    """
    svn = context.scene.svn
    svn.svn_error = ""
    if use_cred:
        command = command_with_credential(context, command)

    command += " --non-interactive"

    try:
        return execute_command(svn.svn_directory, command)
    except subprocess.CalledProcessError as error:
        if suppress_errors:
            return ""
        else:
            # svn.svn_error = error.stderr.decode()     TODO: This error storage should be implemented on a per process basis, not a single error for the entire SVN add-on.
            err_msg = error.stderr.decode()
            if print_errors:
                print(f"Command returned error: {command}")
                print(err_msg)
            raise error