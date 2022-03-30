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
from urllib.parse import unquote

from .util import get_addon_prefs

logger = logging.getLogger("SVN")

LOCAL_CLIENT: LocalClient = None

def get_local_client():
    global LOCAL_CLIENT
    prefs = get_addon_prefs()
    if not LOCAL_CLIENT:
        LOCAL_CLIENT = LocalClient(prefs.svn_directory)

    return LOCAL_CLIENT

@persistent
def init_local_client(context, dummy):
    """Attempt to initialize an SVN LocalClient object when opening a .blend file."""
    global LOCAL_CLIENT

    if not bpy.data.filepath:
        return

    file_client = LocalClient(bpy.data.filepath)
    logger.info("SVN client done: %s", LOCAL_CLIENT)
    prefs = get_addon_prefs(context)

    try:
        info = file_client.info()

        # Populate the addon prefs with the info provided by the LocalClient object.
        prefs.is_in_repo = True
        prefs['svn_url'] = info['repository_root']
        prefs['svn_directory'] = unquote(info['wc-info/wcroot-abspath'])
        LOCAL_CLIENT = LocalClient(prefs.svn_directory)
        prefs['relative_filepath'] = unquote(info['relative_url'][1:])
        prefs['revision_number'] = int(info['entry_revision'])

        rev_datetime = info['commit_date']
        month_name = rev_datetime.strftime("%b")
        date_str = f"{rev_datetime.year}-{month_name}-{rev_datetime.day}"
        time_str = f"{str(rev_datetime.hour).zfill(2)}:{str(rev_datetime.minute).zfill(2)}"

        prefs['revision_date'] = date_str + " " + time_str
        prefs['revision_author'] = info['commit_author']
    except Exception:
        # TODO: Would be nice to have a better way to determine if the current 
        # file is NOT in a repository...
        prefs.reset()

def register():
    load_post.append(init_local_client)

def unregister():
    load_post.remove(init_local_client)