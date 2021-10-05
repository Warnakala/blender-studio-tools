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
# (c) 2021, Blender Foundation - Paul Golter

import re
from typing import List, Dict, Set

import bpy
from bpy.app.handlers import persistent

from media_viewer.ops import (
    MV_OT_toggle_filebrowser,
    MV_OT_toggle_timeline,
    MV_OT_next_media_file,
    MV_OT_screen_full_area,
)
from media_viewer import opsdata
from media_viewer.log import LoggerFactory


logger = LoggerFactory.getLogger(name=__name__)

addon_keymap_items = []


def clear_shortcuts(
    mode: str = "EXCLUDE",
    keymap_pattern: str = r"",
    op_name_pattern: str = r"",
    map_type_pattern: str = r"",
    key_pattern: str = r"",
) -> bool:
    """
    Deletes keymap items, based on the filtering input.

    If mode == "EXCLUDE" it will clear all shortcuts but keep the ones defined in the pattern keys.
    If mode == "INCLUDE" it will clear only shortcuts that are in included in the pattern keys.

    If input patterns are empty, the corresponding items will be skipped.

    keymap_pattern: regular expression string to filter a keymap.name
    op_name_pattern: regular expression string to filter a operator name of keymap_item, e.G 'screen.animation_step',
    map_type_pattern: regular expression string to filter a keymap_item that use a specific map_type, e.G 'MOUSE', 'KEYBOARD'
    key_pattern: regular expression string to filter a keymap_item that use a special key, e.G 'X', 'NUMPAD_PLUS'
    """

    for kcfg in bpy.context.window_manager.keyconfigs:

        # Filter keymaps.
        keymaps_to_process: List[bpy.types.KeyMap] = []

        for keymap in kcfg.keymaps:

            if mode == "EXCLUDE":
                if not keymap_pattern:
                    keymaps_to_process.append(keymap)
                    continue

                if re.search(keymap_pattern, keymap.name):
                    continue

            elif mode == "INCLUDE":
                if not keymap_pattern:
                    continue

                # print(f"Performing search on: {keymap.name} with {keymap_pattern}")
                if re.search(keymap_pattern, keymap.name):
                    keymaps_to_process.append(keymap)

        # Filter keymap_items.
        print(f"Keymaps to process: {str(keymaps_to_process)}")
        for keymap in keymaps_to_process:

            keymap_items_to_delete: Set[bpy.types.KeyMapItem] = set()
            print(keymap)

            for op_name, keymap_item in keymap.keymap_items.items():
                print(keymap_item)

                if mode == "EXCLUDE":
                    if op_name_pattern:
                        if re.search(op_name_pattern, op_name):
                            continue

                    if map_type_pattern:
                        if re.search(map_type_pattern, keymap_item.map_type):
                            continue

                    if key_pattern:
                        if re.search(key_pattern, keymap_item.type):
                            continue

                    keymap_items_to_delete.add(keymap_item)
                    print(f"Deleting {op_name}: {keymap_item.type}")

                if mode == "INCLUDE":
                    print(f"processing {op_name}")
                    if op_name_pattern:
                        if re.search(op_name_pattern, op_name):
                            keymap_items_to_delete.add(keymap_item)
                            print(f"Deleting {op_name}: {keymap_item.type}")

                    if map_type_pattern:
                        if re.search(map_type_pattern, keymap_item.map_type):
                            keymap_items_to_delete.add(keymap_item)
                            print(f"Deleting {op_name}: {keymap_item.type}")

                    if key_pattern:
                        if re.search(key_pattern, keymap_item.type):
                            keymap_items_to_delete.add(keymap_item)
                            print(f"Deleting {op_name}: {keymap_item.type}")

            # Delete keymap items
            for keymap_item in keymap_items_to_delete:
                keymap.keymap_items.remove(keymap_item)


@persistent
def delete_shortcuts_load_post(_):
    bpy.context.preferences.use_preferences_save = False
    print("LOAD POST IS RUNNING")
    clear_shortcuts(
        mode="INCLUDE",
        keymap_pattern=r"Frames",
        op_name_pattern=r"screen.frame_offset",
        key_pattern=r"ARROW",
    )


def register():
    # Register Hotkeys.
    # Does not work if blender runs in background.
    if not bpy.app.background:
        global addon_keymap_items

        # Turn off autosave prefs.
        bpy.context.preferences.use_preferences_save = False

        # Clear all shortcuts except MOUSE, ignore Screen keymap
        """
        clear_shortcuts(
            keymap_pattern=r"(Screen)",
            map_type_pattern=r"MOUSE",
            key_pattern=r"SPACE",
        )
        # Clear arrow shortcuts for frame_offset operators.
        # Does not work on register. Maybe post load?
        clear_shortcuts(
            mode="INCLUDE",
            keymap_pattern=r"Frames",
            op_name_pattern=r"screen.frame_offset",
            key_pattern=r"ARROW",
        )
        """

        keymap = bpy.context.window_manager.keyconfigs.addon.keymaps.new(name="Window")

        # Toggle Timeline.
        addon_keymap_items.append(
            keymap.keymap_items.new(
                MV_OT_toggle_timeline.bl_idname, value="PRESS", type="T"
            )
        )

        # Toggle Filebrowser.
        addon_keymap_items.append(
            keymap.keymap_items.new(
                MV_OT_toggle_filebrowser.bl_idname, value="PRESS", type="B"
            )
        )

        # Full Screen with Hide Panels.
        addon_keymap_items.append(
            keymap.keymap_items.new(
                MV_OT_screen_full_area.bl_idname, value="PRESS", type="F"
            )
        )

        # Next media file.
        kmi = keymap.keymap_items.new(
            MV_OT_next_media_file.bl_idname, value="PRESS", type="RIGHT_ARROW"
        )
        kmi.properties.direction = "RIGHT"
        addon_keymap_items.append(kmi)

        # Previous media file.
        kmi = keymap.keymap_items.new(
            MV_OT_next_media_file.bl_idname, value="PRESS", type="LEFT_ARROW"
        )
        kmi.properties.direction = "LEFT"
        addon_keymap_items.append(kmi)

        for kmi in addon_keymap_items:
            logger.info(
                "Registered new hotkey: %s : %s", kmi.type, kmi.properties.bl_rna.name
            )

    # Handlers
    # Does neither work on register or on load_post. But when reloading the file it works.....?????
    # bpy.app.handlers.load_post.append(delete_shortcuts_load_post)


def unregister():
    # Unregister Hotkeys.
    # Does not work if blender runs in background.
    if not bpy.app.background:
        global addon_keymap_items
        keymap = bpy.context.window_manager.keyconfigs.addon.keymaps["Window"]

        for kmi in addon_keymap_items:
            logger.info("Remove  hotkey: %s : %s", kmi.type, kmi.properties.bl_rna.name)
            keymap.keymap_items.remove(kmi)

        addon_keymap_items.clear()

    # Handlers
    # bpy.app.handlers.load_post.remove(delete_shortcuts_load_post)
