# SPDX-License-Identifier: GPL-2.0-or-later
# (c) 2023, Blender Foundation - Demeter Dzadik

import time

import bpy
from bpy.types import UIList
from bpy.props import BoolProperty

from .. import constants
from ..util import get_addon_prefs, dots
from ..threaded.background_process import Processes


class SVN_UL_file_list(UIList):
    # Value that indicates that this item has passed the filter process successfully. See rna_ui.c.
    UILST_FLT_ITEM = 1 << 30

    show_file_paths: BoolProperty(
        name="Show File Paths",
        description="Show file paths relative to the SVN root, instead of just the file name"
    )

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        # As long as there are any items, always draw the filters.
        self.use_filter_show = True

        if self.layout_type != 'DEFAULT':
            raise NotImplemented

        repo = data
        file_entry = item
        prefs = get_addon_prefs(context)

        main_row = layout.row()
        split = main_row.split(factor=0.6)
        filepath_ui = split.row()
        split = split.split(factor=0.4)
        status_ui = split.row(align=True)

        ops_ui = split.row(align=True)
        ops_ui.alignment = 'RIGHT'

        ops_ui.enabled = file_entry.status_prediction_type == 'NONE' and not prefs.is_busy

        if self.show_file_paths:
            filepath_ui.prop(file_entry, 'svn_path', text="",
                             emboss=False, icon=file_entry.file_icon)
        else:
            filepath_ui.prop(file_entry, 'name', text="",
                             emboss=False, icon=file_entry.file_icon)

        statuses = [file_entry.status]
        # SVN operations
        ops = []
        if file_entry.status in ['missing', 'deleted']:
            ops.append(ops_ui.operator(
                'svn.restore_file', text="", icon='LOOP_BACK'))
            if file_entry.status == 'missing':
                ops.append(ops_ui.operator(
                    'svn.remove_file', text="", icon='TRASH'))
        elif file_entry.status == 'added':
            ops.append(ops_ui.operator(
                'svn.unadd_file', text="", icon='REMOVE'))
        elif file_entry.status == 'unversioned':
            ops.append(ops_ui.operator('svn.add_file', text="", icon='ADD'))
            ops.append(ops_ui.operator(
                'svn.trash_file', text="", icon='TRASH'))

        elif file_entry.status == 'modified':
            ops.append(ops_ui.operator(
                'svn.revert_file', text="", icon='LOOP_BACK'))
            if file_entry.repos_status == 'modified':
                # The file isn't actually `conflicted` yet, by SVN's definition,
                # but it will be as soon as we try to commit or update.
                # I think it's better to let the user know in advance.
                statuses.append('conflicted')
                # Updating the file will create an actual conflict.
                ops.append(ops_ui.operator(
                    'svn.update_single', text="", icon='IMPORT'))

        elif file_entry.status == 'conflicted':
            ops.append(ops_ui.operator('svn.resolve_conflict',
                       text="", icon='TRACKING_CLEAR_FORWARDS'))
        elif file_entry.status in ['incomplete', 'obstructed']:
            ops.append(ops_ui.operator(
                'svn.cleanup', text="", icon='BRUSH_DATA'))
        elif file_entry.status == 'none':
            if file_entry.repos_status == 'added':
                # From user POV it makes a bit more sense to call a file that doesn't
                # exist yet "added" instead of "outdated".
                statuses.append('added')
            ops.append(ops_ui.operator(
                'svn.update_single', text="", icon='IMPORT'))
        elif file_entry.status == 'normal' and file_entry.repos_status == 'modified':
            # From user POV, this file is outdated, not 'normal'.
            statuses = ['none']
            ops.append(ops_ui.operator(
                'svn.update_single', text="", icon='IMPORT'))
        elif file_entry.status in ['normal', 'external', 'ignored']:
            pass
        else:
            print("Unknown file status: ", file_entry.svn_path,
                  file_entry.status, file_entry.repos_status)

        for op in ops:
            if hasattr(op, 'file_rel_path'):
                op.file_rel_path = file_entry.svn_path

        # Populate the status icons.
        for status in statuses:
            icon = constants.SVN_STATUS_DATA[status][0]
            explainer = status_ui.operator(
                'svn.explain_status', text="", icon=icon, emboss=False)
            explainer.status = status
            explainer.file_rel_path = file_entry.svn_path

    @classmethod
    def cls_filter_items(cls, context, data, propname):
        """By moving all of this logic to a classmethod (and all the filter 
        properties to the addon preferences) we can find a visible entry
        from other UI code, allowing us to avoid situations where the active
        element becomes hidden."""
        flt_flags = []
        flt_neworder = []
        list_items = getattr(data, propname)

        helper_funcs = bpy.types.UI_UL_list

        # This list should ALWAYS be sorted alphabetically.
        flt_neworder = helper_funcs.sort_items_by_name(list_items, "name")

        repo = context.scene.svn.get_repo(context)
        if not repo:
            return flt_flags, flt_neworder

        def has_default_status(file):
            return file.status == 'normal' and file.repos_status == 'none' and file.status_prediction_type == 'NONE'

        if repo.file_search_filter:
            flt_flags = helper_funcs.filter_items_by_name(repo.file_search_filter, cls.UILST_FLT_ITEM, list_items, "name",
                                                          reverse=False)
        else:
            # Start with all files visible.
            flt_flags = [cls.UILST_FLT_ITEM] * len(list_items)

            for i, item in enumerate(list_items):
                if item == repo.current_blend_file:
                    # ALWAYS display the current .blend file.
                    continue

                if has_default_status(item):
                    # Filter out files that have default statuses.
                    flt_flags[i] = 0

        return flt_flags, flt_neworder

    def filter_items(self, context, data, propname):
        return type(self).cls_filter_items(context, data, propname)

    def draw_filter(self, context, layout):
        """Custom filtering UI.
        Toggles are stored in addon preferences, see cls_filter_items().
        """
        main_row = layout.row()
        row = main_row.row(align=True)

        row.prop(self, 'show_file_paths', text="",
                 toggle=True, icon="FILE_FOLDER")
        row.prop(context.scene.svn.get_repo(context), 'file_search_filter', text="")


