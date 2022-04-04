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
# (c) 2022, Blender Foundation - Demeter Dzadik

from typing import List, Dict, Union, Any, Set, Optional, Tuple
from collections import OrderedDict

import bpy
from bpy.props import StringProperty


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

SVN_STATUS_CHAR = {
    'M' : 'modified',
    'D' : 'deleted',
    'A' : 'added'
}

class SVN_explain_status(bpy.types.Operator):
    bl_idname = "svn.explain_status"
    bl_label = "" # Don't want the first line of the tooltip on mouse hover.
    bl_description = "Show an explanation of this status, using a dynamic tooltip"
    bl_options = {'INTERNAL'}

    popup_width = 600

    status: StringProperty(
        description = "Identifier of the status to show an explanation for"
    )
    file_rel_path: StringProperty(
        description = "Path of the file to select in the list when clicking this explanation, to act as if it was click-through-able"
    )

    @staticmethod
    def get_explanation(status: str):
        return SVN_STATUS_DATA[status][1]

    @classmethod
    def description(cls, context, properties):
        return cls.get_explanation(properties.status)

    def draw(self, context):
        self.layout.label(text=self.get_explanation(self.status))

    def execute(self, context):
        for i, f in enumerate(context.scene.svn.external_files):
            if f.svn_path == self.file_rel_path:
                context.scene.svn.external_files_active_index = i
        return {'FINISHED'}

registry = [SVN_explain_status]
