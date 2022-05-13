# Sometimes library paths seem to become invalid for no apparent reason,
# so this adds a pre- and post-save handler to warn about invalid library paths.

from typing import Set
import bpy, os
from bpy.types import Library
from bpy.app.handlers import persistent

lib_paths_before_save = set()

def get_invalid_libraries() -> Set[Library]:
    """Return a set of library datablocks whose filepath does not exist."""
    invalid_libs: Set[Library] = set()
    for l in bpy.data.libraries:
        if not os.path.exists(bpy.path.abspath(l.filepath)):
            invalid_libs.add(l)
    return invalid_libs

def get_absolute_libraries() -> Set[Library]:
    """Return a set of library datablocks whose filepaths are not relative."""
    abs_libs: Set[Library] = set()
    for lib in bpy.data.libraries:
        if not lib.filepath.startswith("//"):
            abs_libs.add(lib)
    return abs_libs

def get_library_paths() -> Set[str]:
    """Simply return a set of all library paths."""
    return [l.filepath for l in bpy.data.libraries]

def throw_popup_dialog(context):
    context.window_manager.invoke_popup(self, width=300)

def draw_absolute_library_warning(self, context):
    layout = self.layout
    layout.alert=True
    print("Saved with absolute library paths:")
    for lib in get_absolute_libraries():
        print(lib.filepath)
    layout.label(text="Click this button and save again before committing:")
    layout.operator('file.make_paths_relative')
    layout.label(text="Then report this to Demeter!")

def draw_invalid_library_warning(self, context):
    layout = self.layout
    layout.alert=True

    print("Saved with invalid library paths!")
    lib_paths_after_save = get_library_paths()
    for new_path in lib_paths_after_save:
        if new_path in lib_paths_before_save:
            lib_paths_after_save.remove(new_path)
            lib_paths_before_save.remove(new_path)

    if len(lib_paths_before_save) > 0:
        layout.label(text="Libraries disappeared since last save:")
        print("Old paths that have changed:")
        for old_path in lib_paths_before_save:
            text = f'     "{old_path}"'
            layout.label(text=text, icon='REMOVE')
            print(text)

    if len(lib_paths_after_save) > 0:
        layout.label(text="Libraries added since last save:")
        print("New paths that appeared:")
        for new_path in lib_paths_after_save:
            text = f'     "{new_path}"'
            layout.label(text=text, icon='ADD')
            print(text)
    
    layout.label(text="Invalid libraries:")
    print("Invalid libraries:")
    for invalid_lib in get_invalid_libraries():
        text = f'     "{invalid_lib.filepath}"'
        layout.label(text=text, icon='LIBRARY_DATA_BROKEN')
        print(text)

@persistent
def warn_about_incorrect_lib_paths(dummy=None):
    invalid_libs = get_invalid_libraries()
    abs_libs = get_absolute_libraries()
    if len(invalid_libs) > 0:
        bpy.context.window_manager.popup_menu(
            draw_invalid_library_warning, title="Warning: Saved with invalid library paths.", icon='ERROR'
        )
    elif len(abs_libs) > 0:
        bpy.context.window_manager.popup_menu(
            draw_absolute_library_warning, title="Warning: Saved with absolute library paths.", icon='ERROR'
        )
    
    store_lib_paths()

@persistent
def store_lib_paths(dummy1=None, dummy2=None):
    """Store library paths before saving file, to later check if the file saving
    process might've affected the paths."""
    global lib_paths_before_save
    lib_paths_before_save = get_library_paths()

def register():
    bpy.app.handlers.load_post.append(store_lib_paths)
    bpy.app.handlers.save_post.append(warn_about_incorrect_lib_paths)

def unregister():
    bpy.app.handlers.load_post.remove(store_lib_paths)
    bpy.app.handlers.save_post.remove(warn_about_incorrect_lib_paths)
