# SPDX-License-Identifier: GPL-2.0-or-later
# (c) 2023, Blender Foundation - Demeter Dzadik
from typing import Optional, Any, Set, Tuple, List
from pathlib import Path
from datetime import datetime
from .threaded import svn_log

import bpy
from bpy.types import PropertyGroup
from bpy.props import StringProperty, BoolProperty, CollectionProperty, IntProperty, EnumProperty

from .threaded.background_process import Processes
from .util import make_getter_func, make_setter_func_readonly, svn_date_simple, get_addon_prefs
from . import constants

class SVN_file(bpy.types.PropertyGroup):
    """Property Group that can represent a version of a File in an SVN repository."""

    name: StringProperty(
        name="File Name",
        get=make_getter_func("name", ""),
        set=make_setter_func_readonly("name"),
        options=set()
    )

    svn_path: StringProperty(
        name="SVN Path",
        description="Filepath relative to the SVN root",
        options=set()
    )
    absolute_path: StringProperty(
        name="Absolute Path",
        description="Absolute filepath",
        options=set()
    )

    status: EnumProperty(
        name="Status",
        description="SVN Status of the file in the local repository (aka working copy)",
        items=constants.ENUM_SVN_STATUS,
        default="normal",
        options=set()
    )
    repos_status: EnumProperty(
        name="Remote's Status",
        description="SVN Status of the file in the remote repository (periodically updated)",
        items=constants.ENUM_SVN_STATUS,
        default="none",
        options=set()
    )
    status_prediction_type: EnumProperty(
        name="Status Predicted By Process",
        items=[
            ("NONE", "None", "File status is not predicted, but actual."),
            ("SVN_UP", "Update", "File status is predicted by `svn up`. Status is protected until process is finished."),
            ("SVN_COMMIT", "Commit", "File status is predicted by `svn commit`. Status is protected until process is finished."),
            ("SKIP_ONCE", "Skip Once", "File status is predicted by a working-copy svn file operation, like Revert. Next status update should be ignored, and this enum should be set to SKIPPED_ONCE."),
            ("SKIPPED_ONCE", "Skipped Once", "File status update was skipped. Next status update can be considered accurate, and this flag can be reset to NONE. Until then, operations on this file should remain disabled."),
        ],
        description="Internal flag that notes what process set a predicted status on this file. Should be empty string when the status is not predicted but confirmed. When svn commit/update predicts a status, that status should not be overwritten until the process is finished. With instantaneous processes, a single status update should be ignored since it may be outdated",
        options=set()
    )
    include_in_commit: BoolProperty(
        name="Commit",
        description="Whether this file should be included in the commit or not",
        default=False,
        options=set()
    )

    @property
    def absolute_path(self) -> Path:
        """Return absolute path on the file system."""
        scene = self.id_data
        svn = scene.svn
        return Path(svn.svn_directory).joinpath(Path(self.svn_path))

    @property
    def relative_path(self) -> str:
        """Return relative path with Blender's path conventions."""
        return bpy.path.relpath(self.absolute_path)

    @property
    def is_outdated(self):
        return self.repos_status == 'modified' and self.status == 'normal'

    revision: IntProperty(
        name="Revision",
        description="Revision number",
        options=set()
    )

    @property
    def exists(self) -> bool:
        return Path(self.absolute_path).exists()

    @property
    def status_icon(self) -> str:
        return constants.SVN_STATUS_DATA[self.status][0]

    @property
    def status_name(self) -> str:
        if self.status == 'none':
            return 'Outdated'
        return self.status.title()

    @property
    def file_icon(self) -> str:
        if '.' not in self.name:
            return 'FILE_FOLDER'
        extension = self.name.split(".")[-1] if "." in self.name else ""

        if extension in ['abc']:
            return 'FILE_CACHE'
        elif extension in ['blend', 'blend1']:
            return 'FILE_BLEND'
        elif extension in ['tga', 'bmp', 'tif', 'tiff', 'tga', 'png', 'dds', 'jpg', 'exr', 'hdr']:
            return 'TEXTURE'
        elif extension in ['psd', 'kra']:
            return 'IMAGE_DATA'
        elif extension in ['mp4', 'mov']:
            return 'SEQUENCE'
        elif extension in ['mp3', 'ogg', 'wav']:
            return 'SPEAKER'

        return 'QUESTION'


