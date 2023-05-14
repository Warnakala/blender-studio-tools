# SPDX-License-Identifier: GPL-2.0-or-later
# (c) 2022, Blender Foundation - Demeter Dzadik

import bpy
from bpy.props import BoolProperty, StringProperty

from time import time

from ..util import get_addon_prefs
from .. import constants
from ..commands.background_process import processes

class SVN_UL_file_list(bpy.types.UIList):
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

        svn = data
        file_entry = item

        main_row = layout.row()
        split = main_row.split(factor=0.6)
        filepath_ui = split.row()
        split = split.split(factor=0.4)
        status_ui = split.row(align=True)

        ops_ui = split.row(align=True)
        ops_ui.alignment = 'RIGHT'
        ops_ui.enabled = file_entry.status_predicted_flag == 'NONE'

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

        scene_svn = context.scene.svn
        repo = scene_svn.get_repo(context)

        def has_default_status(file):
            return file.status == 'normal' and file.repos_status == 'none'

        if scene_svn.file_search_filter:
            flt_flags = helper_funcs.filter_items_by_name(scene_svn.file_search_filter, cls.UILST_FLT_ITEM, list_items, "name",
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
        if not self.use_filter_show:
            # Prevent hiding the filter options when there are any file entries.
            # This is done by disabling filtering when the filtering UI would be
            # hidden. If there are any entries, draw_item() switches the
            # filtering UI back on with self.use_filter_show=True.
            list_items = getattr(data, propname)
            helper_funcs = bpy.types.UI_UL_list
            flt_neworder = helper_funcs.sort_items_by_name(list_items, "name")
            flt_flags = [type(self).UILST_FLT_ITEM] * len(list_items)
            # return flt_flags, flt_neworder
        return type(self).cls_filter_items(context, data, propname)

    def draw_filter(self, context, layout):
        """Custom filtering UI.
        Toggles are stored in addon preferences, see cls_filter_items().
        """
        main_row = layout.row()
        row = main_row.row(align=True)

        row.prop(self, 'show_file_paths', text="",
                 toggle=True, icon="FILE_FOLDER")
        row.prop(context.scene.svn, 'file_search_filter', text="")


def svn_file_list_context_menu(self: bpy.types.UIList, context: bpy.types.Context) -> None:
    def is_svn_file_list() -> bool:
        # Important: Must check context first, or the menu is added for every kind of list.
        ui_list = getattr(context, "ui_list", None)
        return ui_list and ui_list.bl_idname == 'SVN_UL_file_list'

    if not is_svn_file_list():
        return

    layout = self.layout
    layout.separator()
    active_file = context.scene.svn.get_repo(context).active_file
    layout.operator("wm.path_open",
                    text=f"Open {active_file.name}").filepath = active_file.relative_path
    layout.operator("wm.path_open",
                    text=f"Open Containing Folder").filepath = active_file.absolute_path.parent.as_posix()
    layout.separator()


def svn_log_list_context_menu(self: bpy.types.UIList, context: bpy.types.Context) -> None:
    def is_svn_log_list() -> bool:
        # Important: Must check context first, or the menu is added for every kind of list.
        ui_list = getattr(context, "ui_list", None)
        return ui_list and ui_list.bl_idname == 'SVN_UL_log'

    if not is_svn_log_list():
        return

    is_filebrowser = context.space_data.type == 'FILE_BROWSER'
    layout = self.layout
    layout.separator()

    repo = context.scene.svn.get_repo(context)
    active_log = repo.active_log_filebrowser if is_filebrowser else repo.active_log
    layout.operator("svn.download_repo_revision",
                    text=f"Revert Repository To r{active_log.revision_number}").revision = active_log.revision_number
    layout.separator()


class VIEW3D_PT_svn_credentials(bpy.types.Panel):
    """Prompt the user to enter their username and password for the remote repository of the current .blend file."""
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'SVN'
    bl_label = 'SVN Credentials'

    @classmethod
    def poll(cls, context):
        repo = context.scene.svn.get_repo(context)
        if not repo:
            # The repo entry should've been created at load_post() by set_scene_svn_info()
            return False

        return not repo.authenticated

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        col = layout.column(align=True)
        repo = context.scene.svn.get_repo(context)
        row = col.row()
        row.prop(repo, 'name', text="Repo Name", icon='FILE_TEXT')
        url = row.operator('svn.custom_tooltip', text="", icon='URL')
        url.tooltip = repo.url
        url.copy_on_click = True
        col.prop(repo, 'username', icon='USER')
        col.prop(repo, 'password', icon='UNLOCKED')
        global processes
        auth_proc = processes.get('Authenticate')
        if auth_proc and auth_proc.is_running:
            col.enabled = False
            layout.label(text="Authenticating" + dots())
        if repo.auth_failed:
            row = layout.row()
            row.alert = True
            row.label(text="Authentication failed. Double-check your credentials.")


def dots():
    return "." * int((time() % 10) + 3)


class VIEW3D_PT_svn_files(bpy.types.Panel):
    """Display a list of files in the SVN repository of the current .blend file."""
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'SVN'
    bl_label = 'SVN Files'

    @classmethod
    def poll(cls, context):
        repo = context.scene.svn.get_repo(context)
        return repo and repo.authenticated

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        draw_svn_file_list(context, layout)


def draw_svn_file_list(context, layout):
    repo = context.scene.svn.get_repo(context)

    process_message = "File statuses are updated every few seconds."
    any_error = False
    for process_id in ['Commit', 'Update', 'Log', 'Status']:
        if process_id not in processes:
            continue
        process = processes[process_id]

        if process.is_running:
            message = process.get_ui_message(context)
            if message:
                message = message.replace("...", dots())
                process_message = f"SVN {process_id}: {message}"
                any_process = True
        elif process.error:
            any_error = True
            row = layout.row()
            row.alert = True
            warning = row.operator(
                'svn.clear_error', text=f"SVN {process_id}: Error Occurred. Hover to view", icon='ERROR')
            warning.process_id = process_id
            warning.copy_on_click = True

    if not any_error:
        layout.label(text=process_message)

    main_col = layout.column()
    main_col.enabled = repo.seconds_since_last_update < 30
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
                       emboss=False).tooltip = "Time since last file status update: " + str(repo.seconds_since_last_update) + 's'

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


