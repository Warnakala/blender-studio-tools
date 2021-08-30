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


from pathlib import Path
from typing import Set, Union, Optional, List, Dict, Any, Tuple

import bpy

from video_player import opsdata
from video_player.log import LoggerFactory


logger = LoggerFactory.getLogger(name=__name__)


class VP_OT_load_media(bpy.types.Operator):

    bl_idname = "video_player.load_media"
    bl_label = "Load Media"
    bl_description = (
        "Loads media in to sequence editor and clears any media before that"
    )
    filepath: bpy.props.StringProperty(name="Filepath", subtype="FILE_PATH")

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return True

    def execute(self, context: bpy.types.Context) -> Set[str]:
        filepath = Path(self.filepath)
        playback = False

        if not filepath.exists():
            return {"CANCELLED"}

        # Init Sequence Editor.
        if not context.scene.sequence_editor:
            context.scene.sequence_editor_create()

        # Stop playback.
        bpy.ops.screen.animation_cancel()

        # Clear all media in the sequence editor
        opsdata.del_all_sequences(context)

        # Import sequence.
        if opsdata.is_image(filepath):

            # Create new image strip.
            strip = context.scene.sequence_editor.sequences.new_image(
                filepath.stem,
                filepath.as_posix(),
                0,
                context.scene.frame_start,
            )
            playback = False

        elif opsdata.is_movie(filepath):

            # Create new movie strip.
            strip = context.scene.sequence_editor.sequences.new_movie(
                filepath.stem,
                filepath.as_posix(),
                0,
                context.scene.frame_start,
            )
            playback = True

        # Unsupported file format.
        else:
            logger.warning("Unsupported file format %s", filepath.suffix)
            return {"CANCELLED"}

        # Set frame range.
        opsdata.fit_frame_range_to_strips(context)

        # Adjust view of timeline to fit all.
        opsdata.fit_timeline_view(context)

        # Set playhead to start of scene.
        context.scene.frame_current = context.scene.frame_start

        # Playback.
        if playback:
            bpy.ops.screen.animation_play()

        return {"FINISHED"}


class VP_OT_toggle_timeline(bpy.types.Operator):

    bl_idname = "video_player.toggle_timeline"
    bl_label = "Toggle Timeline"
    bl_description = "Toggles visibility of timeline area"
    factor: bpy.props.FloatProperty(
        name="Factor that defines space for timeline after area split", default=0.15
    )

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return True

    def execute(self, context: bpy.types.Context) -> Set[str]:

        area_sqe = opsdata.find_area(context, "SEQUENCE_EDITOR")
        area_timeline = opsdata.find_area(context, "DOPESHEET_EDITOR")

        if area_timeline:
            # Timeline needs to be closed.
            opsdata.close_area(area_timeline)

        elif area_sqe:
            # Sequence Editor area needs to be splitted.
            # New area needs to be timeline
            opsdata.split_area(
                context, area_sqe, "DOPESHEET_EDITOR", "HORIZONTAL", self.factor
            )
            opsdata.fit_timeline_view(context)

        else:
            logger.error(
                "Toggle timeline failed. Missing areas: SEQUENCE_EDITOR | DOPESHEET_EDITOR"
            )
            return {"CANCELLED"}

        return {"FINISHED"}