class SVN_log(bpy.types.PropertyGroup):
    """Property Group that can represent an SVN log entry."""

    revision_number: IntProperty(
        name="Revision Number",
        description="Revision number of the current .blend file",
    )
    revision_date: StringProperty(
        name="Revision Date",
        description="Date when the current revision was committed",
    )

    @property
    def revision_date_simple(self):
        return svn_date_simple(self.revision_date)

    revision_author: StringProperty(
        name="Revision Author",
        description="SVN username of the revision author",
    )
    commit_message: StringProperty(
        name="Commit Message",
        description="Commit message written by the commit author to describe the changes in this revision",
    )

    changed_files: CollectionProperty(
        type=SVN_file,
        name="Changed Files",
        description="List of file entries that were affected by this revision"
    )

    matches_filter: BoolProperty(
        name="Matches Filter",
        description="Whether the log entry matches the currently typed in search filter",
        default=True
    )

    def changed_file(self, svn_path: str) -> bool:
        for f in self.changed_files:
            if f.svn_path == "/"+svn_path:
                return True
        return False

    @property
    def text_to_search(self) -> str:
        """Return a string containing all searchable information about this log entry."""
        # TODO: For optimization's sake, this shouldn't be a @property, but instead
        # saved as a proper variable when the log entry is created.
        rev = "r"+str(self.revision_number)
        auth = self.revision_author
        files = " ".join([f.svn_path for f in self.changed_files])
        msg =  self.commit_message
        date = self.revision_date_simple
        return " ".join([rev, auth, files, msg, date]).lower()


class SVN_commit_line(PropertyGroup):
    """Property Group representing a single line of a commit message.
    Only needed for UI/UX purpose, so we can store the commit message
    even if the user changes their mind about wanting to commit."""

    def update_line(self, context):
        line_entries = context.scene.svn.get_repo(context).commit_lines
        for i, line_entry in enumerate(line_entries):
            if line_entry == self and i >= len(line_entries)-2:
                # The last line was just modified
                if self.line:
                    # Content was added to the last line - add another line.
                    line_entries.add()

    line: StringProperty(update=update_line)


