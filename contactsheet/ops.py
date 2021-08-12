import sys
import math
import subprocess
import shutil
from pathlib import Path
from typing import Set, Union, Optional, List, Dict, Any, Tuple

import bpy

from contactsheet import vars, prefs, opsdata, util
from contactsheet.log import LoggerFactory
from contactsheet.geo_seq import SequenceRect
from contactsheet.geo import Grid, NestedRectangle

logger = LoggerFactory.getLogger(name=__name__)


class RR_OT_make_contactsheet(bpy.types.Operator):
    """ """

    bl_idname = "rr.make_contactsheet"
    bl_label = "Make Contact Sheet"
    bl_description = ""

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return bool(opsdata.get_valid_cs_sequences(context))

    def execute(self, context: bpy.types.Context) -> Set[str]:

        addon_prefs = prefs.addon_prefs_get(context)

        # Gather sequences to process.
        sequences: List[bpy.types.Sequence] = opsdata.get_valid_cs_sequences(context)

        if not context.selected_sequences:
            # If nothing selected take a continuous row of the top most sequences.
            sequences = opsdata.get_top_level_valid_strips_continious(context)

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
        logger.info("Create tmp scene for contactsheet: %s", scene_tmp.name)

        # save contactsheet metadata
        sqe_editor = opsdata.get_sqe_editor(context)
        sqe_editor.spaces.active.proxy_render_size = "PROXY_25"
        sqe_editor.spaces.active.use_proxies = True
        scene_tmp.rr.is_contactsheet = True
        scene_tmp.rr.contactsheet_meta.scene = scene_orig
        scene_tmp.rr.contactsheet_meta.use_proxies = orig_use_proxies
        scene_tmp.rr.contactsheet_meta.proxy_render_size = orig_proxy_render_size

        # remove sequences in new scene that are not selected
        seq_rm: List[bpy.types.Sequence] = [
            s for s in scene_tmp.sequence_editor.sequences_all if not s.select
        ]
        for s in seq_rm:
            scene_tmp.sequence_editor.sequences.remove(s)

        # get all sequences in new scene and sort them
        sequences = list(scene_tmp.sequence_editor.sequences_all)
        sequences.sort(key=lambda strip: (strip.frame_final_start, strip.channel))

        # Place black color strip in channel 1
        color_strip = context.scene.sequence_editor.sequences.new_effect(
            "background", "COLOR", 1, start_frame, frame_end=start_frame + 1
        )
        color_strip.color = (0, 0, 0)

        # create required number of metastrips to workaround the limit of 32 channels
        nr_of_metastrips = math.ceil(len(sequences) / 32)
        metastrips: List[bpy.types.MetaSequence] = []
        for i in range(nr_of_metastrips):
            channel = i + 2
            meta_strip = context.scene.sequence_editor.sequences.new_meta(
                f"contactsheet_meta_{channel-1}", channel, start_frame
            )
            metastrips.append(meta_strip)
            logger.info("Created metastrip: %s", meta_strip.name)

        # Move sequences in to metastrips, place them on top of each other, make them start at the same frame.
        for idx, seq in enumerate(sequences):
            # Move to metastrip.
            channel = idx + 1
            meta_index = math.floor(idx / 32)
            seq.move_to_meta(metastrips[meta_index])

            # set seq properties inside metastrip
            seq.channel = channel - ((meta_index) * 32)
            seq.frame_start = start_frame
            seq.blend_type = "ALPHA_OVER"

        # elongate all strips to the strip with the longest duration
        tmp_sequences = sorted(sequences, key=lambda s: s.frame_final_end)
        tmp_sequences.insert(0, color_strip)
        max_end: int = tmp_sequences[-1].frame_final_end
        for strip in tmp_sequences:
            if strip.frame_final_end < max_end:
                strip.frame_final_end = max_end

        # clip the metastrip frame end at max end and set alpha over
        for strip in metastrips:
            strip.frame_start = start_frame
            strip.frame_final_end = max_end
            strip.blend_type = "ALPHA_OVER"

        # scene settings
        # change frame range and frame start
        self.set_render_settings(context)
        self.set_sqe_area_settings(context)

        # create content list for grid
        sqe_rects: List[SequenceRect] = [SequenceRect(seq) for seq in sequences]
        content: List[NestedRectangle] = [
            NestedRectangle(0, 0, srect.width, srect.height, child=srect)
            for srect in sqe_rects
        ]

        # create grid
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
        cs_dir = addon_prefs.contactsheet_dir_path
        render_dir = Path(context.scene.contactsheet.render_dir_path)

        if not render_dir:
            logger.warning(
                "Failed to set output settings. Invalid context.scene.contactsheet.render_dir"
            )
            return

        if not cs_dir:
            logger.warning(
                "Failed to set output settings. Invalid addon_prefs.contactsheet_dir"
            )
            return

        # set output path
        context.scene.render.filepath = cs_dir.joinpath(f"contactsheet.png").as_posix()


class RR_OT_exit_contactsheet(bpy.types.Operator):
    """ """

    bl_idname = "rr.exit_contactsheet"
    bl_label = "Exit Contact Sheet"
    bl_description = ""

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return bool(context.scene.contactsheet.is_contactsheet)

    def execute(self, context: bpy.types.Context) -> Set[str]:
        cs_scene = context.scene
        cs_scene_name = cs_scene.name

        # change active scene to orig scene before cs
        context.window.scene = context.scene.contactsheet.contactsheet_meta.scene

        # restore proxy settings from rr.contactsheet_meta
        sqe_editor = opsdata.get_sqe_editor(context)
        sqe_editor.spaces.active.proxy_render_size = (
            cs_scene.contactsheet.contactsheet_meta.proxy_render_size
        )
        sqe_editor.spaces.active.use_proxies = (
            cs_scene.contactsheet.contactsheet_meta.use_proxies
        )

        # remove cs scene
        bpy.data.scenes.remove(cs_scene)

        self.report({"INFO"}, f"Exited and deleted scene: {cs_scene_name}")

        return {"FINISHED"}


# ----------------REGISTER--------------


classes = [
    RR_OT_make_contactsheet,
    RR_OT_exit_contactsheet,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