class VP_OT_toggle_filebrowser(bpy.types.Operator):

    bl_idname = "video_player.toggle_filebrowser"
    bl_label = "Toggle Filebrowser"
    bl_description = "Toggles visibility of filebrowser area"
    factor_timeline: bpy.props.FloatProperty(
        name="Factor that defines space for timeline after area split", default=0.15
    )
    factor_filebrowser: bpy.props.FloatProperty(
        name="Factor that defines space for filebrowser after area split", default=0.3
    )

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return True

    def execute(self, context: bpy.types.Context) -> Set[str]:

        area_sqe = opsdata.find_area(context, "SEQUENCE_EDITOR")
        area_fb = opsdata.find_area(context, "FILE_BROWSER")
        area_time = opsdata.find_area(context, "DOPESHEET_EDITOR")
        screen_name = context.screen.name
        wm_name = context.window_manager.name

        if not area_fb and area_time and area_sqe:
            # If sqe and timeline visible but not filebrowser
            # we need to first close timeline and then open it after to
            # get correct layout.
            opsdata.close_area(area_time)

            # We need to do some custom context assembly here
            # because the bpy.ops.screen.area_close() sets context.screen to NULL.
            screen = bpy.data.screens[screen_name]
            ctx = opsdata.get_context_for_area(area_sqe)
            ctx["screen"] = screen
            ctx["window"] = bpy.data.window_managers[wm_name].windows[0]

            # Open filebrowser.
            area_fb = opsdata.split_area(
                ctx, area_sqe, "FILE_BROWSER", "VERTICAL", self.factor_filebrowser
            )

            # Open timeline
            area_time = opsdata.split_area(
                ctx, area_sqe, "DOPESHEET_EDITOR", "HORIZONTAL", self.factor_timeline
            )

        elif not area_fb:
            # Sequence Editor area needs to be splitted.
            # New area needs to be filebrowser.
            area_fb = opsdata.split_area(
                context, area_sqe, "FILE_BROWSER", "VERTICAL", self.factor_filebrowser
            )

        elif area_fb:
            # Filebrowser needs to be closed.
            opsdata.close_area(area_fb)
            return {"FINISHED"}

        else:
            logger.error(
                "Toggle timeline failed. Missing areas: SEQUENCE_EDITOR | FILE_BROWSER"
            )
            return {"CANCELLED"}

        # Adjust properties of filebrowser panel.
        # TODO: Screen does not update area has no params
        # opsdata.setup_filebrowser_area(area_fb)

        return {"FINISHED"}


prev_file_name: Optional[str] = None


def callback_filename_change(dummy: None):
    global prev_file_name
    area = opsdata.find_area(bpy.context, "FILE_BROWSER")

    # Early return no area.
    if not area:
        return

    params = area.spaces.active.params

    # Early return filename did not change.
    if prev_file_name == params.filename:
        return

    # Update prev_file_name.
    prev_file_name = params.filename
    print(prev_file_name)

    # Execute load media op.
    directory = Path(bpy.path.abspath(params.directory.decode("utf-8")))
    filepath = directory / params.filename
    bpy.ops.video_player.load_media(filepath=filepath.as_posix())


# ----------------REGISTER--------------.


classes = [VP_OT_load_media, VP_OT_toggle_timeline, VP_OT_toggle_filebrowser]
addon_keymap_items = []


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    # Handlers.
    bpy.types.SpaceFileBrowser.draw_handler_add(
        callback_filename_change, (None,), "WINDOW", "POST_PIXEL"
    )

    # Register Hotkeys.
    # Does not work if blender runs in background.
    if not bpy.app.background:
        global addon_keymap_items
        keymap = bpy.context.window_manager.keyconfigs.addon.keymaps.new(name="Window")

        # Toggle Timeline.
        addon_keymap_items.append(
            keymap.keymap_items.new(
                "video_player.toggle_timeline", value="PRESS", type="T"
            )
        )

        # Toggle Filebrowser.
        addon_keymap_items.append(
            keymap.keymap_items.new(
                "video_player.toggle_file_browser", value="PRESS", type="B"
            )
        )
        for kmi in addon_keymap_items:
            logger.info(
                "Registered new hotkey: %s : %s", kmi.type, kmi.properties.bl_rna.name
            )


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    # Handlers.
    bpy.types.SpaceFileBrowser.draw_handler_remove(callback_filename_change, "WINDOW")

    # Unregister Hotkeys.
    # Does not work if blender runs in background.
    if not bpy.app.background:
        global addon_keymap_items
        keymap = bpy.context.window_manager.keyconfigs.addon.keymaps["Window"]

        for kmi in addon_keymap_items:
            logger.info("Remove  hotkey: %s : %s", kmi.type, kmi.properties.bl_rna.name)
            keymap.keymap_items.remove(kmi)

        addon_keymap_items.clear()
