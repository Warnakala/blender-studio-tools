import bpy


from shot_builder.operators import *

def topbar_file_new_draw_handler(self, context: bpy.types.Context):
    layout = self.layout
    op = layout.operator(SHOTBUILDER_OT_NewShotFile.bl_idname, text="Shot File")

