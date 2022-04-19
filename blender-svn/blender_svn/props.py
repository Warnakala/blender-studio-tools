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
# (c) 2021, Blender Foundation - Paul Golter
# (c) 2022, Blender Foundation - Demeter Dzadik

from typing import Optional, Dict, Any, List, Tuple, Set

from pathlib import Path
from datetime import datetime

import bpy, logging
from bpy.props import IntProperty, StringProperty, CollectionProperty, BoolProperty, EnumProperty

from . import wheels
# This will load the dateutil and svn wheel file.
wheels.preload_dependencies()
from blender_asset_tracer import trace

from .util import make_getter_func, make_setter_func_readonly
from .svn_log import reload_svn_log
from . import constants

logger = logging.getLogger("SVN")

################################################################################
############################# DATA TYPES #######################################
################################################################################

class SVN_file(bpy.types.PropertyGroup):
    """Property Group that can represent a version of a File in an SVN repository."""

    name: StringProperty(
        name="File Name",
        get=make_getter_func("name", ""),
        set=make_setter_func_readonly("name"),
    )
    svn_path: StringProperty(
        name = "SVN Path",
        description="Filepath relative to the SVN root",
        get=make_getter_func("svn_path", ""),
        set=make_setter_func_readonly("svn_path"),
    )
    status: EnumProperty(
        name="Status",
        description = "SVN Status of the file in the local repository (aka working copy)",
        items=constants.ENUM_SVN_STATUS,
        default="normal",
    )
    repos_status: EnumProperty(
        name="Remote's Status",
        description = "SVN Status of the file in the remote repository (periodically updated)",
        items=constants.ENUM_SVN_STATUS,
        default="none",
    )
    @property
    def is_outdated(self):
        return self.repos_status == 'modified' and self.status == 'normal'

    revision: IntProperty(
        name="Revision",
        description="Revision number",
    )
    is_referenced: BoolProperty(
        name="Is Referenced",
        description="True when this file is referenced by this .blend file either directly or indirectly. Flag used for list filtering",
        default=False,
    )

    @property
    def exists(self) -> bool:
        svn = self.id_data.svn
        svn_directory = Path(svn.svn_directory)
        full_path = svn_directory.joinpath(Path(self.svn_path))
        return full_path.exists()

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
    revision_author: StringProperty(
        name="Revision Author",
        description="SVN username of the revision author",
    )
    commit_message: StringProperty(
        name = "Commit Message",
        description="Commit message written by the commit author to describe the changes in this revision",
    )

    changed_files: CollectionProperty(
        type = SVN_file,
        name = "Changed Files",
        description = "List of file paths relative to the SVN root that were affected by this revision"
    )

    def changed_file(self, svn_path: str) -> bool:
        for f in self.changed_files:
            if f.svn_path == "/"+svn_path:
                return True
        return False


