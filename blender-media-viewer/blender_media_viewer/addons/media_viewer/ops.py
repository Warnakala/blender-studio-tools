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

import subprocess
from pathlib import Path
from typing import Set, Union, Optional, List, Dict, Any, Tuple
from collections import OrderedDict
from copy import copy

import bpy
from bpy.app.handlers import persistent

from media_viewer import opsdata, vars, gp_opsdata
from media_viewer.log import LoggerFactory
from media_viewer.states import FileBrowserState

logger = LoggerFactory.getLogger(name=__name__)

# Global variables
active_media_area = "SEQUENCE_EDITOR"

# Global variables for frame handler to check previous value.
prev_dirpath: Path = Path.home()  # TODO: read from json on register
prev_relpath: Optional[str] = None
prev_filepath_list: List[Path] = []

active_dirpath: Path = Path.home()
active_relpath: Optional[str] = None
active_filepath_list: List[Path] = []


filebrowser_state: FileBrowserState = FileBrowserState()
is_fullscreen: bool = False  # TODO: context.screen.show_fullscreen is not updating
is_muted: bool = False
last_folder_at_path: OrderedDict = OrderedDict()
active_bookmark_group_name: str = ""


def get_prev_path() -> Path:
    global prev_relpath
    global prev_dirpath
    return Path(prev_dirpath).joinpath(prev_relpath)


def get_active_path() -> Path:
    global active_dirpath
    global active_relpath
    return Path(active_dirpath).joinpath(active_relpath)


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

        # Check so we don't get index errors later.
        if not filepath_list:
            return {"CANCELLED"}

        # Import sequences.
        for file in filepaths_import:
            frame_start = opsdata.get_last_strip_frame(context)
            # Create new movie strip.
            strip_movie = context.scene.sequence_editor.sequences.new_movie(
                file.stem,
                file.as_posix(),
                3,
                frame_start,
            )
            strip_movie.blend_type = "ALPHA_OVER"

            strip_sound = context.scene.sequence_editor.sequences.new_sound(
                file.stem,
                file.as_posix(),
                2,
                frame_start,
            )

            strip_color = context.scene.sequence_editor.sequences.new_effect(
                file.stem,
                "COLOR",
                1,
                frame_start,
                frame_end=strip_movie.frame_final_end,
            )
            strip_color.color = (0, 0, 0)

        # Set frame range.
        opsdata.fit_frame_range_to_strips(context)

        # Set scene resolution to max width and height to fit all strips.
        strips = opsdata.get_movie_strips(context)
        max_width = max([s.elements[0].orig_width for s in strips])
        max_height = max([s.elements[0].orig_height for s in strips])

        context.scene.render.resolution_x = max_width
        context.scene.render.resolution_y = max_height

        # Adjust view of timeline to fit all.
        opsdata.fit_timeline_view(context)
        opsdata.fit_sqe_preview(context)

        # Update annotation layer.
        # For now let annotation system only work if user selects single
        # movie file. TODO: change layer dynamically when reaching new clip

        # startup.blend contains this layer.
        gp_obj = bpy.data.grease_pencils["SEQUENCE_EDITOR"]

        if len(filepath_list) == 1:
            opsdata.update_gp_object_with_filepath(gp_obj, filepath_list[0])
        else:
            # Hide all gpencil layers.
            for layer in gp_obj.layers:
                layer.annotation_hide = True

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

        # Delete all images. #TODO: caching system? Keeping images might
        # make reloading of previous images faster
        opsdata.del_all_images()

        if self.load_sequence:
            # Detect image sequence.
            file_list = opsdata.get_image_sequence(filepath)
        else:
            file_list = [filepath]

        # Create new image datablock.
        image = bpy.data.images.load(file_list[0].as_posix(), check_existing=True)
        image.name = filepath.stem

        # Set active image.
        area.spaces.active.image = image

        # Fit view, has to be done before setting sequence, otherwise
        # image won't resize? Weird.
        opsdata.fit_image_editor_view(context, area=area)

        # If sequence should be loaded and sequence actually detected
        # set source to SEQUENCE and correct frame range settings
        if self.load_sequence and len(file_list) > 1:

            image.source = "SEQUENCE"

            # Get frame counters from filepaths. Will always work because
            # we already check for image sequence len. Check: opsdata.get_image_sequence
            first_frame = opsdata.get_frame_counter(file_list[0])
            last_frame = opsdata.get_frame_counter(file_list[-1])
            current_frame = opsdata.get_frame_counter(filepath)

            logger.info("Detected image sequence (%s - %s)", first_frame, last_frame)

            context.scene.frame_start = int(first_frame)
            context.scene.frame_end = int(last_frame)

            # Set playhead frame counter of clicked image.
            if current_frame:
                context.scene.frame_current = int(current_frame)

            area.spaces.active.image_user.frame_duration = 5000

        else:
            # Set frame range to 1.
            context.scene.frame_start = 1
            context.scene.frame_end = 1
            context.scene.frame_current = 1

        # Fit timeline view.
        opsdata.fit_timeline_view(context)

        # Set scene resolution.
        context.scene.render.resolution_x = image.resolution[0]
        context.scene.render.resolution_y = image.resolution[1]

        # Set colorspace depending on file extension:
        if file_list[0].suffix == ".exr":
            context.scene.view_settings.view_transform = "Filmic"
            image.use_view_as_render = True
        else:
            context.scene.view_settings.view_transform = "Standard"
            image.use_view_as_render = False

        # Update annotation layer.
        # startup.blend contains this layer.
        gp_obj = bpy.data.grease_pencils["IMAGE_EDITOR"]
        opsdata.update_gp_object_with_filepath(gp_obj, filepath)

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

    def execute(self, context: bpy.types.Context) -> Set[str]:
        global is_fullscreen

        # Don't do anything in fullscreen mode.
        if is_fullscreen:
            return {"CANCELLED"}

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
            area_timeline = opsdata.split_area(
                context, area_media, "DOPESHEET_EDITOR", "HORIZONTAL", self.factor
            )
            opsdata.fit_timeline_view(context)

            # Modify timeline area.
            area_timeline.spaces.active.show_region_header = False
            # area_timeline.spaces.active.show_region_toolbar = False # TODO: does not exist, expose to PythonAPI

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

    def execute(self, context: bpy.types.Context) -> Set[str]:
        global is_fullscreen

        # Don't do anything in fullscreen mode.
        if is_fullscreen:
            # Use own is_fullscreen variable as
            # context.screen.show_fullscreen does not seem to update?
            return {"CANCELLED"}

        global active_media_area
        global filebrowser_state
        global prev_relpath

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

            # Screen must be re-drawn, otherwise space.params is None.
            bpy.ops.wm.redraw_timer(ctx, type="DRAW_WIN_SWAP", iterations=1)

            # Restore previous filebrowser state.
            filebrowser_state.apply_to_area(area_fb)

            # Select previous filepath.
            if prev_relpath:
                area_fb.spaces.active.activate_file_by_relative_path(
                    relative_path=prev_relpath
                )

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

            # Restore previous filebrowser state.
            filebrowser_state.apply_to_area(area_fb)

            # Select previous filepath.
            if prev_relpath:
                area_fb.spaces.active.activate_file_by_relative_path(
                    relative_path=prev_relpath
                )

        elif area_fb:
            # Filebrowser needs to be closed.

            # Save filebrowser state.
            filebrowser_state = FileBrowserState(area=area_fb)

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
        context.preferences.view.show_navigate_ui = False

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

        # Set annotate tool as active.
        if area_media.type in ["SEQUENCE_EDITOR", "IMAGE_EDITOR"]:
            bpy.ops.wm.tool_set_by_id({"area": area_media}, name="builtin.annotate")

        logger.info(f"Changed active media area to: {area_media.type}")

        return {"FINISHED"}


