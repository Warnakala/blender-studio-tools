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
from bpy.app.handlers import persistent

from video_player import opsdata, vars
from video_player.log import LoggerFactory


logger = LoggerFactory.getLogger(name=__name__)

active_media_area = "SEQUENCE_EDITOR"


class VP_OT_load_media_movie(bpy.types.Operator):

    bl_idname = "video_player.load_media_movie"
    bl_label = "Load Media"
    bl_description = (
        "Loads media in to sequence editor and clears any media before that"
    )
    filepath: bpy.props.StringProperty(name="Filepath", subtype="FILE_PATH")
    playback: bpy.props.BoolProperty(
        name="Playback",
        description="Controls if video should playback after load",
        default=True,
    )

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return True

    def execute(self, context: bpy.types.Context) -> Set[str]:
        filepath = Path(self.filepath)
        can_playback = False

        # Check if filepath exists.
        if not filepath.exists():
            return {"CANCELLED"}

        # Init Sequence Editor.
        if not context.scene.sequence_editor:
            context.scene.sequence_editor_create()

        # Check if sequence editor area available.
        area = opsdata.find_area(context, "SEQUENCE_EDITOR")
        if not area:
            logger.error(
                "Failed to load movie media. No Sequence Editor area available."
            )
            return {"CANCELLED"}

        # Stop can_playback.
        bpy.ops.screen.animation_cancel()

        # Clear all media in the sequence editor.
        opsdata.del_all_sequences(context)

        # Import sequence.

        # Handle movie files.
        if opsdata.is_movie(filepath):

            # Create new movie strip.
            strip = context.scene.sequence_editor.sequences.new_movie(
                filepath.stem,
                filepath.as_posix(),
                0,
                context.scene.frame_start,
            )
            can_playback = True

        # Handle image files.
        elif opsdata.is_image(filepath):

            # Create new image strip.
            strip = context.scene.sequence_editor.sequences.new_image(
                filepath.stem,
                filepath.as_posix(),
                0,
                context.scene.frame_start,
            )
            can_playback = False

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
        if can_playback:
            if self.playback:
                bpy.ops.screen.animation_play()

        return {"FINISHED"}


class VP_OT_load_media_image(bpy.types.Operator):

    bl_idname = "video_player.load_media_image"
    bl_label = "Load Image"
    bl_description = (
        "Loads image media in to image editor and clears any media before that"
    )
    filepath: bpy.props.StringProperty(name="Filepath", subtype="FILE_PATH")

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return True

    def execute(self, context: bpy.types.Context) -> Set[str]:
        filepath = Path(self.filepath)

        # Stop playback.
        bpy.ops.screen.animation_cancel()

        # Check if filepath exists.
        if not filepath.exists():
            return {"CANCELLED"}

        # Check if image editor area available.
        area = opsdata.find_area(context, "IMAGE_EDITOR")
        if not area:
            logger.error("Failed to load image media. No Image Editor area available.")
            return {"CANCELLED"}

        # Delete all images.
        opsdata.del_all_images()

        # Create new image datablock.
        image = bpy.data.images.load(filepath.as_posix(), check_existing=True)
        image.name = filepath.stem
        # image.source = "SEQUENCE"
        # image.colorspace_settings.name = "Linear"

        # Set active image.
        area.spaces.active.image = image
        # area.spaces.active.image_user.frame_duration = 5000
        # area.spaces.active.image_user.frame_offset = offset

        return {"FINISHED"}


class VP_OT_load_media_text(bpy.types.Operator):

    bl_idname = "video_player.load_media_text"
    bl_label = "Load Text"
    bl_description = (
        "Loads text media in to text editor and clears any text media before that"
    )
    filepath: bpy.props.StringProperty(name="Filepath", subtype="FILE_PATH")

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return True

    def execute(self, context: bpy.types.Context) -> Set[str]:
        filepath = Path(self.filepath)

        # Stop playback.
        bpy.ops.screen.animation_cancel()

        # Check if filepath exists.
        if not filepath.exists():
            return {"CANCELLED"}

        # Check if text editor is available.
        area = opsdata.find_area(context, "TEXT_EDITOR")
        if not area:
            logger.error("Failed to load text media. No Text Editor area available.")
            return {"CANCELLED"}

        # Delete all texts.
        opsdata.del_all_texts()

        # Create new text datablock.
        text = bpy.data.texts.load(filepath.as_posix())
        text.name = filepath.stem

        # Set active text.
        area.spaces.active.text = text

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


