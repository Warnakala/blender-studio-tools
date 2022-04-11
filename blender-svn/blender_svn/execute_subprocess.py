import subprocess


def command_with_credential(prefs, command) -> str:
    username, password = prefs.get_credentials()
    assert (username and password), "No username and password entered for this repository. The UI shouldn't have allowed you to get into a state where you can press an SVN operation button without having your credentials entered, so this is a bug!"
    return command + f' --username "{username}" --password "{password}"'

def execute_command(path: str, command: str) -> str:
    try:
        return str(
            subprocess.check_output(
                (command), shell=True, cwd=path+"/", stderr=subprocess.PIPE
            ),
            'utf-8'
        )
    except subprocess.CalledProcessError as e:
        print(f"Command returned error: {command}")
        error = e.stderr.decode()
        print(error)
        return e

def execute_svn_command(prefs, command: str) -> str:
    """Execute an svn command in the root of the current svn repository.
    So any file paths that are part of the commend should be relative to the
    SVN root.
    """
    command = command_with_credential(prefs, command)
    output = execute_command(prefs.svn_directory, command)
    if type(output) == subprocess.CalledProcessError:
        cred = prefs.get_credential(get_entry=True)
        cred.svn_error = output
        return ""
    return output

def execute_svn_command_nofreeze(prefs, command: str) -> subprocess.Popen:
    """Execute an svn command in the root of the current svn repository using
    Popen(), which avoids freezing the Blender UI.
    """
    command = command_with_credential(prefs, command)
    svn_root_path = prefs.svn_directory
    return subprocess.Popen(
        (command), shell=True, cwd=svn_root_path+"/", stdout=subprocess.PIPE
    )

def subprocess_request_output(popen: subprocess.Popen) -> str:
    """Return the output of a subprocess if it's finished."""
    if popen.poll() is not None:
        stdout_data, stderr_data = popen.communicate()
        return stdout_data.decode()