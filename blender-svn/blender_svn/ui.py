import bpy
from .util import get_addon_prefs

class VIEW3D_PT_svn(bpy.types.Panel):
    """SVN UI panel in the 3D View Sidebar."""
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'SVN'
    bl_label = 'Repository'

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
        col.enabled = False
        col.prop(prefs, 'svn_url')
        col.prop(prefs, 'svn_directory')
        col.prop(prefs, 'relative_filepath')
        col.prop(prefs, 'revision_number')
        col.prop(prefs, 'revision_date')
        col.prop(prefs, 'revision_author')


class SVN_UL_file_list(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
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

        row.prop(file_entry, 'name', text="", emboss=False, icon=icon)
        row.prop(file_entry, 'status', text="", emboss=False)


class VIEW3D_PT_svn_files(bpy.types.Panel):
    """Display a list of files that the current .blend file depends on"""
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'SVN'
    bl_label = 'Files'

    @classmethod
    def poll(cls, context):
        prefs = get_addon_prefs(context)
        return prefs.enable_ui and prefs.is_in_repo

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        layout.operator("svn.refresh_file_list", icon='FILE_REFRESH')

        if len(context.scene.svn.external_files) == 0:
            return

        layout.template_list(
            "SVN_UL_file_list",
            "svn_file_list",
            context.scene.svn,
            "external_files",
            context.scene.svn,
            "external_files_active_index",
        )

        active_file = context.scene.svn.external_files[context.scene.svn.external_files_active_index]
        col = layout.column()
        col.enabled=False
        col.prop(active_file, 'status')
        col.prop(active_file, 'revision')


registry = [
    VIEW3D_PT_svn,
    SVN_UL_file_list,
    VIEW3D_PT_svn_files,
]