class MV_OT_screen_full_area(bpy.types.Operator):

    bl_idname = "media_viewer.screen_full_area"
    bl_label = "Toggle Fullscreen Area"
    bl_description = "Toggle Fullscreen of active Area"

    def execute(self, context: bpy.types.Context) -> Set[str]:
        global filebrowser_state
        global prev_relpath
        global is_fullscreen

        # Fullscreen area media.
        area_media = opsdata.find_area(context, active_media_area)
        ctx = opsdata.get_context_for_area(area_media)
        bpy.ops.screen.screen_full_area(ctx, use_hide_panels=True)
        is_fullscreen = not is_fullscreen

        # Select previous filepath if in FILE_BROWSER area.
        area_fb = opsdata.find_area(context, "FILE_BROWSER")
        if not is_fullscreen and area_fb:
            if prev_relpath:
                area_fb.spaces.active.activate_file_by_relative_path(
                    relative_path=prev_relpath
                )

        if is_fullscreen:
            # Fit view.
            opsdata.fit_view(context, area_media)

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


class MV_OT_jump_folder_up(bpy.types.Operator):

    bl_idname = "media_viewer.jump_folder_up"
    bl_label = "Folder Up"
    bl_description = "Jumps one folder up in current File Browser directory"

    def execute(self, context: bpy.types.Context) -> Set[str]:
        global last_folder_at_path

        area_fb = opsdata.find_area(context, "FILE_BROWSER")
        if not area_fb:
            return {"CANCELLED"}

        ctx = opsdata.get_context_for_area(area_fb)
        bpy.ops.file.parent(ctx)

        return {"FINISHED"}


class MV_OT_jump_folder_in(bpy.types.Operator):

    bl_idname = "media_viewer.jump_folder_in"
    bl_label = "Folder In"
    bl_description = "Jumps in selected folder in current File Browser directory"

    def execute(self, context: bpy.types.Context) -> Set[str]:
        global prev_relpath
        global last_folder_at_path

        area_fb = opsdata.find_area(context, "FILE_BROWSER")

        # If File Browser area not available.
        if not area_fb:
            return {"CANCELLED"}

        # If no item selected.
        if not prev_relpath:
            return {"CANCELLED"}

        current_dir = Path(area_fb.spaces.active.params.directory.decode("utf-8"))
        new_path = current_dir.joinpath(prev_relpath)

        # Jump in to dir.
        if new_path.exists() and new_path.is_dir():
            area_fb.spaces.active.params.directory = new_path.as_posix().encode("utf-8")

        return {"FINISHED"}