class SVN_custom_tooltip(bpy.types.Operator):
    bl_idname = "svn.custom_tooltip"
    bl_label = ""  # Don't want the first line of the tooltip on mouse hover.
    bl_description = ""
    bl_options = {'INTERNAL'}

    tooltip: StringProperty(
        name="Tooltip",
        description="Tooltip that is displayed when mouse hovering this operator"
    )
    copy_on_click: BoolProperty(
        name="Copy on Click",
        description="If True, the tooltip will be copied to the clipboard when the operator is clicked",
        default=False
    )

    @classmethod
    def description(cls, context, properties):
        return properties.tooltip

    def execute(self, context):
        if self.copy_on_click:
            context.window_manager.clipboard = self.tooltip
        return {'FINISHED'}


class SVN_clear_error(SVN_custom_tooltip):
    bl_idname = "svn.clear_error"
    bl_label = "Error:"
    bl_description = ""
    bl_options = {'INTERNAL'}

    process_id: StringProperty()

    @classmethod
    def description(cls, context, properties):
        process = processes[properties.process_id]
        return process.error + "\n\n" + process.error_description

    def execute(self, context):
        super().execute(context)
        processes[self.process_id].clear_error()

        return {'FINISHED'}


def draw_outdated_file_warning(self, context):
    repo = context.scene.svn.get_repo(context)
    if not repo:
        return
    try:
        current_file = repo.current_blend_file
    except ValueError:
        # This can happen if the svn_directory property wasn't update yet (not enough time has passed since opening the file)
        pass
    if not current_file:
        # If the current file is not in an SVN repository.
        return

    if current_file.status == 'normal' and current_file.repos_status == 'none':
        return

    layout = self.layout
    row = layout.row()
    row.alert = True

    if current_file.status == 'conflicted':
        row.operator('svn.resolve_conflict',
                     text="SVN: This .blend file is conflicted.", icon='ERROR')
    elif current_file.repos_status != 'none':
        warning = row.operator(
            'svn.custom_tooltip', text="SVN: This .blend file is outdated.", icon='ERROR')
        warning.tooltip = "The currently opened .blend file has a newer version available on the remote repository. This means any changes in this file will result in a conflict, and potential loss of data. See the SVN panel for info"


registry = [
    SVN_UL_file_list,
    VIEW3D_PT_svn_credentials,
    VIEW3D_PT_svn_files,
    SVN_custom_tooltip,
    SVN_clear_error
]


def register():
    bpy.types.VIEW3D_HT_header.prepend(draw_outdated_file_warning)

    bpy.types.UI_MT_list_item_context_menu.append(svn_file_list_context_menu)
    bpy.types.UI_MT_list_item_context_menu.append(svn_log_list_context_menu)


def unregister():
    bpy.types.VIEW3D_HT_header.remove(draw_outdated_file_warning)

    bpy.types.UI_MT_list_item_context_menu.remove(svn_file_list_context_menu)
    bpy.types.UI_MT_list_item_context_menu.remove(svn_log_list_context_menu)
