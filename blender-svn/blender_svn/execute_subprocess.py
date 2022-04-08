import subprocess

def execute_svn_command(svn_root_path: str, command: str) -> str:
    """Execute an svn command in the root of the current svn repository.
    So any file paths that are part of the commend should be relative to the
    SVN root.
    """
    return str(
        subprocess.check_output(
            (command), shell=True, cwd=svn_root_path+"/"
        ),
        'utf-8'
    )

def execute_svn_command_nofreeze(svn_root_path: str, command: str) -> subprocess.Popen:
    """Execute an svn command in the root of the current svn repository using
    Popen(), which avoids freezing the Blender UI.
    """
    return subprocess.Popen(
        (command), shell=True, cwd=svn_root_path+"/", stdout=subprocess.PIPE
    )

def subprocess_request_output(popen: subprocess.Popen) -> str:
    """Return the output of a subprocess if it's finished."""
    if popen.poll() is not None:
        stdout_data, stderr_data = popen.communicate()
        return stdout_data.decode()