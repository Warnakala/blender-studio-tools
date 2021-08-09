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

filetree_default = {
    "working": {
        "mountpoint": "",
        "root": "",
        "folder_path": {
            "shot": "<Project>/shots/production/<Sequence>/<Shot>/<TaskType>/work",
            "asset": "<Project>/assets/<AssetType>/<Asset>/<TaskType>/work",
            "sequence": "<Project>/shots/production/<Sequence>/<TaskType>/work",
            "style": "lowercase",
        },
        "file_name": {
            "shot": "<Shot>_<TaskType>_work",
            "asset": "<Asset>_<TaskType>_work",
            "sequence": "<Sequence>_<TaskType>_work",
            "style": "lowercase",
        },
    },
    "output": {
        "mountpoint": "",
        "root": "",
        "folder_path": {
            "shot": "<Project>/shots/production/<Sequence>/<Shot>/<TaskType>/publish",
            "asset": "<Project>/assets/<AssetType>/<Asset>/<TaskType>/publish",
            "sequence": "<Project>/shots/production/<Sequence>/<TaskType>/publish",
            "style": "lowercase",
        },
        "file_name": {
            "shot": "<Shot>_<TaskType>_publish",
            "asset": "<Asset>_<TaskType>_publish",
            "sequence": "<Sequence>_<TaskType>_publish",
            "style": "lowercase",
        },
    },
    "preview": {
        "mountpoint": "",
        "root": "",
        "folder_path": {
            "shot": "<Project>/shots/production/<Sequence>/<Shot>/<TaskType>/preview",
            "asset": "<Project>/assets/<AssetType>/<Asset>/<TaskType>/preview",
            "sequence": "<Project>/shots/production/<Sequence>/<TaskType>/preview",
            "style": "lowercase",
        },
        "file_name": {
            "shot": "<Shot>_<TaskType>_preview",
            "asset": "<Asset>_<TaskType>_preview",
            "sequence": "<Sequence>_<TaskType>_preview",
            "style": "lowercase",
        },
    },
}