class SVN_scene_properties(bpy.types.PropertyGroup):
    """Subversion properties and functions"""


    ### Basic SVN Info #########################################################

    is_in_repo: BoolProperty(
        name="is_in_repo",
        default=False,
        description="Internal flag marking whether the current file was deemed to be in an SVN repository on file save/load"
    )
    svn_directory: StringProperty(
        name="Root Directory",
        default="",
        subtype="DIR_PATH",
        description="Absolute directory path of the SVN repository's root in the file system",
    )
    svn_url: StringProperty(
        name="Remote URL",
        default="",
        description="URL of the remote SVN repository",
    )
    svn_error: StringProperty(
        name="Error Message",
        default="",
        description="If SVN throws an error other than authentication error, store it here",
    )

    def reset_info(self):
        """Reset SVN repository information."""
        self.svn_directory = ""
        self.svn_url = ""
        self.is_in_repo = False


    ### Blender Asset Tracer  Integration ######################################

    @staticmethod
    def get_referenced_filepaths() -> Set[Path]:
        """Return a flat list of absolute filepaths of existing files referenced
        either directly or indirectly by this .blend file, as a flat list.

        This uses the Blender Asset Tracer, so we rely on that to catch everything;
        Images, video files, mesh sequence caches, blender libraries, etc.

        Deleted files are not handled here; They are grabbed with PySVN instead, 
        for the entire repository. The returned list also does not include the 
        currently opened .blend file itself.
        """

        # We want to suppress BAT's missing file warnings, since from the SVN
        # addon's perspective, they are not relevant.
        bat_logger = logging.getLogger('blender_asset_tracer.trace.result')
        bat_logger.setLevel(50)

        if not bpy.data.filepath:
            return set()

        bpath = Path(bpy.data.filepath)

        reported_assets: Set[Path] = set()
        if not bpath.exists():
            # Rare case: File was deleted from file system, but is still open.
            return reported_assets

        assert bpath.is_file(), f"{bpy.data.filepath!r} is not a file"

        for usage in trace.deps(bpath):
            for assetpath in usage.files():
                if assetpath in reported_assets:
                    logger.debug("Already reported %s", assetpath)
                    continue

                reported_assets.add(assetpath)

        bat_logger.setLevel(0)
        return reported_assets


    ### SVN File List ##########################################################

    def remove_by_svn_path(self, path_to_remove: str):
        """Remove a file entry from the file list, based on its filepath."""
        for i, file_entry in enumerate(self.external_files):
            if file_entry.svn_path == path_to_remove:
                self.external_files.remove(i)
                return

    def remove_unversioned_files(self) -> None:
        """Update the status of unversioned files in the local repository."""

        context = bpy.context
        svn = context.scene.svn

        if not svn.is_in_repo:
            return

        # Remove unversioned files from the list. The ones that are still around
        # will be re-discovered below, through get_repo_file_statuses.
        for i, file_entry in reversed(list(enumerate(self.external_files))):
            if file_entry.status == "unversioned":
                self.external_files.remove(i)

    def absolute_to_svn_path(self, absolute_path: Path) -> Path:
        if type(absolute_path) == str:
            absolute_path = Path(absolute_path)
        svn_dir = Path(self.svn_directory)
        return absolute_path.relative_to(svn_dir)

    def get_file_by_svn_path(self, svn_path: str or Path, get_index=False) -> Optional[Tuple[int, SVN_file]]:
        if isinstance(svn_path, Path):
            # We must use isinstance() instead of type() because apparently the Path() constructor
            # returns a WindowsPath object on Windows.
            svn_path = svn_path.as_posix()

        for i, file in enumerate(self.external_files):
            if file.svn_path == svn_path:
                if get_index:
                    return i
                return file

    external_files: bpy.props.CollectionProperty(type=SVN_file)  # type: ignore

    def update_active_file(self, context):
        """When user clicks on a different file, the latest log entry of that file
        should become the active log entry."""
        latest_idx = self.get_latest_revision_of_file(self.active_file.svn_path)
        # SVN Revisions are not 0-indexed, so we need to subtract 1.
        self.log_active_index = latest_idx-1
    external_files_active_index: bpy.props.IntProperty(
        update = update_active_file
    )

    @property
    def active_file(self):
        return self.external_files[self.external_files_active_index]

    @property
    def current_blend_file(self):
        return self.get_file_by_svn_path(self.absolute_to_svn_path(Path(bpy.data.filepath)))


    ### SVN File List UIList filter properties #################################
    # These are normally stored on the UIList, but then they cannot be accessed
    # from anywhere else, since template_list() does not return the UIList instance.
    # We need to be able to access them outside of drawing code, to be able to 
    # know which entries are visible and ensure that a filtered out entry can never 
    # be the active one.

    def get_visible_indicies(self, context) -> List[int]:
        flt_flags, _flt_neworder = bpy.types.SVN_UL_file_list.cls_filter_items(context, self, 'external_files')

        visible_indicies = [i for i, flag in enumerate(flt_flags) if flag != 0]
        return visible_indicies

    def force_good_active_index(self, context) -> bool:
        """
        We want to avoid having the active file entry be invisible due to filtering.
        If the active element is being filtered out, set the active element to 
        something that is visible.
        """
        visible_indicies = self.get_visible_indicies(context)
        if len(visible_indicies) == 0:
            self.external_files_active_index = 0
        elif self.external_files_active_index not in visible_indicies:
            self.external_files_active_index = visible_indicies[0]

    def update_filters(dummy, context):
        """Should run when any of the SVN file list search filters are changed."""
        context.scene.svn.force_good_active_index(context)

    include_normal: BoolProperty(
        name = "Show Normal Files",
        description = "Include files whose SVN status is Normal",
        default = False,
        update = update_filters
    )
    only_referenced_files: BoolProperty(
        name = "Only Referenced Files",
        description = "Only show modified files referenced by this .blend file, rather than the entire repository",
        default = False,
        update = update_filters
    )
    search_filter: StringProperty(
        name = "Search Filter",
        description = "Only show entries that contain this string",
        update = update_filters
    )


    ### SVN File List Status Updating ##########################################

    ignore_next_status_update: BoolProperty(
        name="Ignore Next Status Update",
        description="Internal flag that should be set to True by operators that set file statuses to a predicted state. This prevents them from being re-set by an ongoing svn status call that would be outdated after the operator has run",
        default=False
    )

    timestamp_last_status_update: StringProperty(
        name="Last Status Update",
        description="Timestamp of when the last successful file status update was completed"
    )

    @property
    def time_since_last_update(self) -> int:
        """Returns seconds passed since timestamp_last_status_update."""
        if not self.timestamp_last_status_update:
            return 1000
        last_update_time = datetime.strptime(self.timestamp_last_status_update, "%Y/%m/%d %H:%M:%S")
        current_time = datetime.now()
        delta = current_time - last_update_time
        return delta.seconds


    ### SVN Log / Revision History #############################################

    log: bpy.props.CollectionProperty(type=SVN_log)
    log_active_index: bpy.props.IntProperty()

    reload_svn_log = reload_svn_log

    @property
    def active_log(self):
        return self.log[self.log_active_index]

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



# ----------------REGISTER--------------.

registry = [
    SVN_file,
    SVN_log,
    SVN_scene_properties,
]

def register() -> None:
    # Scene Properties.
    bpy.types.Scene.svn = bpy.props.PointerProperty(type=SVN_scene_properties)


def unregister() -> None:
    del bpy.types.Scene.svn