class VP_OT_load_recent_dir(bpy.types.Operator):

    bl_idname = "video_player.load_recent_directory"
    bl_label = "Load Recent Directory"
    bl_description = "Loads the recent directory that is saved in the config file"

    def execute(self, context: bpy.types.Context) -> Set[str]:
        # Load last filebrowser path.
        area_fb = opsdata.find_area(context, "FILE_BROWSER")
        if not area_fb:
            logger.info("No filebrowser area to load recent directory")
            return {"CANCELLED"}

        opsdata.load_filebrowser_dir_from_config_file(area_fb)

        return {"FINISHED"}

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event) -> Set[str]:
        # Ensure config file exists.
        opsdata.ensure_config_file()
        return self.execute(context)


class VP_OT_set_template_defaults(bpy.types.Operator):
    bl_idname = "video_player.set_template_defaults"
    bl_label = "Set Template defaults"
    bl_description = (
        "Sets default values that can't be saved in userpref.blend or startup.blend"
    )

    def execute(self, context: bpy.types.Context) -> Set[str]:
        area_fb = opsdata.find_area(context, "FILE_BROWSER")

        # Find filebrowser area.
        if area_fb:
            opsdata.setup_filebrowser_area(area_fb)
        return {"FINISHED"}


class VP_OT_set_media_area_type(bpy.types.Operator):

    bl_idname = "video_player.set_media_area_type"
    bl_label = "Set media area type"
    bl_description = "Sets media are type to specified area type"

    area_type: bpy.props.StringProperty(
        name="Area Type",
        description="Type that media area should be changed to",
        default="SEQUENCE_EDITOR",
    )

    def execute(self, context: bpy.types.Context) -> Set[str]:
        global active_media_area

        # Find active media area.
        area_media = opsdata.find_area(context, active_media_area)

        if not area_media:
            logger.info(
                f"Failed to find active media area of type: {active_media_area}"
            )
            return {"CANCELLED"}

        # Early return if same type already.
        if area_media.type == self.area_type:
            return {"FINISHED"}

        # Change area type.
        area_media.type = self.area_type

        # Update global media area type.
        active_media_area = area_media.type

        logger.info(f"Changed active media area to: {area_media.type}")
        return {"FINISHED"}


# Global variables for frame handler to check previous value.
prev_file_name: Optional[str] = None
prev_dir_path: Path = Path.home()


@persistent
def callback_filename_change(dummy: None):
    global prev_file_name
    global prev_dir_path

    area = opsdata.find_area(bpy.context, "FILE_BROWSER")

    # Early return no area.
    if not area:
        return

    params = area.spaces.active.params
    directory = Path(bpy.path.abspath(params.directory.decode("utf-8")))

    # Save recent directory to config file if direcotry changed.
    if prev_dir_path != directory:
        opsdata.save_to_json(
            {"recent_dir": directory.as_posix()}, vars.get_config_file()
        )
        logger.info(f"Saved new recent directory: {directory.as_posix()}")
        prev_dir_path = directory

    # Early return filename did not change.
    if prev_file_name == params.filename:
        return

    # Update prev_file_name.
    prev_file_name = params.filename

    filepath = directory.joinpath(params.filename)

    # Execute load media op.
    if opsdata.is_movie(filepath):
        bpy.ops.video_player.set_media_area_type(area_type="SEQUENCE_EDITOR")
        bpy.ops.video_player.load_media_movie(filepath=filepath.as_posix())

    elif opsdata.is_image(filepath):
        bpy.ops.video_player.set_media_area_type(area_type="IMAGE_EDITOR")
        bpy.ops.video_player.load_media_image(filepath=filepath.as_posix())

    elif opsdata.is_text(filepath) or opsdata.is_script(filepath):
        bpy.ops.video_player.set_media_area_type(area_type="TEXT_EDITOR")
        bpy.ops.video_player.load_media_text(filepath=filepath.as_posix())


# ----------------REGISTER--------------.


classes = [
    VP_OT_load_media_movie,
    VP_OT_load_media_image,
    VP_OT_toggle_timeline,
    VP_OT_toggle_filebrowser,
    VP_OT_load_recent_dir,
    VP_OT_set_media_area_type,
    VP_OT_set_template_defaults,
    VP_OT_load_media_text,
]
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
