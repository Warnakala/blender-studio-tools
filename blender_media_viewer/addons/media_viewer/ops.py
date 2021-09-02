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

from media_viewer import opsdata, vars
from media_viewer.log import LoggerFactory


logger = LoggerFactory.getLogger(name=__name__)

active_media_area = "SEQUENCE_EDITOR"


class MV_OT_load_media_movie(bpy.types.Operator):

    bl_idname = "media_viewer.load_media_movie"
    bl_label = "Load Movie"
    bl_description = (
        "Loads media in to sequence editor and clears any media before that"
    )

    # This enables us to pass a list of items to the operator input.
    # The list apparently needs to be a list of dictionaries [Dict["name": key]]
    # This operator expects the 'name' key to be the full path.
    files: bpy.props.CollectionProperty(
        type=bpy.types.OperatorFileListElement,
        description="List of filepaths to import in to Sequence Editor",
    )

    playback: bpy.props.BoolProperty(
        name="Playback",
        description="Controls if video should playback after load",
        default=True,
    )
    append: bpy.props.BoolProperty(
        name="Append File",
        description=(
            "Controls if all strips should be deleted "
            "or new strip should be appended to timeline"
        ),
        default=False,
    )

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return True

    def execute(self, context: bpy.types.Context) -> Set[str]:
        frame_start = context.scene.frame_start

        # print([f.name for f in self.files])

        # Filter out all non movie files.
        filepath_list: List[Path] = []
        for f in self.files:
            # Name key is full path.
            p = Path(f.name)
            if opsdata.is_movie(p):
                filepath_list.append(p)

        filepaths_import: List[Path] = []

        # Init Sequence Editor.
        if not context.scene.sequence_editor:
            context.scene.sequence_editor_create()

        # Stop can_playback.
        bpy.ops.screen.animation_cancel()

        if self.append:
            # Append strips, check which ones are already in sqe
            loaded_files = opsdata.get_loaded_movie_sound_strip_paths(context)
            filepaths_import.extend([f for f in filepath_list if f not in loaded_files])

        else:
            # Clear all media in the sequence editor.
            opsdata.del_all_sequences(context)
            filepaths_import.extend(filepath_list)

        # Import sequence.

        # Handle movie files.
        for file in filepaths_import:
            frame_start = opsdata.get_last_strip_frame(context)
            # Create new movie strip.
            strip = context.scene.sequence_editor.sequences.new_movie(
                file.stem,
                file.as_posix(),
                0,
                frame_start,
            )

        # Set frame range.
        opsdata.fit_frame_range_to_strips(context)

        # Adjust view of timeline to fit all.
        opsdata.fit_timeline_view(context)

        # Set playhead to start of scene.
        context.scene.frame_current = context.scene.frame_start

        # Playback.
        if self.playback:
            bpy.ops.screen.animation_play()

        return {"FINISHED"}


class MV_OT_load_media_image(bpy.types.Operator):

    bl_idname = "media_viewer.load_media_image"
    bl_label = "Load Image"
    bl_description = (
        "Loads image media in to image editor and clears any media before that"
    )
    filepath: bpy.props.StringProperty(name="Filepath", subtype="FILE_PATH")
    load_sequence: bpy.props.BoolProperty(
        name="Load Sequence",
        description="Controls if operator should search for an image sequence and load it",
        default=True,
    )
    playback: bpy.props.BoolProperty(
        name="Playback",
        description="Controls if image sequence should playback after load",
        default=True,
    )

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return True

    def execute(self, context: bpy.types.Context) -> Set[str]:
        filepath = Path(self.filepath)
        can_playback = False

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

        if self.load_sequence:
            # Detect image sequence.
            file_list = opsdata.get_image_sequence(filepath)
        else:
            file_list = [filepath]

        # Create new image datablock.
        image = bpy.data.images.load(file_list[0].as_posix(), check_existing=True)
        image.name = filepath.stem

        # If sequence should be loaded and sequence actually detected
        # set source to SEQUENCE and correct frame range settings
        if self.load_sequence and len(file_list) > 1:

            image.source = "SEQUENCE"

            first_frame = opsdata.get_frame_counter(file_list[0])
            last_frame = opsdata.get_frame_counter(file_list[-1])
            current_frame = opsdata.get_frame_counter(filepath)

            if all([first_frame, last_frame]):
                context.scene.frame_start = int(first_frame)
                context.scene.frame_end = int(last_frame)
                can_playback = True

                # Set playhead frame counter of clicked image.
                if current_frame:
                    context.scene.frame_current = int(current_frame)

            area.spaces.active.image_user.frame_duration = 5000

        # image.colorspace_settings.name = "Linear"

        # Set active image.
        area.spaces.active.image = image

        # Playback.
        if can_playback and self.playback:
            pass
            # TODO: does not seem to trigger playback in image editor
            # bpy.ops.screen.animation_play()

        return {"FINISHED"}


