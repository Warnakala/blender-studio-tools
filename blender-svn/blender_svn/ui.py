import bpy
from .util import get_addon_prefs

from bpy.props import BoolProperty

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

        col = layout.column()
        col.prop(prefs, 'svn_url')
        col.prop(prefs, 'svn_directory')
        col.prop(prefs, 'relative_filepath')
        col.prop(prefs, 'revision_number')
        col.prop(prefs, 'revision_date')
        col.prop(prefs, 'revision_author')


class SVN_UL_file_list(bpy.types.UIList):
    include_normal: BoolProperty(
        name = "Show Normal Files",
        description = "Include files whose SVN status is Normal",
        default = False
    )
    include_entire_repo: BoolProperty(
        name = "Show All Files",
        description = "Include all modified files in the repository, even if they are not referenced by this .blend file",
        default = False
    )

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        if self.layout_type != 'DEFAULT':
            raise NotImplemented

        file_entry = item
        prefs = get_addon_prefs(context)

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

        split = row.split(factor=0.5)
        split.prop(file_entry, 'name', text="", emboss=False, icon=icon)

        row = split.row()
        split = row.split(factor=0.6)
        split.label(text=file_entry.status_name, icon=file_entry.status_icon)

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
                op.svn_root_abs_path = prefs.svn_directory
                op.file_rel_path = file_entry.svn_relative_path

    def filter_items(self, context, data, propname):
        """Default filtering functionality:
            - Filter by name
            - Sort alphabetical by name
        """
        flt_flags = []
        flt_neworder = []
        list_items = getattr(data, propname)

        helper_funcs = bpy.types.UI_UL_list

        # This list should ALWAYS be sorted alphabetically.
        flt_neworder = helper_funcs.sort_items_by_name(list_items, "name")

        if self.filter_name:
            flt_flags = helper_funcs.filter_items_by_name(self.filter_name, self.bitflag_filter_item, list_items, "name",
                                                            reverse=False)

        if not flt_flags:
            flt_flags = [self.bitflag_filter_item] * len(list_items)

        if not self.include_normal:
            for i, item in enumerate(list_items):
                flt_flags[i] *= int(item.status != "normal")

        if not self.include_entire_repo:
            for i, item in enumerate(list_items):
                flt_flags[i] *= int(item.is_referenced)

        return flt_flags, flt_neworder

    def draw_filter(self, context, layout):
        """Default filtering UI:
        - String input for name filtering
        - Toggles for invert, sort alphabetical, reverse sort
        """
        main_row = layout.row()
        row = main_row.row(align=True)

        row.prop(self, 'filter_name', text="")

        row = main_row.row(align=True)
        row.use_property_split=True
        row.use_property_decorate=False
        row.prop(self, 'include_normal', toggle=True, text="", icon="CHECKMARK")
        row.prop(self, 'include_entire_repo', toggle=True, text="", icon='DISK_DRIVE')

    def get_good_active_index(self, context) -> int:
        """Return the index of the first available item that is not being filtered out"""
        flt_flags, flt_neworder = self.filter_items(context, context.scene.svn, 'external_files')
        for i, flag in flt_flags:
            if flag != 0:
                return i
        return 0

class VIEW3D_PT_svn_files(bpy.types.Panel):
    """Display a list of files that the current .blend file depends on"""
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
        col.operator("svn.check_for_local_changes", icon='FILE_REFRESH', text="")
        check_up = col.operator("svn.check_for_updates", icon='URL', text="")
        prefs = get_addon_prefs(context)
        check_up.svn_root_abs_path = prefs.svn_directory
        col.separator()
        up = col.operator("svn.update_all", icon='IMPORT', text="")
        up.svn_root_abs_path = prefs.svn_directory
        col.operator("svn.commit", icon='CHECKMARK', text="")

        active_file = context.scene.svn.external_files[context.scene.svn.external_files_active_index]
        col = layout.column()
        split = col.row().split(factor=0.4)
        row = split.row()
        row.alignment = 'RIGHT'
        row.label(text="Status")
        split.label(text=active_file.status_name, icon=active_file.status_icon)
        col.prop(active_file, 'path_str')
        col.prop(active_file, 'revision')


registry = [
    VIEW3D_PT_svn,
    SVN_UL_file_list,
    VIEW3D_PT_svn_files,
]