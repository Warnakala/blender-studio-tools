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

# Global variables
active_media_area = "SEQUENCE_EDITOR"

# Global variables for frame handler to check previous value.
prev_relpath: Optional[str] = None
prev_dirpath: Path = Path.home()  # TODO: read from json on register
prev_filepath_list: List[Path] = []


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
        opsdata.fit_sqe_preview(context)

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

            logger.info("Detected image sequence (%s - %s)", first_frame, last_frame)

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

        # Fit view.
        opsdata.fit_image_editor_view(context)

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
        global active_media_area

        area_media = opsdata.find_area(context, active_media_area)
        area_timeline = opsdata.find_area(context, "DOPESHEET_EDITOR")

        if area_timeline:
            # Timeline needs to be closed.
            opsdata.close_area(area_timeline)
            logger.info("Hide timeline")

        elif area_media:
            # Media area needs to be splitted.
            # New area needs to be timeline
            opsdata.split_area(
                context, area_media, "DOPESHEET_EDITOR", "HORIZONTAL", self.factor
            )
            opsdata.fit_timeline_view(context)
            logger.info("Show timeline")

        else:
            logger.error(
                "Toggle timeline failed. Missing areas: %s | DOPESHEET_EDITOR",
                active_media_area,
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
        global active_media_area

        area_media = opsdata.find_area(context, active_media_area)
        area_fb = opsdata.find_area(context, "FILE_BROWSER")
        area_time = opsdata.find_area(context, "DOPESHEET_EDITOR")
        screen_name = context.screen.name
        wm_name = context.window_manager.name

        if not area_fb and area_time and area_media:
            # If sqe and timeline visible but not filebrowser
            # we need to first close timeline and then open it after to
            # get correct layout.
            opsdata.close_area(area_time)

            # We need to do some custom context assembly here
            # because the bpy.ops.screen.area_close() sets context.screen to NULL.
            screen = bpy.data.screens[screen_name]
            ctx = opsdata.get_context_for_area(area_media)
            ctx["screen"] = screen
            ctx["window"] = bpy.data.window_managers[wm_name].windows[0]

            # Open filebrowser.
            area_fb = opsdata.split_area(
                ctx, area_media, "FILE_BROWSER", "VERTICAL", self.factor_filebrowser
            )

            # Screen must be re-drawn, otherwise space.params is None
            bpy.ops.wm.redraw_timer(ctx, type="DRAW_WIN_SWAP", iterations=1)

            # Load prev filebrowser dir from win manager
            opsdata.load_filebrowser_dir_from_win_manager(area_fb)

            # Adjust properties of filebrowser panel.
            opsdata.setup_filebrowser_area(area_fb)

            # Open timeline
            area_time = opsdata.split_area(
                ctx, area_media, "DOPESHEET_EDITOR", "HORIZONTAL", self.factor_timeline
            )

            logger.info("Show filebrowser")

        elif not area_fb:
            # Media area needs to be splitted.
            # New area needs to be filebrowser.
            area_fb = opsdata.split_area(
                context, area_media, "FILE_BROWSER", "VERTICAL", self.factor_filebrowser
            )
            logger.info("Show filebrowser")

            # Screen must be re-drawn, otherwise space.params is None
            bpy.ops.wm.redraw_timer(type="DRAW_WIN_SWAP", iterations=1)

            # Load prev filebrowser dir from win manager
            opsdata.load_filebrowser_dir_from_win_manager(area_fb)

            # Adjust properties of filebrowser panel.
            opsdata.setup_filebrowser_area(area_fb)

        elif area_fb:
            # Filebrowser needs to be closed.

            # Save directory to a custom property so it can be restored later.
            # For example in toggling filebrowser window.
            params = area_fb.spaces.active.params
            bpy.context.window_manager["directory"] = params.directory.decode("utf-8")

            opsdata.close_area(area_fb)
            logger.info("Hide filebrowser")
            return {"FINISHED"}

        else:
            logger.error(
                "Toggle timeline failed. Missing areas: %s | FILE_BROWSER",
                active_media_area,
            )
            return {"CANCELLED"}

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
        context.preferences.use_preferences_save = False
        context.preferences.view.show_playback_fps = False
        context.preferences.view.show_view_name = False
        context.preferences.view.show_object_info = False

        # Dedicated apps settings.
        apps = context.preferences.apps
        apps.show_corner_split = False
        apps.show_regions_visibility_toggle = False
        # apps.show_edge_resize = False

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


class MV_OT_screen_full_area(bpy.types.Operator):

    bl_idname = "media_viewer.screen_full_area"
    bl_label = "Toggle Fullscreen Area"
    bl_description = "Toggle Fullscreen of active Area"

    def execute(self, context: bpy.types.Context) -> Set[str]:
        # TODO: only fullscreen media area
        bpy.ops.screen.screen_full_area(use_hide_panels=True)
        return {"FINISHED"}


class MV_OT_toggle_fb_region_toolbar(bpy.types.Operator):

    bl_idname = "media_viewer.toggle_fb_region_toolbar"
    bl_label = "Toggle Filebrowser Toolbar"
    bl_description = "Toggle Filebrowser Toolbar"

    def execute(self, context: bpy.types.Context) -> Set[str]:
        area_fb = opsdata.find_area(context, "FILE_BROWSER")
        if not area_fb:
            return {"CANCELLED"}

        # Invert current value.
        area_fb.spaces.active.show_region_toolbar = (
            not area_fb.spaces.active.show_region_toolbar
        )
        return {"FINISHED"}


class MV_OT_next_media_file(bpy.types.Operator):

    bl_idname = "media_viewer.next_media_file"
    bl_label = "Next Media File"
    bl_description = "Load next media file in the current file browser directory"
    direction: bpy.props.EnumProperty(
        items=(
            ("LEFT", "LEFT", ""),
            ("RIGHT", "RIGHT", ""),
        ),
        default="RIGHT",
    )

    def execute(self, context: bpy.types.Context) -> Set[str]:
        global prev_relpath  # Is relative path to prev_dirpath.
        global prev_dirpath
        area_fb = opsdata.find_area(context, "FILE_BROWSER")

        if not context.screen.show_fullscreen and area_fb:
            # If not fullscreen, just call select_wall op
            area_fb = opsdata.find_area(context, "FILE_BROWSER")
            ctx = opsdata.get_context_for_area(area_fb)
            bpy.ops.file.select_walk(ctx, "INVOKE_DEFAULT", direction=self.direction)
            return {"FINISHED"}

        # Get all files and folders and sort them alphabetically.
        file_list = [
            p for p in Path(prev_dirpath).iterdir() if not p.name.startswith(".")
        ]
        if not file_list:
            logger.info("Empty directory: %s", prev_dirpath.as_posix())
            return {"CANCELLED"}

        file_list.sort(key=lambda p: p.name)

        # If there was not previous filepath take the first file.
        if not prev_relpath:
            filepath = file_list[0]

        # If previous filepath, get index of that and take next index.
        else:
            prev_filepath_abs = Path(prev_dirpath).joinpath(prev_relpath)
            try:
                index = file_list.index(prev_filepath_abs)
            except ValueError:
                logger.info(
                    "File %s does not exist anymore", prev_filepath_abs.as_posix()
                )
                next_index = 0

            else:
                # If direction is RIGHT we increment the new index.
                if self.direction == "RIGHT":
                    next_index = index + 1

                    # If index is last index, go to the beginning.
                    if next_index > (len(file_list) - 1):
                        next_index = 0

                # If direction is LEFT we decrement the new index.
                else:
                    next_index = index - 1

                    # If index is first index, go to the end.
                    if next_index < 0:
                        next_index = len(file_list) - 1

            filepath = file_list[next_index]

        # Load file in media viewer.
        logger.info(f"Loading file: {filepath.as_posix()}")

        # Execute load media op.
        if opsdata.is_movie(filepath):
            bpy.ops.media_viewer.set_media_area_type(area_type="SEQUENCE_EDITOR")
            # Operator expects List[Dict] because of collection property.
            bpy.ops.media_viewer.load_media_movie(
                files=[{"name": filepath.as_posix()}], append=False
            )

        elif opsdata.is_image(filepath):
            bpy.ops.media_viewer.set_media_area_type(area_type="IMAGE_EDITOR")
            # Load media image handles image sequences.
            bpy.ops.media_viewer.load_media_image(filepath=filepath.as_posix())

        elif opsdata.is_text(filepath) or opsdata.is_script(filepath):
            bpy.ops.media_viewer.set_media_area_type(area_type="TEXT_EDITOR")
            bpy.ops.media_viewer.load_media_text(filepath=filepath.as_posix())

        # Update prev_ variables.
        prev_relpath = filepath.relative_to(Path(prev_dirpath)).as_posix()
        return {"FINISHED"}


@persistent
def callback_filename_change(dummy: None):

    """
    This will be registered as a draw handler on the filebrowser and runs everytime the
    area gets redrawn. This handles the dynamic loading of the selected media and
    saves filebrowser directory on window manager to restore it on area toggling.
    """
    global prev_relpath
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

    # When user goes in fullscreen mode and then exits, selected_files will be None
    # And therefore media files will be cleared. Active file tough survives the full
    # screen mode switch. Therefore we can append that to selected files, so we don't
    # loose the loaded media.
    if not selected_files:
        selected_files.append(active_file)

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
            and prev_relpath == active_file.relative_path
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
        if prev_relpath == active_file.relative_path:
            return

        bpy.ops.media_viewer.set_media_area_type(area_type="IMAGE_EDITOR")
        # Load media image handles image sequences.
        bpy.ops.media_viewer.load_media_image(filepath=filepath.as_posix())

    elif opsdata.is_text(filepath) or opsdata.is_script(filepath):

        # Early return filename did not change.
        if prev_relpath == active_file.relative_path:
            return

        bpy.ops.media_viewer.set_media_area_type(area_type="TEXT_EDITOR")
        bpy.ops.media_viewer.load_media_text(filepath=filepath.as_posix())

    # Update prev_ variables.
    prev_relpath = active_file.relative_path
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
    MV_OT_screen_full_area,
    MV_OT_next_media_file,
    MV_OT_toggle_fb_region_toolbar,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    # Handlers.
    bpy.types.SpaceFileBrowser.draw_handler_add(
        callback_filename_change, (None,), "WINDOW", "POST_PIXEL"
    )


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    # Handlers.
    bpy.types.SpaceFileBrowser.draw_handler_remove(callback_filename_change, "WINDOW")
