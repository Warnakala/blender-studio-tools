import bpy
import contextlib

@contextlib.contextmanager
def override_save_version():
        """Overrides the save version settings"""
        save_version = bpy.context.preferences.filepaths.save_version

        try:
            bpy.context.preferences.filepaths.save_version = 0
            yield

        finally:
            bpy.context.preferences.filepaths.save_version = save_version


with override_save_version():
    bpy.ops.wm.save_mainfile()
    print(f"Saved file: '{bpy.data.filepath}'")
    bpy.ops.wm.quit_blender()
