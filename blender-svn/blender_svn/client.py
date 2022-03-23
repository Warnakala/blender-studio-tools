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

import bpy
from bpy.app.handlers import load_post, persistent

import logging

from . import wheels
# This will load the dateutil and svn wheel file.
wheels.preload_dependencies()

from svn.local import LocalClient

from typing import List, Dict, Union, Any, Set, Optional, Tuple
from pathlib import Path

from .util import get_addon_prefs

logger = logging.getLogger("SVN")

LOCAL_CLIENT: LocalClient = None

@persistent
def init_local_client(context, dummy):
    """Attempt to initialize an SVN LocalClient object when opening a .blend file."""
    global LOCAL_CLIENT

    if not bpy.data.filepath:
        return

    LOCAL_CLIENT = LocalClient(bpy.data.filepath)
    # TODO: What happens when the file is not in an SVN repository directory? We should catch that case, reset the prefs, and early exit!
    logger.info("SVN client done: %s", LOCAL_CLIENT)
    prefs = get_addon_prefs(context)

    try:
        info = LOCAL_CLIENT.info()

        # Populate the addon prefs with the info provided by the LocalClient object.
        prefs.is_in_repo = True
        prefs.svn_url = info['repository_root']
        prefs.svn_directory = info['wc-info/wcroot-abspath']
        prefs.relative_filepath = info['relative_url'][1:]
        prefs.revision_number = int(info['entry_revision'])
        prefs.revision_date = str(info['commit_date']) # TODO: format this nicely.
        prefs.revision_author = info['commit_author']
    except Exception:
        # TODO: Would be nice to have a better way to determine if the current 
        # file is NOT in a repository...
        prefs.reset()


def register():
    load_post.append(init_local_client)

def unregister():
    load_post.remove(init_local_client)