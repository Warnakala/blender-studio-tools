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

from typing import Optional, Dict, Any, List, Tuple, Set

from collections import OrderedDict
from pathlib import Path

import bpy, functools, logging
from bpy.props import StringProperty, EnumProperty, IntProperty, BoolProperty

from .util import get_addon_prefs, make_getter_func, make_setter_func_readonly
from . import client

from blender_asset_tracer import cli, trace, bpathlib

logger = logging.getLogger("SVN")

SVN_STATUS_DATA = OrderedDict(
    [
        (
            "added",
            (
                "ADD",
                "This file was added to the local repository, and will be added to the remote repository when committing",
            ),
        ),
        (
            "conflicted",
            (
                "ERROR",
                "This file was modified locally, and a newer version has appeared on the remote repository at the same time. To resolve the conflict, one of the changes must be discarded",
            ),
        ),
        (
            "deleted",
            (
                "TRASH",
                "This file was deleted locally, but still exists on the remote repository",
            ),
        ),
        (
            "external",
            (
                "EXTERNAL_DRIVE",
                "This file is present because of an externals definition",
            ),
        ),
        (
            "ignored",
            (
                "RADIOBUT_OFF",
                "This file is being ignored (e.g., with the svn:ignore property)",
            ),
        ),
        (
            "incomplete",
            (
                "FOLDER_REDIRECT",
                "A directory is incomplete (a checkout or update was interrupted)",
            ),
        ),
        ("merged", ("AUTOMERGE_ON", "TODO")),
        (
            "missing",
            (
                "FILE_HIDDEN",
                "This file is missing (e.g., you moved or deleted it without using svn)",
            ),
        ),
        (
            "modified",
            (
                "MODIFIER",
                "This file was modified locally, and can be pushed to the remote repository without a conflict",
            ),
        ),
        (
            "none",
            (
                "TIME",
                "There is a newer version of this file available on the remote repository. You should update it",
            ),
        ),
        (
            "normal",
            (
                "CHECKMARK",
                "This file is in the repository. There are no local modifications to commit",
            ),
        ),
        ("obstructed", ("ERROR", "Something has gone horribly wrong. Try svn cleanup")),
        (
            "replaced",
            (
                "FILE_REFRESH",
                "This file has been replaced in your local repository. This means the file was scheduled for deletion, and then a new file with the same name was scheduled for addition in its place",
            ),
        ),
        (
            "unversioned",
            (
                "FILE_NEW",
                "This file is new in file system, but not yet added to the local repository. It needs to be added before it can be committed to the remote repository",
            ),
        ),
    ]
)

# Based on PySVN/svn/constants.py/STATUS_TYPE_LOOKUP.
ENUM_SVN_STATUS = [
    (status, status.title(), SVN_STATUS_DATA[status][1], SVN_STATUS_DATA[status][0], i)
    for i, status in enumerate(SVN_STATUS_DATA.keys())
]


class SVN_file(bpy.types.PropertyGroup):
    """Property Group that can represent a version of a File in an SVN repository."""

    lock: BoolProperty(
        name="Lock Editing",
        description="Flag used to keep the properties read-only without graying them out in the UI. Purely for aesthetic purpose",
        default=False,
    )
    name: StringProperty(
        name="File Name",
        get=make_getter_func("name", ""),
        set=make_setter_func_readonly("name"),
    )
    path_str: StringProperty(
        name="Absolute Path",
        description="Absolute file path",
        subtype="FILE_PATH",
        get=make_getter_func("path_str", ""),
        set=make_setter_func_readonly("path_str"),
    )
    status: EnumProperty(
        name="Status",
        items=ENUM_SVN_STATUS,
        default="normal",
        get=make_getter_func("status", 10),
        set=make_setter_func_readonly("status"),
    )
    revision: IntProperty(
        name="Revision",
        description="Revision number",
        get=make_getter_func("revision", 0),
        set=make_setter_func_readonly("revision"),
    )
    is_referenced: BoolProperty(
        name="Is Referenced",
        description="True when this file is referenced by this .blend file either directly or indirectly. Flag used for list filtering",
        default=False,
    )

    @property
    def path(self) -> Optional[Path]:
        if not self.path_str:
            return None
        return Path(self.path_str)

    @property
    def status_icon(self) -> str:
        return SVN_STATUS_DATA[self.status][0]

    @property
    def status_name(self) -> str:
        if self.status == 'none':
            return 'Outdated'
        return self.status.title()

    @property
    def svn_relative_path(self) -> str:
        prefs = get_addon_prefs(bpy.context)
        return self.path_str.replace(prefs.svn_directory, "")[1:]