def draw_process_info(context, layout):
    prefs = get_addon_prefs(context)
    process_message = ""
    any_error = False
    col = layout.column()
    for process in Processes.processes.values():
        if process.name not in {'Commit', 'Update', 'Log', 'Status', 'Authenticate'}:
            continue

        if process.error:
            row = col.row()
            row.alert = True
            warning = row.operator(
                'svn.clear_error', text=f"SVN {process.name}: Error Occurred. Hover to view", icon='ERROR')
            warning.process_id = process.name
            any_error = True
            break
        
        if process.is_running:
            message = process.get_ui_message(context)
            if message:
                message = message.replace("...", dots())
                process_message = f"SVN: {message}"

    if not any_error and process_message:
        col.label(text=process_message)
    if prefs.debug_mode:
        col.label(text="Processes: " + ", ".join([p.name for p in Processes.running_processes]))


def draw_repo_file_list(context, layout, repo):
    if not repo:
        return

    main_col = layout.column()
    main_col.enabled = False
    status_proc = Processes.get('Status')
    time_since_last_update = 1000
    if status_proc:
        time_since_last_update = time.time() - status_proc.timestamp_last_update
        if time_since_last_update < 30:
            main_col.enabled = True
    main_row = main_col.row()
    split = main_row.split(factor=0.6)
    filepath_row = split.row()
    filepath_row.label(text="          Filepath")

    status_row = split.row()
    status_row.label(text="         Status")

    ops_row = main_row.row()
    ops_row.alignment = 'RIGHT'
    ops_row.label(text="Operations")

    timer_row = main_row.row()
    timer_row.alignment = 'RIGHT'
    timer_row.operator("svn.custom_tooltip", icon='BLANK1', text="",
                       emboss=False).tooltip = "Time since last file status update: " + str(time_since_last_update) + 's'

    row = main_col.row()
    row.template_list(
        "SVN_UL_file_list",
        "svn_file_list",
        repo,
        "external_files",
        repo,
        "external_files_active_index",
    )

    col = row.column()

    col.separator()
    col.operator("svn.commit", icon='EXPORT', text="")
    col.operator("svn.update_all", icon='IMPORT', text="")

    col.separator()
    col.operator("svn.cleanup", icon='BRUSH_DATA', text="")


registry = [
    SVN_UL_file_list,
]
