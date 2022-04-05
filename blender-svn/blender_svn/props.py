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

from collections import OrderedDict
from pathlib import Path

from blender_svn.util import get_addon_prefs

import bpy, logging
from bpy.props import BoolProperty

from . import client, prefs
from .svn_log import SVN_log, SVN_file

from blender_asset_tracer import trace

logger = logging.getLogger("SVN")


class SVN_scene_properties(bpy.types.PropertyGroup):
    """Scene Properties for SVN"""

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
        if not bpy.data.filepath:
            return set()

        bpath = Path(bpy.data.filepath)
        assert bpath.is_file(), f"{bpy.data.filepath!r} is not a file"

        reported_assets: Set[Path] = set()

        for usage in trace.deps(bpath):
            for assetpath in usage.files():
                if assetpath in reported_assets:
                    logger.debug("Already reported %s", assetpath)
                    continue

                reported_assets.add(assetpath)

        return reported_assets

    def update_outdated_file_entries(self):
        """Update all files with the 'none' status, which signified that a file 
        had a newer version available on the remote repository.
        Running this function means that this file's up-to-date-ness has been 
        ensured, and this function is just to indicate this in the UI."""
        for i, file_entry in reversed(list(enumerate(self.external_files))):
            if file_entry.status == "none":
                file_entry.status = 'normal'
                file_entry.revision = self.get_latest_revision_of_file(file_entry.svn_path)

    def remove_by_svn_path(self, path_to_remove: str):
        """Remove a file entry from the file list, based on its filepath."""
        for i, file_entry in enumerate(self.external_files):
            filepath = file_entry.svn_path
            if filepath == path_to_remove:
                self.external_files.remove(i)
                return

    def check_for_local_changes(self) -> None:
        """Update the status of file entries by checking for changes in the
        local repository."""

        context = bpy.context

        local_client = client.get_local_client()
        if not local_client:
            return

        # Remove unversioned files from the list. The ones that are still around
        #  will be re-discovered below, through local_client.status().
        for i, file_entry in reversed(list(enumerate(self.external_files))):
            if file_entry.status == "unversioned":
                self.external_files.remove(i)

        referenced_files: Set[Path] = self.get_referenced_filepaths()
        referenced_files.add(Path(bpy.data.filepath))

        # Calls `svn status` to get a list of files that have been added, modified, etc.
        # Match each file name with a tuple that is the modification type and revision number.
        file_statuses = {
            s.name: (s.type_raw_name, s.revision) for s in local_client.status()
        }

        # Add file entries that are referenced by this .blend file,
        # even if the file's status is normal (un-modified)
        for referenced_file in referenced_files:
            status = (
                "normal",
                0,
            )  # TODO: We currently don't show a revision number for Normal status files!
            if str(referenced_file) in file_statuses:
                status = file_statuses[str(referenced_file)]
                del file_statuses[str(referenced_file)]
            file_entry = self.add_file_entry(self.absolute_to_svn_path(referenced_file), status[0], status[1], is_referenced=True)

        # Add file entries in the entire SVN repository for files whose status isn't
        # normal. Do this even for files not referenced by this .blend file.
        for f in file_statuses.keys():
            status = file_statuses[f]
            file_entry = self.add_file_entry(self.absolute_to_svn_path(f), status[0], status[1])
        
        prefs.force_good_active_index(context)

    @staticmethod
    def absolute_to_svn_path(absolute_path: Path) -> Path:
        if type(absolute_path) == str:
            absolute_path = Path(absolute_path)
        prefs = get_addon_prefs(bpy.context)
        svn_dir = Path(prefs.svn_directory)
        return absolute_path.relative_to(svn_dir)

    def add_file_entry(
        self, svn_path: Path, status: str, rev=0, is_referenced=False
    ) -> SVN_file:
        tup = self.get_file_by_svn_path(str(svn_path))
        if not tup:
            item = self.external_files.add()
        else:
            _idx, item = tup

        # Set collection property.
        item['svn_path'] = str(svn_path)
        item['name'] = svn_path.name

        item.status = status
        if rev==0:
            """SVN revisions start at 1, so 0 means it wasn't specified.
            Let's assume that the svn status is accurate. This means that in the
            case of a 'normal' status, we can just find the latest log that
            affected this file and put that log's as the revision number.
            """
            item['revision'] = self.get_latest_revision_of_file(svn_path)
        else:
            item['revision'] = rev

        # Prevent editing values in the UI.
        item['is_referenced'] = is_referenced
        return item

    def get_file_by_svn_path(self, svn_path: str) -> Tuple[int, SVN_file]:
        for i, file in enumerate(self.external_files):
            if file.svn_path == svn_path:
                return i, file

    external_files: bpy.props.CollectionProperty(type=SVN_file)  # type: ignore
    external_files_active_index: bpy.props.IntProperty()

    def get_log_by_revision(self, revision: int) -> Tuple[int, SVN_log]:
        for i, log in enumerate(self.log):
            if log.revision_number == revision:
                return i, log

    def get_latest_revision_of_file(self, svn_path: str) -> int:
        ret = 0
        for log in self.log:
            for changed_file in log.changed_files:
                if changed_file.svn_path == "/"+str(svn_path):
                    ret = log.revision_number
        return ret

    log: bpy.props.CollectionProperty(type=SVN_log)
    log_active_index: bpy.props.IntProperty()

    # Flags for the Fetch Log operator.
    log_update_in_progress: BoolProperty(default=False, description="This is set to True when an SVN log update process is running. Can be used for UI code checks and to avoid starting several SVN Log update process in parallel")
    log_update_cancel_flag: BoolProperty(default=False, description="Set this to True to request cancellation of the SVN log update process")

    @property
    def active_file(self):
        return self.external_files[self.external_files_active_index]

    @property
    def active_log(self):
        return self.log[self.log_active_index]


@bpy.app.handlers.persistent
def check_for_local_changes(scene):
    if not scene:
        # When called from save_post() handler, which apparently does not pass context
        scene = bpy.context.scene
    scene.svn.log_update_in_progress = False
    scene.svn.log_update_cancel_flag = False
    scene.svn.check_for_local_changes()


# ----------------REGISTER--------------.

registry = [SVN_scene_properties]

def register() -> None:
    # Scene Properties.
    bpy.types.Scene.svn = bpy.props.PointerProperty(type=SVN_scene_properties)
    bpy.app.handlers.load_post.append(check_for_local_changes)
    bpy.app.handlers.save_post.append(check_for_local_changes)


def unregister() -> None:
    del bpy.types.Scene.svn
    bpy.app.handlers.load_post.remove(check_for_local_changes)
    bpy.app.handlers.save_post.remove(check_for_local_changes)
