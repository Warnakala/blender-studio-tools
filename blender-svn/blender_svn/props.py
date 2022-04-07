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

from blender_svn.util import get_addon_prefs

import bpy, logging

from . import wheels
# This will load the dateutil and svn wheel file.
wheels.preload_dependencies()

from .svn_log import SVN_log, SVN_file, reload_svn_log

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

    def remove_by_svn_path(self, path_to_remove: str):
        """Remove a file entry from the file list, based on its filepath."""
        for i, file_entry in enumerate(self.external_files):
            filepath = file_entry.svn_path
            if filepath == path_to_remove:
                self.external_files.remove(i)
                return

    def remove_unversioned_files(self) -> None:
        """Update the status of unversioned files in the local repository."""

        context = bpy.context
        addon_prefs = get_addon_prefs(context)

        if not addon_prefs.is_in_repo:
            return

        # Remove unversioned files from the list. The ones that are still around
        #  will be re-discovered below, through get_file_statuses.
        for i, file_entry in reversed(list(enumerate(self.external_files))):
            if file_entry.status == "unversioned":
                self.external_files.remove(i)

    @staticmethod
    def absolute_to_svn_path(absolute_path: Path) -> Path:
        if type(absolute_path) == str:
            absolute_path = Path(absolute_path)
        prefs = get_addon_prefs(bpy.context)
        svn_dir = Path(prefs.svn_directory)
        return absolute_path.relative_to(svn_dir)

    def add_file_entry(
        self, svn_path: Path, status: str, rev: int, is_referenced=False
    ) -> SVN_file:
        if svn_path.suffix.startswith(".r") and svn_path.suffix[2:].isdecimal():
            # Do not add .r### files to the file list, ever.
            return
        tup = self.get_file_by_svn_path(str(svn_path))
        existed = False
        if not tup:
            item = self.external_files.add()
        else:
            existed = True
            _idx, item = tup

        # Set collection property.
        item['svn_path'] = str(svn_path)
        item['name'] = svn_path.name

        assert rev > 0 or status in ['unversioned', 'added'], "Revision number of a versioned file must be greater than 0."
        item['revision'] = rev

        if rev < self.get_latest_revision_of_file(svn_path) and status == 'normal':
            # Strange case 1: We checked out an older version of a file.
            # SVN assigns this the 'normal' status instead of 'none'(Outdated)
            # which makes more sense from user POV.
            status = 'none'

        if not svn_path.is_file() and item.status == 'none' and status == 'normal':
            # Strange case 2: A previous `svn status --verbose --show-updates`
            # marked a folder as being outdated, but a subsequent `svn status --verbose`
            # reports the status of this folder as normal. In this case, it feels more
            # accurate to keep the folder on outdated.
            # TODO: Updating an outdated folder doesn't mark the outdated files as no longer being outdated. Maybe folders shouldn't even be displayed in the UIList, I don't even really get why svn marks the folder path as modified.
            status = 'none'

        item.status = status
        item.is_referenced = is_referenced
        return item

    def get_file_by_svn_path(self, svn_path: str) -> Tuple[int, SVN_file]:
        svn_path = str(svn_path)
        for i, file in enumerate(self.external_files):
            if file.svn_path == svn_path:
                return i, file


    def get_visible_indicies(self, context) -> List[int]:
        flt_flags, _flt_neworder = bpy.types.SVN_UL_file_list.cls_filter_items(context, self, 'external_files')

        visible_indicies = [i for i, flag in enumerate(flt_flags) if flag != 0]
        return visible_indicies

    def force_good_active_index(self, context) -> bool:
        """If the active element is being filtered out, set the active element to 
        something that is visible.
        Return False if no elements are visible.
        """
        visible_indicies = self.get_visible_indicies(context)
        if len(visible_indicies) == 0:
            self.external_files_active_index = 0
            return False
        if self.external_files_active_index not in visible_indicies:
            self.external_files_active_index = visible_indicies[0]

        return True

    external_files: bpy.props.CollectionProperty(type=SVN_file)  # type: ignore
    external_files_active_index: bpy.props.IntProperty()

    def get_log_by_revision(self, revision: int) -> Tuple[int, SVN_log]:
        for i, log in enumerate(self.log):
            if log.revision_number == revision:
                return i, log

    def get_latest_revision_of_file(self, svn_path: str) -> int:
        svn_path = str(svn_path)
        ret = 0
        for log in self.log:
            for changed_file in log.changed_files:
                if changed_file.svn_path == "/"+str(svn_path):
                    ret = log.revision_number
        return ret

    def is_file_outdated(self, file: SVN_file) -> bool:
        """A file may have the 'modified' state while also being outdated.
        In this case SVN is of no use, we need to detect and handle this case
        by ourselves.
        """
        latest = self.get_latest_revision_of_file(file.svn_path)
        current = file.revision
        return latest > current

    def file_exists(self, file: SVN_file) -> bool:
        context = bpy.context
        prefs = get_addon_prefs(context)
        svn_directory = Path(prefs.svn_directory)
        full_path = svn_directory.joinpath(Path(file.svn_path))
        return full_path.exists()

    reload_svn_log = reload_svn_log
    log: bpy.props.CollectionProperty(type=SVN_log)
    log_active_index: bpy.props.IntProperty()

    @property
    def active_file(self):
        return self.external_files[self.external_files_active_index]

    @property
    def active_log(self):
        return self.log[self.log_active_index]

    @property
    def current_blend_file(self):
        tup = self.get_file_by_svn_path(self.absolute_to_svn_path(Path(bpy.data.filepath)))
        if tup:
            return tup[1]


# ----------------REGISTER--------------.

registry = [SVN_scene_properties]

def register() -> None:
    # Scene Properties.
    bpy.types.Scene.svn = bpy.props.PointerProperty(type=SVN_scene_properties)


def unregister() -> None:
    del bpy.types.Scene.svn