class SVN_repository(PropertyGroup):
    ### Basic SVN Info. ###
    @property
    def name(self):
        return self.directory

    display_name: StringProperty(
        name="Display Name",
        description="Display name of this SVN repository"
    )

    url: StringProperty(
        name="URL",
        description="URL of the remote repository"
    )

    def update_directory(self, context):
        self['name'] = self.directory

    directory: StringProperty(
        name="Root Directory",
        default="",
        subtype="DIR_PATH",
        description="Absolute directory path of the SVN repository's root in the file system",
        update=update_directory
    )

    ### Credentials. ###
    def update_cred(self, context):
        if not (self.username and self.password):
            # Only try to authenticate if BOTH username AND pw are entered.
            return
        if get_addon_prefs(context).loading:
            return

        self.authenticate(context)

    def authenticate(self, context):
        self.auth_failed = False
        Processes.start('Authenticate')
        get_addon_prefs(context).save_repo_info_to_file()

    username: StringProperty(
        name="Username",
        description="User name used for authentication with this SVN repository",
        update=update_cred
    )
    password: StringProperty(
        name="Password",
        description="Password used for authentication with this SVN repository. This password is stored in your Blender user preferences as plain text. Somebody with access to your user preferences will be able to read your password",
        subtype='PASSWORD',
        update=update_cred
    )

    @property
    def is_cred_entered(self):
        """Check if there's a username and password entered at all."""
        return self.username and self.password

    authenticated: BoolProperty(
        name="Authenticated",
        description="Internal flag to mark whether the last entered credentials were confirmed by the repo as correct credentials",
        default=False
    )
    auth_failed: BoolProperty(
        name="Authentication Failed",
        description="Internal flag to mark whether the last entered credentials were denied by the repo",
        default=False
    )

    ### SVN Commit Message. ###
    commit_lines: CollectionProperty(type=SVN_commit_line)

    @property
    def commit_message(self):
        return "\n".join([l.line for l in self.commit_lines]).strip()

    @commit_message.setter
    def commit_message(self, msg: str):
        self.commit_lines.clear()
        for line in msg.split("\n"):
            line_entry = self.commit_lines.add()
            line_entry.line = line
        while len(self.commit_lines) < 3:
            self.commit_lines.add()

    ### SVN Log / Revision History. ###
    log: CollectionProperty(type=SVN_log)
    log_active_index: IntProperty(
        name="SVN Log",
        options=set()
    )
    log_active_index_filebrowser: IntProperty(
        name="SVN Log",
        options=set()
    )

    reload_svn_log = svn_log.reload_svn_log

    @property
    def log_file_path(self) -> Path:
        return Path(self.directory+"/.svn/svn.log")

    @property
    def active_log(self):
        try:
            return self.log[self.log_active_index]
        except IndexError:
            return None

    @property
    def active_log_filebrowser(self):
        try:
            return self.log[self.log_active_index_filebrowser]
        except IndexError:
            return None

    def get_log_by_revision(self, revision: int) -> Tuple[int, SVN_log]:
        for i, log in enumerate(self.log):
            if log.revision_number == revision:
                return i, log

    def get_latest_revision_of_file(self, svn_path: str) -> int:
        svn_path = str(svn_path)
        for log in reversed(self.log):
            for changed_file in log.changed_files:
                if changed_file.svn_path == "/"+str(svn_path):
                    return log.revision_number
        return 0

    def is_file_outdated(self, file: SVN_file) -> bool:
        """A file may have the 'modified' state while also being outdated.
        In this case SVN is of no use, we need to detect and handle this case
        by ourselves.
        """
        latest = self.get_latest_revision_of_file(file.svn_path)
        current = file.revision
        return latest > current


    ### SVN File List. ###
    external_files: bpy.props.CollectionProperty(type=SVN_file)  # type: ignore

    def remove_file_entry(self, file_entry: SVN_file):
        """Remove a file entry from the file list, based on its filepath."""
        for i, f in enumerate(self.external_files):
            if f == file_entry:
                self.external_files.remove(i)
                if i <= self.external_files_active_index:
                    self.external_files_active_index -= 1
                return

    def absolute_to_svn_path(self, absolute_path: Path) -> Path:
        if type(absolute_path) == str:
            absolute_path = Path(absolute_path)
        svn_dir = Path(self.directory)
        return absolute_path.relative_to(svn_dir)

    def svn_to_absolute_path(self, svn_path: Path) -> Path:
        if type(svn_path) == str:
            svn_path = Path(svn_path)
        svn_dir = Path(self.directory)
        return svn_dir / svn_path

    def get_file_by_svn_path(self, svn_path: str or Path) -> Optional[SVN_file]:
        if isinstance(svn_path, Path):
            # We must use isinstance() instead of type() because apparently
            # the Path() constructor returns a WindowsPath object on Windows.
            svn_path = str(svn_path.as_posix())

        for file in self.external_files:
            if file.svn_path == svn_path:
                return file

    def get_file_by_absolute_path(self, abs_path: str or Path) -> Optional[SVN_file]:
        if isinstance(abs_path, Path):
            # We must use isinstance() instead of type() because apparently
            # the Path() constructor returns a WindowsPath object on Windows.
            abs_path = str(abs_path.as_posix())
        else:
            abs_path = str(Path(abs_path).as_posix())

        for file in self.external_files:
            if file.absolute_path == abs_path:
                return file

    def get_index_of_file(self, file_entry) -> Optional[int]:
        for i, file in enumerate(self.external_files):
            if file == file_entry:
                return i

    def update_active_file(self, context):
        """When user clicks on a different file, the latest log entry of that file
        should become the active log entry."""

        latest_idx = self.get_latest_revision_of_file(
            self.active_file.svn_path)
        # SVN Revisions are not 0-indexed, so we need to subtract 1.
        self.log_active_index = latest_idx-1

        space = context.space_data
        if space and space.type == 'FILE_BROWSER':
            # Set the active file in the file browser to whatever was selected in the SVN Files panel.
            self.log_active_index_filebrowser = latest_idx-1

            space.params.directory = self.active_file.absolute_path.parent.as_posix().encode()
            space.params.filename = self.active_file.name.encode()

            space.deselect_all()
            space.activate_file_by_relative_path(
                relative_path=self.active_file.name)
            Processes.start('Activate File')

    external_files_active_index: bpy.props.IntProperty(
        name="File List",
        description="Files tracked by SVN",
        update=update_active_file,
        options=set()
    )

    @property
    def active_file(self) -> SVN_file:
        return self.external_files[self.external_files_active_index]

    def is_filebrowser_directory_in_repo(self, context) -> bool:
        assert context.space_data.type == 'FILE_BROWSER', "This function needs a File Browser context."

        params = context.space_data.params
        abs_path = Path(params.directory.decode())

        if not abs_path.exists():
            return False

        return Path(self.directory) in [abs_path] + list(abs_path.parents)

    def get_filebrowser_active_file(self, context) -> SVN_file:
        assert context.space_data.type == 'FILE_BROWSER', "This function needs a File Browser context."

        params = context.space_data.params
        abs_path = Path(params.directory.decode()) / Path(params.filename)

        if not abs_path.exists():
            return

        if Path(self.directory) not in abs_path.parents:
            return False

        svn_path = self.absolute_to_svn_path(abs_path)
        svn_file = self.get_file_by_svn_path(svn_path)

        return svn_file

    @property
    def current_blend_file(self) -> SVN_file:
        return self.get_file_by_absolute_path(bpy.data.filepath)

    ### SVN File List Status Updating ##########################################

    timestamp_last_status_update: StringProperty(
        name="Last Status Update",
        description="Timestamp of when the last successful file status update was completed"
    )

    @property
    def seconds_since_last_update(self):
        if not self.timestamp_last_status_update:
            return 1000
        last_update_time = datetime.strptime(
            self.timestamp_last_status_update, "%Y/%m/%d %H:%M:%S")
        current_time = datetime.now()
        delta = current_time - last_update_time
        return delta.seconds


registry = [
    SVN_file,
    SVN_log,
    SVN_commit_line,
    SVN_repository,
]