class MV_OT_load_media_text(bpy.types.Operator):

    bl_idname = "media_viewer.load_media_text"
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


class MV_OT_toggle_timeline(bpy.types.Operator):

    bl_idname = "media_viewer.toggle_timeline"
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


class MV_OT_toggle_filebrowser(bpy.types.Operator):

    bl_idname = "media_viewer.toggle_filebrowser"
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


class MV_OT_load_recent_dir(bpy.types.Operator):

    bl_idname = "media_viewer.load_recent_directory"
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


class MV_OT_set_template_defaults(bpy.types.Operator):
    bl_idname = "media_viewer.set_template_defaults"
    bl_label = "Set Template Defaults"
    bl_description = (
        "Sets default values that can't be saved in userpref.blend or startup.blend"
    )

    def execute(self, context: bpy.types.Context) -> Set[str]:
        area_fb = opsdata.find_area(context, "FILE_BROWSER")

        # Set scene settings.
        context.scene.view_settings.view_transform = "Standard"

        # Set preference settings.
        context.preferences.view.show_navigate_ui = False
        context.preferences.view.show_layout_ui = False

        # Find filebrowser area.
        if area_fb:
            # Set filebrowser settings.
            opsdata.setup_filebrowser_area(area_fb)

        logger.info("Set app template defaults")

        return {"FINISHED"}


class MV_OT_set_media_area_type(bpy.types.Operator):

    bl_idname = "media_viewer.set_media_area_type"
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
prev_filepath: Optional[str] = None
prev_dirpath: Path = Path.home()  # TODO: read from json on register
prev_filepath_list: List[Path] = []


@persistent
def callback_filename_change(dummy: None):
    global prev_filepath
    global prev_dirpath

    # Because frame handler runs in area,
    # context has active_file, and selected_files.
    area = bpy.context.area
    params = area.spaces.active.params
    directory = Path(bpy.path.abspath(params.directory.decode("utf-8")))
    active_file = bpy.context.active_file  # Can be None.
    selected_files = bpy.context.selected_files

    # Save recent directory to config file if direcotry changed.
    if prev_dirpath != directory:
        opsdata.save_to_json(
            {"recent_dir": directory.as_posix()}, vars.get_config_file()
        )
        logger.info(f"Saved new recent directory: {directory.as_posix()}")
        prev_dirpath = directory

    # Early return no active_file:
    if not active_file:
        return

    # print(active_file)
    # print(selected_files)

    # Assemble Path data structures.
    filepath = directory.joinpath(Path(active_file.relative_path))
    filepath_list: List[Path] = [
        directory.joinpath(Path(file.relative_path)) for file in selected_files
    ]

    # Execute load media op.
    if opsdata.is_movie(filepath):
        # Check if active filepath list grew bigger compared to the previous.
        # If so that means, user added more files to existing selection.
        # That means we append the new files to the sequence editor.
        # If the selection shrinked we clear out all media before loading
        # new files

        # Selection did not change, early return.
        if (
            len(filepath_list) == len(prev_filepath_list)
            and prev_filepath == active_file.relative_path
        ):
            return

        append = False
        if len(filepath_list) > len(prev_filepath_list):
            append = True

        bpy.ops.media_viewer.set_media_area_type(area_type="SEQUENCE_EDITOR")
        # Operator expects List[Dict] because of collection property.
        bpy.ops.media_viewer.load_media_movie(
            files=[{"name": f.as_posix()} for f in filepath_list], append=append
        )

    elif opsdata.is_image(filepath):

        # Early return filename did not change.
        if prev_filepath == active_file.relative_path:
            return

        bpy.ops.media_viewer.set_media_area_type(area_type="IMAGE_EDITOR")
        # Load media image handles image sequences.
        bpy.ops.media_viewer.load_media_image(filepath=filepath.as_posix())

    elif opsdata.is_text(filepath) or opsdata.is_script(filepath):

        # Early return filename did not change.
        if prev_filepath == active_file.relative_path:
            return

        bpy.ops.media_viewer.set_media_area_type(area_type="TEXT_EDITOR")
        bpy.ops.media_viewer.load_media_text(filepath=filepath.as_posix())

    # Update prev_ variables.
    prev_filepath = active_file.relative_path
    prev_filepath_list.clear()
    prev_filepath_list.extend(filepath_list)


# ----------------REGISTER--------------.


classes = [
    MV_OT_load_media_movie,
    MV_OT_load_media_image,
    MV_OT_toggle_timeline,
    MV_OT_toggle_filebrowser,
    MV_OT_load_recent_dir,
    MV_OT_set_media_area_type,
    MV_OT_set_template_defaults,
    MV_OT_load_media_text,
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
                "media_viewer.toggle_timeline", value="PRESS", type="T"
            )
        )

        # Toggle Filebrowser.
        addon_keymap_items.append(
            keymap.keymap_items.new(
                "media_viewer.toggle_file_browser", value="PRESS", type="B"
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