class SVN_scene_properties(bpy.types.PropertyGroup):
    """Scene Properties for SVN"""

    @staticmethod
    def get_referenced_filepaths() -> Set[Path]:
        """Return a flat list of absolute filepaths of existing files referenced
        either directly or indirectly by this .blend file, as a flat list.

        This uses the Blender Asset Tracer, so we rely on that to catch everything;
        Images, video files, mesh sequence caches, blender libraries, everything.

        Deleted files are not handled here; They are grabbed with PySVN instead, for the entire repository.
        The returned list also does not include the currently opened .blend file itself.
        """
        bpath = Path(bpy.data.filepath)

        reported_assets: Set[Path] = set()
        last_reported_bfile = None
        shorten = functools.partial(cli.common.shorten, Path.cwd())

        for usage in trace.deps(bpath):
            files = [f for f in usage.files()]

            # Path of the blend file that references this BlockUsage.
            blend_path = usage.block.bfile.filepath.absolute()
            # if blend_path != last_reported_bfile:
            # print(shorten(blend_path))

            last_reported_bfile = blend_path

            for assetpath in usage.files():
                # assetpath = bpathlib.make_absolute(assetpath)
                if assetpath in reported_assets:
                    logger.debug("Already reported %s", assetpath)
                    continue

                # print("   ", shorten(assetpath))
                reported_assets.add(assetpath)

        return reported_assets

    def remove_outdated_file_entries(self):
        """Remove all outdated files currently in the file list."""
        for i, file_entry in reversed(list(enumerate(self.external_files))):
            if file_entry.status == "none":
                self.external_files.remove(i)

    def remove_by_path(self, path_to_remove: str):
        """Remove a file entry from the file list, based on its filepath."""
        for i, file_entry in enumerate(self.external_files):
            filepath = file_entry.path_str
            if filepath == path_to_remove:
                self.external_files.remove(i)
                return

    def check_for_local_changes(self) -> None:
        """Update the status of file entries by checking for changes in the
        local repository."""

        # Remove all files from the list except the ones with the Outdated status.
        for i, file_entry in reversed(list(enumerate(self.external_files))):
            if file_entry.status != "none":
                self.external_files.remove(i)

        self.external_files_active_index = -1

        files: Set[Path] = self.get_referenced_filepaths()
        files.add(Path(bpy.data.filepath))

        local_client = client.get_local_client()

        # Calls `svn status` to get a list of files that have been added, modified, etc.
        # Match each file name with a tuple that is the modification type and revision number.
        statuses = {
            s.name: (s.type_raw_name, s.revision) for s in local_client.status()
        }

        # Add file entries that are referenced by this .blend file,
        # even if the file's status is normal (un-modified)
        for f in files:
            status = (
                "normal",
                0,
            )  # TODO: We currently don't show a revision number for Normal status files!
            if str(f) in statuses:
                status = statuses[str(f)]
                del statuses[str(f)]
            file_entry = self.add_file_entry(f, status, is_referenced=True)

        # Add file entries in the entire SVN repository for files whose status isn't
        # normal. Do this even for files not referenced by this .blend file.
        for f in statuses.keys():
            file_entry = self.add_file_entry(Path(f), statuses[f])

    def add_file_entry(
        self, path: Path, status: Tuple[str, int], is_referenced=False
    ) -> SVN_file:
        # Add item.
        item = self.external_files.add()

        # Set collection property.
        item.path_str = path.as_posix()
        item.name = path.name

        if status:
            item.status = status[0]
            if status[1]:
                item.revision = status[1]

        # Prevent editing values in the UI.
        item.lock = True
        item.is_referenced = is_referenced
        return item

    external_files: bpy.props.CollectionProperty(type=SVN_file)  # type: ignore
    external_files_active_index: bpy.props.IntProperty()


@bpy.app.handlers.persistent
def check_for_local_changes(scene):
    if not scene:
        # When called from save_post() handler, which apparently does not pass context
        scene = bpy.context.scene
    scene.svn.check_for_local_changes()


# ----------------REGISTER--------------.

registry = [SVN_file, SVN_scene_properties]

def register() -> None:
    # Scene Properties.
    bpy.types.Scene.svn = bpy.props.PointerProperty(type=SVN_scene_properties)
    bpy.app.handlers.load_post.append(check_for_local_changes)
    bpy.app.handlers.save_post.append(check_for_local_changes)


def unregister() -> None:
    del bpy.types.Scene.svn
    bpy.app.handlers.load_post.remove(check_for_local_changes)
    bpy.app.handlers.save_post.remove(check_for_local_changes)
