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

        col = layout.column()
        col.prop(prefs, 'svn_url')
        col.prop(prefs, 'svn_directory')
        col.prop(prefs, 'relative_filepath')
        col.prop(prefs, 'revision_number')
        col.prop(prefs, 'revision_date')
        col.prop(prefs, 'revision_author')


class SVN_UL_file_list(bpy.types.UIList):
    UILST_FLT_ITEM = 1 << 30 # Value that indicates that this item has passed the filter process successfully. See rna_ui.c.

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        # As long as there are any items, always draw the filters.
        self.use_filter_show = True

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

        col.separator()
        cleanup = col.operator("svn.cleanup", icon='BRUSH_DATA', text="")
        cleanup.svn_root_abs_path = prefs.svn_directory

        active_file = context.scene.svn.external_files[context.scene.svn.external_files_active_index]

        any_visible = get_visible_indicies(context)
        if not any_visible:
            return

        col = layout.column()

        split = col.row().split(factor=0.4)
        row = split.row()
        row.alignment = 'RIGHT'
        row.label(text="Status")

        row = split.row()
        row.operator('svn.explain_status', text=active_file.status_name, icon=active_file.status_icon).status = active_file.status

        col.prop(active_file, 'path_str')
        col.prop(active_file, 'revision')


registry = [
    VIEW3D_PT_svn,
    SVN_UL_file_list,
    VIEW3D_PT_svn_files,
]