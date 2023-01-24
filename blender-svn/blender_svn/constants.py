# SPDX-License-Identifier: GPL-2.0-or-later
# (c) 2022, Blender Foundation - Demeter Dzadik

from collections import OrderedDict

SVN_STATUS_DATA = OrderedDict(
    [
        (
            "added",
            (
                "ADD",
                "This file was added",
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
                "This file was deleted",
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
                "GREASEPENCIL",
                "This file was modified",
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
                "This file has been moved",
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
    (status, status.title(),
     SVN_STATUS_DATA[status][1], SVN_STATUS_DATA[status][0], i)
    for i, status in enumerate(SVN_STATUS_DATA.keys())
]


SVN_STATUS_CHAR_TO_NAME = {
    '': 'normal',
    'A': 'added',
    'D': 'deleted',
    'M': 'modified',
    'R': 'replaced',
    'C': 'conflicted',
    'X': 'external',
    'I': 'ignored',
    '?': 'unversioned',
    '!': 'missing',
    '~': 'replaced'
}

SVN_STATUS_NAME_TO_CHAR = {value: key for key,
                           value in SVN_STATUS_CHAR_TO_NAME.items()}
