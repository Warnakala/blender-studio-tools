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

import logging

from typing import List, Dict, Union, Any, Set, Optional, Tuple
from pathlib import Path

import bpy

from . import client
from .props import SVN_file

import functools
from blender_asset_tracer import cli, trace, bpathlib

logger = logging.getLogger("SVN")

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


def add_file_entry(scene: bpy.types.Scene, path: Path, status: Tuple[str, int]) -> SVN_file:

    # Add item.
    item = scene.svn.external_files.add()

    # Set collection property.
    item.path_str = path.as_posix()
    item.name = path.name

    if status:
        item.status = status[0]
        if status[1]:
            item.revision = status[1]

    # Prevent editing values in the UI.
    item.lock = True
    return item

@bpy.app.handlers.persistent
def refresh_file_list(scene) -> None:
    if not scene:
        # When called from save_post() handler, which apparently does not pass context
        scene = bpy.context.scene
    scene.svn.external_files.clear()
    scene.svn.external_files_active_index = -1

    files: Set[Path] = get_referenced_filepaths()
    files.add(Path(bpy.data.filepath))

    local_client = client.get_local_client()

    # Calls `svn status` to get a list of files that have been added, modified, etc.
    # Match each file name with a tuple that is the modification type and revision number.
    statuses = {s.name : (s.type_raw_name, s.revision) for s in local_client.status()}

    # Add file entries that are referenced by this .blend file,
    # even if the file's status is normal (un-modified)
    for f in files:
        status = ('normal', 0) # TODO: We currently don't show a revision number for Normal status files!
        if str(f) in statuses:
            status = statuses[str(f)]
            del statuses[str(f)]
        file_entry = add_file_entry(scene, f, status)
        file_entry.is_referenced = True

    # Add file entries in the entire SVN repository for files whose status isn't
    # normal. Do this even for files not referenced by this .blend file.
    for f in statuses.keys():
        file_entry = add_file_entry(scene, Path(f), statuses[f])
        file_entry.is_referenced = False
