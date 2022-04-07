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
        if file_entry.status in ['missing', 'deleted']:
            ops.append(row.operator('svn.restore_file', text="", icon='LOOP_BACK'))
            if file_entry.status == 'missing':
                ops.append(row.operator('svn.remove_file', text="", icon='TRASH'))
        elif file_entry.status == 'added':
            ops.append(row.operator('svn.unadd_file', text="", icon='REMOVE'))
        elif file_entry.status == 'unversioned':
            ops.append(row.operator('svn.add_file', text="", icon='ADD'))
            ops.append(row.operator('svn.trash_file', text="", icon='TRASH'))

        elif file_entry.status == 'modified':
            ops.append(row.operator('svn.revert_file', text="", icon='LOOP_BACK'))
            if file_entry.repos_status == 'modified':
                # The file isn't actually `conflicted` yet, by SVN's definition, 
                # but it will be as soon as we try to commit or update.
                # I think it's better to let the user know in advance.
                statuses.append('conflicted')
                # Updating the file will create an actual conflict.
                ops.append(row.operator('svn.update_single', text="", icon='IMPORT'))

        elif file_entry.status == 'conflicted':
            ops.append(row.operator('svn.resolve_conflict', text="", icon='TRACKING_CLEAR_FORWARDS'))
        elif file_entry.status in ['incomplete', 'obstructed']:
            ops.append(row.operator('svn.cleanup', text="", icon='BRUSH_DATA'))
        elif file_entry.status == 'none':
            if file_entry.repos_status == 'added':
                # From user POV it makes a bit more sense to call a file that doesn't
                # exist yet "added" instead of "outdated".
                statuses.append('added')
            ops.append(row.operator('svn.update_single', text="", icon='IMPORT'))
        elif file_entry.status == 'normal' and file_entry.repos_status == 'modified':
            # From user POV, this file is outdated, not 'normal'.
            statuses = ['none']
            ops.append(row.operator('svn.update_single', text="", icon='IMPORT'))
        elif file_entry.status in ['normal', 'external', 'ignored']:
            pass
        else:
            print("Unknown file status: ", file_entry.svn_path, file_entry.status, file_entry.repos_status)

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

        has_default_status = lambda f: f.status == 'normal' and f.repos_status == 'none'

        if not flt_flags:
            # Start with all files visible.
            flt_flags = [cls.UILST_FLT_ITEM] * len(list_items)

        for i, item in enumerate(list_items):
            if has_default_status(item) and not item.is_referenced:
                # ALWAYS filter out files that have default statuses and aren't referenced.
                flt_flags[i] = 0

            if prefs.only_referenced_files:
                # Filter out files that are not being referenced, regardless of status.
                flt_flags[i] *= int(item.is_referenced)
                if has_default_status(item) and not prefs.include_normal:
                    # Filter out files that are being referenced but have default status.
                    flt_flags[i] = 0
            else:
                # Filter out files that have default status.
                if has_default_status(item):
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
            layout.label(text="No files detected in the repository")
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

        col.separator()
        col.operator("svn.commit", icon='EXPORT', text="")
        col.operator("svn.update_all", icon='IMPORT', text="")

        col.separator()
        col.operator("svn.cleanup", icon='BRUSH_DATA', text="")

        active_file = context.scene.svn.active_file
        layout.prop(active_file, "revision", emboss=False)

class SVN_file_outdated_warning(bpy.types.Operator):
    bl_idname = "svn.file_outdated_warning"
    bl_label = "" # Don't want the first line of the tooltip on mouse hover.
    bl_description = "The currently opened .blend file has a newer version available on the remote repository. This means any changes in this file will result in a conflict, and potential loss of data! See the SVN panel for info"
    bl_options = {'INTERNAL'}

    def execute(self, context):
        return {'FINISHED'}

def draw_outdated_file_warning(self, context):
    svn = context.scene.svn
    current_file = svn.current_blend_file
    if not current_file:
        # If the current file is not in an SVN repository.
        return

    if current_file.status == 'normal' and current_file.repos_status == 'none':
        return

    layout = self.layout
    row = layout.row()
    row.alert = True

    if current_file.status == 'conflicted':
        row.operator('svn.resolve_conflict', text="SVN: This .blend file is conflicted!", icon='ERROR')
    elif current_file.repos_status != 'none':
        row.operator('svn.file_outdated_warning', text="SVN: This .blend file is outdated!", icon='ERROR')


registry = [
    SVN_UL_file_list,
    VIEW3D_PT_svn,
    VIEW3D_PT_svn_files,
    SVN_file_outdated_warning
]

def register():
    bpy.types.VIEW3D_HT_header.prepend(draw_outdated_file_warning)

def unregister():
    bpy.types.VIEW3D_HT_header.remove(draw_outdated_file_warning)