class MV_OT_walk_bookmarks(bpy.types.Operator):

    bl_idname = "media_viewer.walk_bookmarks"
    bl_label = "Walk Bookmarks"
    bl_description = "Walk through bookmarks"

    direction: bpy.props.EnumProperty(
        items=(
            ("UP", "UP", ""),
            ("DOWN", "DOWN", ""),
        ),
        default="DOWN",
    )

    def execute(self, context: bpy.types.Context) -> Set[str]:
        global active_bookmark_group_name
        area_fb = opsdata.find_area(context, "FILE_BROWSER")
        delta = -1 if self.direction == "UP" else 1

        if not area_fb:
            return {"CANCELLED"}

        if not area_fb.spaces.active.show_region_toolbar:
            return {"CANCELLED"}

        # Run Cleanup.
        ctx = opsdata.get_context_for_area(area_fb)
        bpy.ops.file.bookmark_cleanup(ctx)

        # !!!!!
        # The following section is the most stupid code in the universe.
        # !!!!!

        space_fb = area_fb.spaces.active
        bookmark_group_list: List[Tuple] = [
            # (space_fb.system_folders, "system_folders_active"),# Is -1 if nothing is active.
            (space_fb.system_bookmarks, "system_bookmarks_active", "system_bookmarks"),
            (space_fb.bookmarks, "bookmarks_active", "bookmarks"),
            (space_fb.recent_folders, "recent_folders_active", "recent_folders"),
        ]
        bookmark_group_list_index = 0
        active_bookmark_group = None
        active_bookmark_group_index = -1
        active_bookmark_group_idx_attr_name = ""

        for idx, item in enumerate(bookmark_group_list):
            bookmark_group, idx_attr_name, bookmark_group_name = item

            # If prev bookmark group was recent folders, ignore other
            # bookmark groups. This is used to work around the fact that the filebrowser
            # selects all entries that represent the same folder. So if a bookmark is selected
            # that also happens to be in the recent folder section it will select both and set
            # both indexes. With this behavior we would never reach the recent folder section.
            # Thats why we check here if the active_bookmark_group_name is recent folder so we can
            # ignore all other selections.
            if active_bookmark_group_name == "recent_folders":
                if not bookmark_group_name == active_bookmark_group_name:
                    continue

            active_index = getattr(space_fb, idx_attr_name)
            if active_index != -1:
                active_bookmark_group = bookmark_group
                active_bookmark_group_index = active_index
                bookmark_group_list_index = idx
                active_bookmark_group_idx_attr_name = idx_attr_name
                break

        # Check if active_groupmark_group has enough items if we jump to the next index.
        # If not we need to change the active_bookmark_group by choosing the next one on in the
        # bookmarg_group_list.

        # If nothing is active or selected, activate the first index of the first bookmark group.
        if not active_bookmark_group:
            setattr(space_fb, bookmark_group_list[0][1], 0)

        # Catch case jump to next bookmark group.
        elif (active_bookmark_group_index + delta) > len(
            active_bookmark_group.items()
        ) - 1:
            # Choose next item in bookmark group list.
            # Start in the front if we have reached the end of the list.
            if (bookmark_group_list_index + 1) > len(bookmark_group_list) - 1:
                new_boookmark_group_list_index = 0

            # Otherwise just make one step forward.
            else:
                new_boookmark_group_list_index = bookmark_group_list_index + 1

            # Get the new active bookmark group.
            new_active_bookmark_group = bookmark_group_list[
                new_boookmark_group_list_index
            ][0]

            # Get the attr name for set.
            new_active_bookmark_group_idx_attr_name = bookmark_group_list[
                new_boookmark_group_list_index
            ][1]
            # Update the global active bookmark group name.
            active_bookmark_group_name = bookmark_group_list[
                new_boookmark_group_list_index
            ][2]

            # SET
            # As we go DOWN the new index in thew new group will be the first one.
            setattr(space_fb, new_active_bookmark_group_idx_attr_name, 0)

        # Catch case jump to previous bookmark group.
        elif (active_bookmark_group_index + delta) < 0:
            # Choose next item in bookmark group list.
            # Go to the end if we have reached the start of the list.
            if (bookmark_group_list_index - 1) < 0:
                new_boookmark_group_list_index = len(bookmark_group_list) - 1
            # Otherwise just make one step back.
            else:
                new_boookmark_group_list_index = bookmark_group_list_index - 1

            # Get the new active bookmark group.
            new_active_bookmark_group = bookmark_group_list[
                new_boookmark_group_list_index
            ][0]

            # Get the attr name for set.
            new_active_bookmark_group_idx_attr_name = bookmark_group_list[
                new_boookmark_group_list_index
            ][1]

            # Update the global active bookmark group name.
            active_bookmark_group_name = bookmark_group_list[
                new_boookmark_group_list_index
            ][2]

            # SET
            # As we go UP the new index in the new group will be the last one.
            setattr(
                space_fb,
                new_active_bookmark_group_idx_attr_name,
                len(new_active_bookmark_group.items()) - 1,
            )

        # Normal down in same bookmark group.
        elif self.direction == "DOWN":
            # Easiest case just activate next index in same group.
            print(f"Same bookmarkgroup next index: {active_bookmark_group_index+delta}")
            setattr(
                space_fb,
                active_bookmark_group_idx_attr_name,
                (active_bookmark_group_index + delta),
            )

        # Normal up in same bookmark group.
        else:
            # Easiest case just activate previous index in same group.
            print(
                f"Same bookmarkgroup previous index: {active_bookmark_group_index+delta}"
            )
            setattr(
                space_fb,
                active_bookmark_group_idx_attr_name,
                (active_bookmark_group_index + delta),
            )

        return {"FINISHED"}


