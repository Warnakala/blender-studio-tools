import math
from pathlib import Path
from typing import Set, Union, Optional, List, Dict, Any, Tuple

import bpy

from contactsheet import prefs, opsdata
from contactsheet.log import LoggerFactory
from contactsheet.geo_seq import SequenceRect
from contactsheet.geo import Grid, NestedRectangle

logger = LoggerFactory.getLogger(name=__name__)


class CS_OT_make_contactsheet(bpy.types.Operator):
    """
    This operator creates a contactsheet out of the selected sequence strips.
    The contactsheet will be created in a separate scene.
    """

    bl_idname = "contactsheet.make_contactsheet"
    bl_label = "Make Contact Sheet"
    bl_description = (
        "Creates a temporary scene and arranges the previously selected sequences in a grid. "
        "If no sequences were selected it takes a continuous row of the top most sequences."
    )

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return opsdata.poll_make_contactsheet(context)

    def execute(self, context: bpy.types.Context) -> Set[str]:

        addon_prefs = prefs.addon_prefs_get(context)

        # Gather sequences to process.
        sequences = context.selected_sequences
        if not sequences:
            # If nothing selected take a continuous row of the top most sequences.
            sequences = opsdata.get_top_level_valid_strips_continuous(context)
        else:
            sequences = opsdata.get_valid_cs_sequences(sequences)

        # Select sequences, will remove sequences later that are not selected.
        bpy.ops.sequencer.select_all(action="DESELECT")
        for s in sequences:
            s.select = True

        row_count = None
        start_frame = 1

        # Get contactsheet metadata.
        sqe_editor = opsdata.get_sqe_editor(context)
        orig_proxy_render_size = sqe_editor.spaces.active.proxy_render_size
        orig_use_proxies = sqe_editor.spaces.active.use_proxies

        # Create new scene.
        scene_orig = bpy.context.scene
        bpy.ops.scene.new(type="FULL_COPY")  # Changes active scene, makes copy.
        scene_tmp = bpy.context.scene
        scene_tmp.name = "contactsheet"
        logger.info("Created temporary scene for contactsheet: %s", scene_tmp.name)

        # Save contactsheet metadata.
        sqe_editor = opsdata.get_sqe_editor(context)
        sqe_editor.spaces.active.proxy_render_size = "PROXY_25"
        sqe_editor.spaces.active.use_proxies = True
        scene_tmp.contactsheet.is_contactsheet = True
        scene_tmp.contactsheet.contactsheet_meta.scene = scene_orig
        scene_tmp.contactsheet.contactsheet_meta.use_proxies = orig_use_proxies
        scene_tmp.contactsheet.contactsheet_meta.proxy_render_size = (
            orig_proxy_render_size
        )

        # Remove sequences in new scene that are not selected.
        seq_rm: List[bpy.types.Sequence] = [
            s for s in scene_tmp.sequence_editor.sequences_all if not s.select
        ]
        for s in seq_rm:
            scene_tmp.sequence_editor.sequences.remove(s)

        # Get all sequences in new scene and sort them.
        sequences = list(scene_tmp.sequence_editor.sequences_all)
        sequences.sort(key=lambda strip: (strip.frame_final_start, strip.channel))

        # Place black color strip in channel 1.
        color_strip = context.scene.sequence_editor.sequences.new_effect(
            "background", "COLOR", 1, start_frame, frame_end=start_frame + 1
        )
        color_strip.color = (0, 0, 0)

        # Create required number of metastrips to workaround the limit of 32 channels.
        nr_of_metastrips = math.ceil(len(sequences) / 32)
        metastrips: List[bpy.types.MetaSequence] = []
        for i in range(nr_of_metastrips):
            channel = i + 2
            meta_strip = context.scene.sequence_editor.sequences.new_meta(
                f"contactsheet_meta_{channel-1}", channel, start_frame
            )
            metastrips.append(meta_strip)
            logger.debug("Created metastrip: %s", meta_strip.name)

        # Move sequences in to metastrips, place them on top of each other
        # make them start at the same frame.
        for idx, seq in enumerate(sequences):
            # Move to metastrip.
            channel = idx + 1
            meta_index = math.floor(idx / 32)
            seq.move_to_meta(metastrips[meta_index])

            # Set seq properties inside metastrip.
            seq.channel = channel - ((meta_index) * 32)
            seq.frame_start = start_frame
            seq.blend_type = "ALPHA_OVER"

        # Elongate all strips to the strip with the longest duration.
        tmp_sequences = sorted(sequences, key=lambda s: s.frame_final_end)
        tmp_sequences.insert(0, color_strip)
        max_end: int = tmp_sequences[-1].frame_final_end
        for strip in tmp_sequences:
            if strip.frame_final_end < max_end:
                strip.frame_final_end = max_end

        # Clip the metastrip frame end at max end and set alpha over.
        for strip in metastrips:
            strip.frame_start = start_frame
            strip.frame_final_end = max_end
            strip.blend_type = "ALPHA_OVER"

        # Scene settings.
        # Change frame range and frame start.
        self.set_render_settings(context)
        self.set_output_path(context)
        self.set_sqe_area_settings(context)

        # Create content list for grid.
        sqe_rects: List[SequenceRect] = [SequenceRect(seq) for seq in sequences]
        content: List[NestedRectangle] = [
            NestedRectangle(0, 0, srect.width, srect.height, child=srect)
            for srect in sqe_rects
        ]

        # Create grid.
        if context.scene.contactsheet.use_custom_rows:
            row_count = context.scene.contactsheet.rows

        grid = Grid.from_content(
            0,
            0,
            context.scene.contactsheet.contactsheet_x,
            context.scene.contactsheet.contactsheet_y,
            content,
            row_count=row_count,
        )

        grid.scale_content(addon_prefs.contactsheet_scale_factor)

        return {"FINISHED"}

    def set_sqe_area_settings(self, context: bpy.types.Context) -> None:
        sqe_editor = opsdata.get_sqe_editor(context)
        sqe_editor.spaces.active.proxy_render_size = "PROXY_25"
        sqe_editor.spaces.active.use_proxies = True

    def set_render_settings(self, context: bpy.types.Context) -> None:
        opsdata.fit_frame_range_to_strips(context)
        context.scene.frame_current = context.scene.frame_start
        context.scene.render.resolution_x = context.scene.contactsheet.contactsheet_x
        context.scene.render.resolution_y = context.scene.contactsheet.contactsheet_y
        context.scene.render.image_settings.file_format = "PNG"
        context.scene.render.image_settings.color_mode = "RGB"
        context.scene.render.image_settings.color_depth = "8"
        context.scene.render.image_settings.compression = 15

    def set_output_path(self, context: bpy.types.Context) -> None:
        addon_prefs = prefs.addon_prefs_get(context)
        cs_dir: Path = addon_prefs.contactsheet_dir_path
        output_path: str = ""

        # File not saved and cs_dir not available.
        if not bpy.data.filepath and not cs_dir:
            logger.warning(
                "Failed to set output settings. Contactsheet Output Directory "
                "not defined in addon preferences and file not saved."
            )
            return

        # File saved and cs_dir available.
        if cs_dir and bpy.data.filepath:
            output_path = cs_dir.joinpath(
                f"{Path(bpy.data.filepath).stem}_contactsheet.png"
            ).as_posix()

        # File not saved but cs_dir available.
        elif cs_dir:
            output_path = cs_dir.joinpath(f"contactsheet.png").as_posix()

        # File saved but cs_dir not available.
        else:
            output_path = (
                Path(bpy.data.filepath)
                .parent.joinpath(f"{Path(bpy.data.filepath).stem}_contactsheet.png")
                .as_posix()
            )

        # Set output path.
        context.scene.render.filepath = output_path


class CS_OT_exit_contactsheet(bpy.types.Operator):
    """ """

    bl_idname = "contactsheet.exit_contactsheet"
    bl_label = "Exit Contact Sheet"
    bl_description = ""

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return bool(context.scene.contactsheet.is_contactsheet)

    def execute(self, context: bpy.types.Context) -> Set[str]:
        cs_scene = context.scene
        cs_scene_name = cs_scene.name

        # Change active scene to orig scene
        context.window.scene = context.scene.contactsheet.contactsheet_meta.scene

        # Restore proxy settings from contactsheet.contactsheet_meta.
        sqe_editor = opsdata.get_sqe_editor(context)
        sqe_editor.spaces.active.proxy_render_size = (
            cs_scene.contactsheet.contactsheet_meta.proxy_render_size
        )
        sqe_editor.spaces.active.use_proxies = (
            cs_scene.contactsheet.contactsheet_meta.use_proxies
        )

        # Remove contactsheet scene.
        bpy.data.scenes.remove(cs_scene)

        self.report({"INFO"}, f"Exited and deleted scene: {cs_scene_name}")

        return {"FINISHED"}


# ----------------REGISTER--------------


classes = [
    CS_OT_make_contactsheet,
    CS_OT_exit_contactsheet,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
