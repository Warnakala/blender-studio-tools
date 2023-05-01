
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
# (c) 2021, Blender Foundation

import argparse
import sys
import os
import importlib

from pathlib import Path

from blender_purge import app
from blender_purge.log import LoggerFactory

importlib.reload(app)
logger = LoggerFactory.getLogger()

# Command line arguments.
parser = argparse.ArgumentParser()
parser.add_argument(
    "path", help="Path to a file or folder on which to perform purge", type=str
)
parser.add_argument(
    "-R",
    "--recursive",
    help="If -R is provided in combination with a folder path will perform recursive purge",
    action="store_true",
)

parser.add_argument(
    "-N",
    "--nocommit",
    help="If -N is provided there will be no svn commit prompt with the purged files.",
    action="store_true",
)

parser.add_argument(
    "--regex",
    help="Provide any regex pattern that will be performed on each found filepath with re.search()",
)

parser.add_argument(
    "--yes",
    help="If --yes is provided there will be no confirmation prompt.",
    action="store_true",
)


def main():
    args = parser.parse_args()
    app.purge(args)


if __name__ == "__main__":
    main()
