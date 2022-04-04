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
from .prefs import get_visible_indicies


class VIEW3D_PT_svn(bpy.types.Panel):
    """SVN UI panel in the 3D View Sidebar."""
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'SVN'
    bl_label = 'SVN Repository'

    @classmethod
    def poll(cls, context):
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

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        # As long as there are any items, always draw the filters.
        self.use_filter_show = True

        if self.layout_type != 'DEFAULT':
            raise NotImplemented

        file_entry = item

        row = layout.row()
        extension = file_entry.name.split(".")[-1] if "." in file_entry.name else ""
        icon = 'QUESTION'
        if extension in ['abc']:
            icon = 'FILE_CACHE'
        elif extension in ['blend', 'blend1']:
            icon = 'FILE_BLEND'
        elif extension in ['tga', 'bmp', 'tif', 'tiff', 'tga', 'png', 'dds', 'jpg', 'exr', 'hdr']:
            icon = 'TEXTURE'
        elif extension in ['mp4', 'mov']:
            icon = 'SEQUENCE'
        elif extension in ['mp3', 'ogg', 'wav']:
            icon = 'SPEAKER'

        split = row.split(factor=0.8)
        split.prop(file_entry, 'name', text="", emboss=False, icon=icon)

        row = split.row()
        split = row.split(factor=0.2)
        explainer = split.operator('svn.explain_status', text="", icon=file_entry.status_icon)
        explainer.status = file_entry.status
        explainer.file_rel_path = file_entry.svn_path

        row = split.row(align=True)
        row.alignment = 'RIGHT'

        # SVN operations
        ops = []
        if file_entry.status == 'none':
            ops.append(row.operator('svn.update_single', text="", icon='IMPORT'))
        if file_entry.status == 'modified':
            ops.append(row.operator('svn.revert_file', text="", icon='LOOP_BACK'))
        if file_entry.status in ['missing', 'deleted']:
            ops.append(row.operator('svn.restore_file', text="", icon='LOOP_BACK'))
            if file_entry.status == 'missing':
                ops.append(row.operator('svn.remove_file', text="", icon='TRASH'))
        if file_entry.status == 'added':
            ops.append(row.operator('svn.unadd_file', text="", icon='REMOVE'))
        if file_entry.status == 'unversioned':
            ops.append(row.operator('svn.add_file', text="", icon='ADD'))
            ops.append(row.operator('svn.trash_file', text="", icon='TRASH'))

        if ops:
            for op in ops:
                op.file_rel_path = file_entry.svn_path

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

        if not prefs.include_normal:
            for i, item in enumerate(list_items):
                flt_flags[i] *= int(item.status != "normal")

        if not prefs.include_entire_repo:
            for i, item in enumerate(list_items):
                flt_flags[i] *= int(item.is_referenced)

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
        """Default filtering UI:
        - String input for name filtering
        - Toggles for invert, sort alphabetical, reverse sort
        """
        main_row = layout.row()
        row = main_row.row(align=True)

        prefs = get_addon_prefs(context)
        row.prop(prefs, 'search_filter', text="")

        row = main_row.row(align=True)
        row.use_property_split=True
        row.use_property_decorate=False
        row.prop(prefs, 'include_normal', toggle=True, text="", icon="CHECKMARK")
        row.prop(prefs, 'include_entire_repo', toggle=True, text="", icon='DISK_DRIVE')


class SVN_MT_context_menu(bpy.types.Menu):
    bl_label = "SVN Operations"

    def draw(self, context):
        layout = self.layout

        layout.operator("svn.check_for_local_changes", icon='FILE_REFRESH')
        layout.operator("svn.cleanup", icon='BRUSH_DATA')
        svn = context.scene.svn
        if svn.log_update_in_progress:
            layout.operator("svn.update_log_cancel", icon="TEXT")
        else:
            layout.operator("svn.update_log", icon="TEXT")


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

        active_file = context.scene.svn.external_files[context.scene.svn.external_files_active_index]

        any_visible = get_visible_indicies(context)
        if not any_visible:
            return

        layout.prop(active_file, 'svn_path')
        layout.prop(active_file, 'revision')


registry = [
    SVN_UL_file_list,
    SVN_MT_context_menu,
    VIEW3D_PT_svn,
    VIEW3D_PT_svn_files,
]