class MV_OT_animation_play(bpy.types.Operator):

    bl_idname = "media_viewer.animation_play"
    bl_label = "Play"
    bl_description = "Start animation playback"

    def execute(self, context: bpy.types.Context) -> Set[str]:
        global active_media_area
        area_media = opsdata.find_area(context, active_media_area)

        if not area_media:
            return {"CANCELLED"}

        ctx = opsdata.get_context_for_area(area_media)

        bpy.ops.screen.animation_play(ctx)

        return {"FINISHED"}


class MV_OT_next_media_file(bpy.types.Operator):

    bl_idname = "media_viewer.next_media_file"
    bl_label = "Next Media File"
    bl_description = "Load next media file in the current file browser directory"
    direction: bpy.props.EnumProperty(
        items=(
            ("LEFT", "LEFT", ""),
            ("RIGHT", "RIGHT", ""),
            ("UP", "UP", ""),
            ("DOWN", "DOWN", ""),
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
            prev_filepath_abs = get_prev_path()
            try:
                index = file_list.index(prev_filepath_abs)
            except ValueError:
                logger.info(
                    "File %s does not exist anymore", prev_filepath_abs.as_posix()
                )
                next_index = 0

            else:
                # If direction is RIGHT we increment the new index.
                if self.direction in ["RIGHT", "DOWN"]:
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


class MV_OT_set_fb_display_type(bpy.types.Operator):

    bl_idname = "media_viewer.set_fb_display_type"
    bl_label = "Filebrowser Display Type"
    bl_description = "Sets the display type of the File Browser"

    display_type: bpy.props.EnumProperty(
        items=[
            ("LIST_VERTICAL", "LIST_VERTICAL", ""),
            ("LIST_HORIZONTAL", "LIST_HORIZONTAL", ""),
            ("THUMBNAIL", "THUMBNAIL", ""),
        ],
        name="Display Type",
    )

    def execute(self, context: bpy.types.Context) -> Set[str]:
        area_fb = opsdata.find_area(context, "FILE_BROWSER")

        if not area_fb:
            return {"CANCELLED"}

        ctx = opsdata.get_context_for_area(area_fb)

        # Redraw if needed to update params.
        if not area_fb.spaces.active.params:
            bpy.ops.wm.redraw_timer(ctx, type="DRAW_WIN_SWAP", iterations=1)

        # Set display type.
        area_fb.spaces.active.params.display_type = self.display_type

        return {"FINISHED"}


class MV_OT_fit_view(bpy.types.Operator):

    bl_idname = "media_viewer.fit_view"
    bl_label = "Fit view"
    bl_description = "Fits the content of the media area to fill all available space"

    def execute(self, context: bpy.types.Context) -> Set[str]:
        global active_media_area

        # Get media area.
        area_media = opsdata.find_area(context, active_media_area)

        if not area_media:
            return {"CANCELLED"}

        # Fit view.
        opsdata.fit_view(context, area_media)

        return {"FINISHED"}


class MV_OT_toggle_mute_audio(bpy.types.Operator):

    bl_idname = "media_viewer.toggle_mute_audio"
    bl_label = "Mute Audio"
    bl_description = "Toggles mute of all sounds strips"

    def execute(self, context: bpy.types.Context) -> Set[str]:
        global is_muted

        strips = [
            s for s in context.scene.sequence_editor.sequences_all if s.type == "SOUND"
        ]

        for strip in strips:
            strip.mute = not is_muted

        is_muted = not is_muted

        return {"FINISHED"}


class MV_OT_quit_blender(bpy.types.Operator):

    bl_idname = "media_viewer.quit_blender"
    bl_label = "Quit Blender"
    bl_description = "Quits Blender without confirmation"

    def execute(self, context: bpy.types.Context) -> Set[str]:

        # Not 100% sure if this makes a lot of sense.
        # It seems like confirmation dialog does not pop up this way.
        bpy.ops.wm.quit_blender()
        return {"FINISHED"}


class MV_OT_pan_media_view(bpy.types.Operator):

    bl_idname = "media_viewer.pan_media_view"
    bl_label = "Pan Media View"
    bl_description = "Pans the media view by specified delta"

    deltax: bpy.props.IntProperty(name="Delta X")
    deltay: bpy.props.IntProperty(name="Delta Y")

    def execute(self, context: bpy.types.Context) -> Set[str]:
        global active_media_area

        # Find active media area.
        area_media = opsdata.find_area(context, active_media_area)
        if not area_media:
            return {"CANCELLED"}

        if area_media.type == "IMAGE_EDITOR":
            ctx = opsdata.get_context_for_area(area_media)
            bpy.ops.image.view_pan(
                ctx, "EXEC_DEFAULT", offset=(self.deltax, self.deltay)
            )

        elif area_media.type == "SEQUENCE_EDITOR":
            ctx = opsdata.get_context_for_area(area_media, region_type="PREVIEW")
            bpy.ops.view2d.pan(
                ctx, "EXEC_DEFAULT", deltax=self.deltax, deltay=self.deltay
            )

        # Redraw Area.
        area_media.tag_redraw()

        # Reset to default.
        self.deltay = 0
        self.deltax = 0

        return {"FINISHED"}


class MV_OT_zoom_media_view(bpy.types.Operator):

    bl_idname = "media_viewer.zoom_media_view"
    bl_label = "Zoom Media View"
    bl_description = "Zooms media view in specified direction"

    direction: bpy.props.EnumProperty(items=[("IN", "IN", ""), ("OUT", "OUT", "")])

    def execute(self, context: bpy.types.Context) -> Set[str]:
        global active_media_area

        # Find active media area.
        area_media = opsdata.find_area(context, active_media_area)
        if not area_media:
            return {"CANCELLED"}

        if area_media.type == "IMAGE_EDITOR":
            ctx = opsdata.get_context_for_area(area_media)

            if self.direction == "IN":
                bpy.ops.image.view_zoom_in(ctx, "EXEC_DEFAULT", location=(0.5, 0.5))

            elif self.direction == "OUT":
                bpy.ops.image.view_zoom_out(ctx, "EXEC_DEFAULT", location=(0.5, 0.5))

        elif area_media.type == "SEQUENCE_EDITOR":
            ctx = opsdata.get_context_for_area(area_media, region_type="PREVIEW")

            if self.direction == "IN":
                bpy.ops.view2d.zoom_in(ctx, "EXEC_DEFAULT")
            elif self.direction == "OUT":
                bpy.ops.view2d.zoom_out(ctx, "EXEC_DEFAULT")

        # Redraw Area.
        area_media.tag_redraw()

        return {"FINISHED"}


class MV_OT_frame_offset(bpy.types.Operator):

    bl_idname = "media_viewer.frame_offset"
    bl_label = "Frame Offset"
    bl_description = "Offsets current frame by delta amount. Wraps around start and end"

    delta: bpy.props.IntProperty(name="Delta", description="Delta to current frame")

    def execute(self, context: bpy.types.Context) -> Set[str]:
        frame_start = context.scene.frame_start
        frame_end = context.scene.frame_end
        frame_current = context.scene.frame_current

        if frame_current not in range(frame_start, frame_end + 1):
            context.scene.frame_current += self.delta
            return {"FINISHED"}

        # Frame wrap left.
        if frame_current + self.delta < frame_start:
            left_over = (frame_current + self.delta) - frame_start
            context.scene.frame_current = (frame_end + 1) + left_over

        # Frame wrap right.
        elif frame_current + self.delta > frame_end:
            left_over = (frame_current + self.delta) - frame_end
            context.scene.frame_current = (frame_start - 1) + left_over

        else:
            context.scene.frame_current += self.delta

        return {"FINISHED"}


class MV_OT_delete_active_gpencil_frame(bpy.types.Operator):

    bl_idname = "media_viewer.delete_active_gpencil_frame"
    bl_label = "Delete Active Grease Pencil frame"
    bl_description = "Deletes the active frame of the active Grease Pencil layer"

    def execute(self, context: bpy.types.Context) -> Set[str]:
        global active_media_area
        try:
            # Little hack to get the right grease pencil object.
            # In startup.blend we made sure that the gp objects are named after
            # the area type.
            gp_obj = bpy.data.grease_pencils[active_media_area]
        except KeyError:
            return {"CANCELLED"}

        # Get active layer and remove active frame.
        active_layer = gp_obj.layers.active
        if active_layer.active_frame:
            active_layer.frames.remove(active_layer.active_frame)

        return {"FINISHED"}


class MV_OT_delete_all_gpencil_frames(bpy.types.Operator):

    bl_idname = "media_viewer.delete_all_gpencil_frames"
    bl_label = "Delete all Grease Pencil frames"
    bl_description = "Deletes all the frames of the active Grease Pencil layer"

    def execute(self, context: bpy.types.Context) -> Set[str]:
        global active_media_area
        try:
            # Little hack to get the right grease pencil object.
            # In startup.blend we made sure that the gp objects are named after
            # the area type.
            gp_obj = bpy.data.grease_pencils[active_media_area]
        except KeyError:
            return {"CANCELLED"}

        # Delete all frames of active layer.
        for i in reversed(range(len(gp_obj.layers.active.frames))):
            gp_obj.layers.active.frames.remove(gp_obj.layers.active.frames[i])

        return {"FINISHED"}


class MV_OT_insert_empty_gpencil_frame(bpy.types.Operator):

    bl_idname = "media_viewer.insert_empty_gpencil_frame"
    bl_label = "Insert Empty GPencil Frame"
    bl_description = "Inserts an empty GPencil frame at current frame"

    def execute(self, context: bpy.types.Context) -> Set[str]:
        global active_media_area

        # Get active grease pencil layer.
        # startup.blend contains this layer.
        gp_obj = bpy.data.grease_pencils[active_media_area]
        active_layer = gp_obj.layers[gp_obj.layers.active_index]

        # Insert new frame.
        active_layer.frames.new(context.scene.frame_current)

        return {"FINISHED"}


class MV_OT_render_review_sqe_editor(bpy.types.Operator):
    bl_idname = "media_viewer.render_review_sqe_editor"
    bl_label = "Render Review"
    bl_description = (
        "Makes an openGL render of the Sequence Editor. Includes all annotations"
        "Saves file to review_output_path with timestamp. Can render .mp4 of whole"
        "movie strip or single image"
    )
    render_sequence: bpy.props.BoolProperty(
        name="Render Sequence",
        description="Controls if entire movie strip should be rendered or only a single image",
        default=True,
    )
    sequence_file_type: bpy.props.EnumProperty(
        name="File Format",
        items=[("IMAGE", "IMAGE", ""), ("MOVIE", "MOVIE", "")],
        default="MOVIE",
        description="Only works when render_sequence is enabled. Controls if output should be a .mp4 or a jpg sequence",
    )

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        global active_media_area
        return bool(active_media_area in ["SEQUENCE_EDITOR"])

    def execute(self, context: bpy.types.Context) -> Set[str]:
        global prev_relpath  # Is relative path to prev_dirpath.
        global prev_dirpath
        global active_media_area

        # Verify area.
        area_media = opsdata.find_area(context, active_media_area)
        if area_media.type != "SEQUENCE_EDITOR":
            return {"CANCELLED"}

        current_frame = context.scene.frame_current
        media_filepath = get_active_path()
        review_output_dir = Path(context.window_manager.media_viewer.review_output_dir)
        output_path: Path = opsdata.get_review_output_path(
            review_output_dir, media_filepath
        )
        # If sequence and file type MOVIE
        if self.render_sequence and self.sequence_file_type == "MOVIE":

            # Overwrite suffix to be .mp4.
            ext = ".mp4"
            output_path = output_path.parent.joinpath(f"{output_path.stem}{ext}")

            # Set output settings for movie.
            opsdata.set_render_settings_movie(context, output_path)

        # If sequence and file type MOVIE
        elif self.render_sequence and self.sequence_file_type == "IMAGE":
            output_dir: Path = opsdata.get_review_output_path(
                review_output_dir, media_filepath, get_sequence_dir_only=True
            )
            filename = f"{media_filepath.stem}_######.jpg"
            output_path = output_dir.joinpath(filename)

            # Set output settings for movie.
            opsdata.set_render_settings_image_sequence(context, output_path)

        # If single image
        else:
            # Overwrite suffix to be .mp4.
            ext = ".jpg"
            output_path = output_path.parent.joinpath(f"{output_path.stem}{ext}")

        # Ensure folder exists.
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Make opengl render.
        # If animation is False, it will render in bpy.data.images["Render Result"]
        bpy.ops.render.opengl(animation=self.render_sequence, sequencer=True)

        # If not render_sequence we have to save the image manually from Render Result.
        if not self.render_sequence:
            try:
                image = bpy.data.images["Render Result"]
            except KeyError:
                logger.error("Didn't find 'Render Result' in bpy.data.images")
                return {"CANCELLED"}
            else:
                image.save_render(output_path.as_posix())
                print(f"Saved image to: {output_path.as_posix()}")
        else:
            print(f"Saved movie to: {output_path.as_posix()}")

        # Restore current frame.
        context.scene.frame_current = current_frame

        return {"FINISHED"}


class MV_OT_init_with_media_paths(bpy.types.Operator):
    bl_idname = "media_viewer.init_with_media_paths"
    bl_label = "Initialize with media paths"
    bl_description = (
        "Based on input filepath list jumps to right directory "
        "and select active file defined by active_file_idx"
    )
    # This enables us to pass a list of items to the operator input.
    # The list apparently needs to be a list of dictionaries [Dict["name": key]]
    # This operator expects the 'name' key to be the full path.
    files: bpy.props.CollectionProperty(
        type=bpy.types.OperatorFileListElement,
        description="List of filepaths to import in to Sequence Editor",
    )
    active_file_idx: bpy.props.IntProperty(
        name="Index of active file in files list", default=0, min=0
    )

    def execute(self, context: bpy.types.Context) -> Set[str]:
        # No files input nothing to load.
        if not self.files:
            return {"CANCELLED"}

        # Name key is full path.
        filepath_list: List[Path] = [Path(f.name) for f in self.files]

        # Get active filepath.
        try:
            _active_filepath = filepath_list[self.active_file_idx]
        except IndexError:
            # active_file_idx is out of range
            return {"CANCELLED"}

        # Find active media area.
        area_fb = opsdata.find_area(context, "FILE_BROWSER")

        if not area_fb:
            return {"CANCELLED"}

        # Update File Browser directory.
        area_fb.spaces.active.params.directory = (
            _active_filepath.parent.as_posix().encode("utf-8")
        )

        # Select file.
        area_fb.spaces.active.activate_file_by_relative_path(
            relative_path=_active_filepath.name
        )
        return {"FINISHED"}


class MV_OT_export_annotation_data_to_3dcam(bpy.types.Operator):
    bl_idname = "media_viewer.export_annotation_data_to_3dcam"
    bl_label = "Export review to 3D Cam"
    bl_description = (
        "Exports the annotation data in to a blend file. "
        "Converts coordinates of each stroke point. "
        "That way the annotation can be viewed directly in a 3D Camera "
        "that has the same resolution as review media"
    )

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        global active_media_area
        return bool(active_media_area in ["SEQUENCE_EDITOR", "IMAGE_EDITOR"])

    def execute(self, context: bpy.types.Context) -> Set[str]:
        global active_media_area  # :str

        resolution = (
            bpy.context.scene.render.resolution_x,
            bpy.context.scene.render.resolution_y,
        )
        # Check function docstrings for more info.
        v_translate = gp_opsdata.get_translation_vector_to_3dview(
            resolution, active_media_area
        )
        v_scale = gp_opsdata.get_scale_vector_to_3dview(resolution, active_media_area)

        media_filepath = get_prev_path()
        review_output_dir = Path(context.window_manager.media_viewer.review_output_dir)
        output_path: Path = opsdata.get_review_output_path(
            review_output_dir, media_filepath
        )
        output_path = output_path.parent.joinpath(f"{output_path.stem}.blend")

        # Get active greace pencil layer.
        # startup.blend contains this layer.
        gp_obj = bpy.data.grease_pencils[active_media_area]

        # Copy grease pencil object.
        gp_obj_export = gp_obj.copy()
        gp_obj_export.name = "REVIEW"

        # Delete not needed layers.
        active_layer = gp_obj_export.layers[gp_obj_export.layers.active_index]
        for layer in gp_obj_export.layers:
            if layer == active_layer:
                continue
            gp_obj_export.layers.remove(layer)

        # Transform each point coordinate of the gpobj so they can be imported
        # in a 3D_CAMERA_VIEW (That has the same resolution) as the review media and
        # matches perfectly.
        gp_obj_export = gp_opsdata.gplayer_sqe_to_3d(
            gp_obj_export, v_translate, v_scale
        )

        # Create empty library blend file.
        # Write grease pencil data in to it.
        bpy.data.libraries.write(
            output_path.as_posix(),
            {gp_obj_export},
            path_remap="RELATIVE",
            fake_user=True,
            compress=False,
        )

        print(
            f"Exported annotation datablock ({gp_obj_export.name}) to: {output_path.as_posix()}"
        )

        # Delete convert grease pencil object.
        bpy.data.grease_pencils.remove(gp_obj_export)

        return {"CANCELLED"}


class MV_OT_convert_image_seq_to_movie(bpy.types.Operator):
    bl_idname = "media_viewer.convert_image_seq_to_movie"
    bl_label = "Convert Image Sequence to Movie"
    bl_description = (
        "Opens a new Blender instance in the background"
        "that converts the input image sequence in to a movie file."
        "Movie file will be saved one folder up with same name as parent folder"
    )
    filepath: bpy.props.StringProperty(
        name="Filepath",
        description="Filepath to file that is part of image sequence",
        subtype="FILE_PATH",
    )

    def execute(self, context: bpy.types.Context) -> Set[str]:

        if not self.filepath:
            return {"CANCELLED"}

        filepath = Path(self.filepath)
        script_path: Path = vars.TO_MOVIE_SCRIPT_PATH
        blender_exec = Path(bpy.path.abspath(bpy.app.binary_path))

        # Will be one level up, name of folder with .mp4 extension.
        output_path = filepath.parent.parent.joinpath(f"{filepath.parent.name}.mp4")

        if not filepath.exists():
            return {"CANCELLED"}

        filepath_list = opsdata.get_image_sequence(filepath)

        if len(filepath_list) <= 1:
            # Found no image sequence
            return {"CANCELLED"}

        cmd_str = f"{blender_exec.as_posix()} -b --factory-startup -P {script_path.as_posix()} -- {filepath.as_posix()} {output_path.as_posix()}"
        popen = subprocess.Popen(
            cmd_str, shell=True, cwd=Path(__file__).parent.as_posix()
        )
        popen.wait()

        return {"FINISHED"}


@persistent
def callback_filename_change(dummy: None):

    """
    This will be registered as a draw handler on the filebrowser and runs everytime the
    area gets redrawn. This handles the dynamic loading of the selected media and
    saves filebrowser directory on window manager to restore it on area toggling.
    """
    # Read only.
    global last_folder_at_path  # :List[Path]

    # Will be overwritten.
    global active_relpath  # :Optional[str]
    global active_dirpath  # :Path
    global active_filepath_list  # :List[Path]
    global prev_relpath  # :Optional[str]
    global prev_dirpath  # :Path
    global prev_filepath_list  # :List[Path]

    # Because frame handler runs in area,
    # context has active_file, and selected_files.
    area = bpy.context.area
    active_file = bpy.context.active_file  # Can be None.
    selected_files = bpy.context.selected_files
    params = area.spaces.active.params
    directory = Path(bpy.path.abspath(params.directory.decode("utf-8")))

    # Update globals.
    active_dirpath = directory
    active_relpath = active_file.relative_path if active_file else None

    # Save recent directory to config file if direcotry changed.
    # Save and load from folder history.
    if prev_dirpath != active_dirpath:

        # Save recent_dir to config file on disk, to restore it on next
        # startup.
        opsdata.save_to_json(
            {"recent_dir": active_dirpath.as_posix()}, vars.get_config_file()
        )
        logger.info(f"Saved new recent directory: {active_dirpath.as_posix()}")

        # Add previously selected folder to folder history.
        opsdata.add_to_folder_history(
            last_folder_at_path, prev_dirpath.as_posix(), prev_relpath
        )

        # Check if current directory has an entry in folder history.
        # If so select that folder.
        if active_dirpath.as_posix() in last_folder_at_path:
            area.spaces.active.activate_file_by_relative_path(
                relative_path=last_folder_at_path[active_dirpath.as_posix()]
            )

        # Update global var prev_dirpath with current directory.
        prev_dirpath = active_dirpath

    # Early return no active_file:
    if not active_file:
        return

    # When user goes in fullscreen mode and then exits, selected_files will be None
    # And therefore media files will be cleared. Active file tough survives the full
    # screen mode switch. Therefore we can append that to selected files, so we don't
    # loose the loaded media.
    if not selected_files:
        selected_files.append(active_file)

    # Update global active filepath list.
    active_filepath_list.clear()
    active_filepath_list.extend(
        [directory.joinpath(Path(file.relative_path)) for file in selected_files]
    )
    active_filepath = get_active_path()

    # Execute load media op.
    if opsdata.is_movie(active_filepath):
        # Check if active filepath list grew bigger compared to the previous.
        # If so that means, user added more files to existing selection.
        # That means we append the new files to the sequence editor.
        # If the selection shrinked we clear out all media before loading
        # new files

        # Selection did not change, early return.
        if (
            len(active_filepath_list) == len(prev_filepath_list)
            and prev_relpath == active_relpath
        ):
            return None

        append = False
        if len(active_filepath_list) > len(prev_filepath_list):
            append = True

        bpy.ops.media_viewer.set_media_area_type(area_type="SEQUENCE_EDITOR")
        # Operator expects List[Dict] because of collection property.
        bpy.ops.media_viewer.load_media_movie(
            files=[{"name": f.as_posix()} for f in active_filepath_list], append=append
        )

    elif opsdata.is_image(active_filepath):

        # Early return filename did not change.
        if prev_relpath == active_relpath:
            return None

        # Set area type.
        bpy.ops.media_viewer.set_media_area_type(area_type="IMAGE_EDITOR")

        # Load media image handles image sequences.
        bpy.ops.media_viewer.load_media_image(filepath=active_filepath.as_posix())

    elif opsdata.is_text(active_filepath) or opsdata.is_script(active_filepath):

        # Early return filename did not change.
        if prev_relpath == active_relpath:
            return None

        # Set area type.
        bpy.ops.media_viewer.set_media_area_type(area_type="TEXT_EDITOR")

        # Load media.
        bpy.ops.media_viewer.load_media_text(filepath=active_filepath.as_posix())

    # Update prev_ variables.
    prev_relpath = active_relpath
    prev_filepath_list.clear()
    prev_filepath_list.extend(copy(active_filepath_list))


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
    MV_OT_jump_folder_in,
    MV_OT_jump_folder_up,
    MV_OT_animation_play,
    MV_OT_set_fb_display_type,
    MV_OT_fit_view,
    MV_OT_frame_offset,
    MV_OT_toggle_mute_audio,
    MV_OT_walk_bookmarks,
    MV_OT_quit_blender,
    MV_OT_pan_media_view,
    MV_OT_zoom_media_view,
    MV_OT_delete_active_gpencil_frame,
    MV_OT_delete_all_gpencil_frames,
    MV_OT_render_review_sqe_editor,
    MV_OT_init_with_media_paths,
    MV_OT_export_annotation_data_to_3dcam,
    MV_OT_insert_empty_gpencil_frame,
    MV_OT_convert_image_seq_to_movie,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.SpaceFileBrowser.draw_handler_add(
        callback_filename_change, (None,), "WINDOW", "POST_PIXEL"
    )


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    # Handlers.
    bpy.types.SpaceFileBrowser.draw_handler_remove(callback_filename_change, "WINDOW")
