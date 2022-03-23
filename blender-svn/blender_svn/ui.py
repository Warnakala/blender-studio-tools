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

        layout.template_list(
            "UI_UL_list",
            "svn_file_list",
            context.scene.svn,
            "external_files",
            context.scene.svn,
            "external_files_active_index",
        )


registry = [
    VIEW3D_PT_svn,
    VIEW3D_PT_svn_files
]