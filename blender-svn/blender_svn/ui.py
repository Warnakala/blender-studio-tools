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

import bpy
from .util import get_addon_prefs

from bpy.props import BoolProperty

from . import svn_status

class VIEW3D_PT_svn(bpy.types.Panel):
    """SVN UI panel in the 3D View Sidebar."""
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'SVN'
    bl_label = 'SVN Repository'

    @classmethod
    def poll(cls, context):
        return False
        prefs = get_addon_prefs(context)
        return prefs.enable_ui and prefs.is_in_repo

    def draw(self, context):
        prefs = get_addon_prefs(context)
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        col = layout.column(align=True)

        col.prop(prefs, 'svn_url', emboss=False)
        col.prop(prefs, 'svn_directory', emboss=False)
        col.prop(prefs, 'relative_filepath', emboss=False)
        col.prop(prefs, 'revision_number', emboss=False)
        col.prop(prefs, 'revision_date', emboss=False)
        col.prop(prefs, 'revision_author', emboss=False)


class SVN_UL_file_list(bpy.types.UIList):
    UILST_FLT_ITEM = 1 << 30 # Value that indicates that this item has passed the filter process successfully. See rna_ui.c.

    show_file_paths: BoolProperty(
        name = "Show File Paths",
        description = "Show file paths relative to the SVN root, instead of just the file name"
    )

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        # As long as there are any items, always draw the filters.
        self.use_filter_show = True

        if self.layout_type != 'DEFAULT':
            raise NotImplemented

        svn = data
        file_entry = item

        row = layout.row()
        split = row.split(factor=0.7)
        if self.show_file_paths:
            split.prop(file_entry, 'svn_path', text="", emboss=False, icon=file_entry.file_icon)
        else:
            split.prop(file_entry, 'name', text="", emboss=False, icon=file_entry.file_icon)

        row = split.row()
        split = row.split(factor=0.4)
        status_row = split.row(align=True)
        statuses = [file_entry.status]

        row = split.row(align=True)
        row.alignment = 'RIGHT'

        # SVN operations
        ops = []
        if file_entry.status == 'none':
            ops.append(row.operator('svn.update_single', text="", icon='IMPORT'))
        if file_entry.status == 'modified':
            ops.append(row.operator('svn.revert_file', text="", icon='LOOP_BACK'))
            if svn.is_file_outdated(file_entry):
                # This happens when we checkout an older version of the file and modify it,
                # So we can immediately know that the file will be in conflict.
                statuses.append('conflicted')
                ops.append(row.operator('svn.update_single', text="", icon='IMPORT'))
        if file_entry.status in ['missing', 'deleted']:
            ops.append(row.operator('svn.restore_file', text="", icon='LOOP_BACK'))
            if file_entry.status == 'missing':
                ops.append(row.operator('svn.remove_file', text="", icon='TRASH'))
        if file_entry.status == 'added':
            if file_entry.revision == 0:
                # This means the file only exists on the remote.
                statuses.append('none')
                ops.append(row.operator('svn.update_single', text="", icon='IMPORT'))
            else:
                ops.append(row.operator('svn.unadd_file', text="", icon='REMOVE'))
        if file_entry.status == 'unversioned':
            ops.append(row.operator('svn.add_file', text="", icon='ADD'))
            ops.append(row.operator('svn.trash_file', text="", icon='TRASH'))
        if file_entry.status == 'conflicted':
            if file_entry.newer_on_remote:
                # This happens when we make changes to a file then check for updates on the remote, and find one.
                # See Strange case 3 in SVN_check_for_updates.
                ops.append(row.operator('svn.revert_file', text="", icon='LOOP_BACK'))
                ops.append(row.operator('svn.update_single', text="", icon='IMPORT'))
            else:
                ops.append(row.operator('svn.resolve_conflict', text="", icon='TRACKING_CLEAR_FORWARDS'))

        if ops:
            for op in ops:
                op.file_rel_path = file_entry.svn_path

        # Populate the status icons.
        for status in statuses:
            icon = svn_status.SVN_STATUS_DATA[status][0]
            explainer = status_row.operator('svn.explain_status', text="", icon=icon)
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

        prefs = get_addon_prefs(context)
        if prefs.search_filter:
            flt_flags = helper_funcs.filter_items_by_name(prefs.search_filter, cls.UILST_FLT_ITEM, list_items, "name",
                                                            reverse=False)

        if not flt_flags:
            flt_flags = [cls.UILST_FLT_ITEM] * len(list_items)

        if prefs.only_referenced_files:
            for i, item in enumerate(list_items):
                flt_flags[i] *= int(item.is_referenced)

        if not prefs.only_referenced_files or not prefs.include_normal:
            for i, item in enumerate(list_items):
                flt_flags[i] *= int(item.status != "normal")

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
            return flt_flags, flt_neworder
        return type(self).cls_filter_items(context, data, propname)

    def draw_filter(self, context, layout):
        """Custom filtering UI.
        Toggles are stored in addon preferences, see cls_filter_items().
        """
        main_row = layout.row()
        row = main_row.row(align=True)

        prefs = get_addon_prefs(context)
        row.prop(self, 'show_file_paths', text="", toggle=True, icon="FILE_FOLDER")
        row.prop(prefs, 'search_filter', text="")

        row = main_row.row(align=True)
        row.use_property_split=True
        row.use_property_decorate=False
        row.prop(prefs, 'only_referenced_files', toggle=True, text="", icon='APPEND_BLEND')
        col = row.column(align=True)
        col.enabled = prefs.only_referenced_files
        col.prop(prefs, 'include_normal', toggle=True, text="", icon="CHECKMARK")


class SVN_MT_context_menu(bpy.types.Menu):
    bl_label = "SVN Operations"

    def draw(self, context):
        layout = self.layout

        layout.operator("svn.check_for_local_changes", icon='FILE_REFRESH')
        layout.operator("svn.cleanup", icon='BRUSH_DATA')
        svn = context.scene.svn
        if svn.log_update_in_progress:
            layout.operator("svn.fetch_log_cancel", icon="TEXT")
        else:
            layout.operator("svn.fetch_log", icon="TEXT")


class VIEW3D_PT_svn_files(bpy.types.Panel):
    """Display a list of files in the SVN repository of the current .blend file."""
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'SVN'
    bl_label = 'SVN Files'

    @classmethod
    def poll(cls, context):
        prefs = get_addon_prefs(context)
        return prefs.enable_ui and prefs.is_in_repo

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        if len(context.scene.svn.external_files) == 0:
            layout.operator("svn.check_for_local_changes", icon='FILE_REFRESH')
            return

        row = layout.row()

        row.template_list(
            "SVN_UL_file_list",
            "svn_file_list",
            context.scene.svn,
            "external_files",
            context.scene.svn,
            "external_files_active_index",
        )

        col = row.column()
        col.operator("svn.check_for_updates", icon='URL', text="")

        col.separator()
        col.operator("svn.update_all", icon='IMPORT', text="")
        col.operator("svn.commit", icon='CHECKMARK', text="")

        col.separator()
        col.row().menu(menu='SVN_MT_context_menu', text="", icon='TRIA_DOWN')

        active_file = context.scene.svn.active_file
        layout.prop(active_file, "revision", emboss=False)


registry = [
    SVN_UL_file_list,
    SVN_MT_context_menu,
    VIEW3D_PT_svn,
    VIEW3D_PT_svn_files,
]