import bpy
from pathlib import Path

import contextlib

from blender_kitsu import (
    prefs,
)

@contextlib.contextmanager
def override_render_format(self, context):
        """Overrides the render settings for playblast creation"""
        rd = context.scene.render
       # Format render settings.
        percentage = rd.resolution_percentage
        file_format = rd.image_settings.file_format
        ffmpeg_constant_rate = rd.ffmpeg.constant_rate_factor
        ffmpeg_codec = rd.ffmpeg.codec
        ffmpeg_format = rd.ffmpeg.format
        ffmpeg_audio_codec = rd.ffmpeg.audio_codec

        try:
            rd.resolution_percentage = 100
            rd.image_settings.file_format = "FFMPEG"
            rd.ffmpeg.constant_rate_factor = "HIGH"
            rd.ffmpeg.codec = "H264"
            rd.ffmpeg.format = "MPEG4"
            rd.ffmpeg.audio_codec = "AAC"

            yield

        finally:
            rd.resolution_percentage = percentage
            rd.image_settings.file_format = file_format
            rd.ffmpeg.codec = ffmpeg_codec
            rd.ffmpeg.constant_rate_factor = ffmpeg_constant_rate
            rd.ffmpeg.format = ffmpeg_format
            rd.ffmpeg.audio_codec = ffmpeg_audio_codec

@contextlib.contextmanager
def override_render_path(self, context, render_file_path):
        """Overrides the render settings for playblast creation"""
        rd = context.scene.render
        # Filepath.
        filepath = rd.filepath

        try:
            # Filepath.
            rd.filepath = render_file_path

            yield

        finally:
            # Filepath.
            rd.filepath = filepath

@contextlib.contextmanager
def override_hide_viewport_gizmos(self, context,):
        sp = context.space_data
        show_gizmo = sp.show_gizmo
        show_overlays = sp.overlay.show_overlays

        try:
            sp.show_gizmo = False
            sp.overlay.show_overlays = False

            yield
        finally:
            sp.show_gizmo = show_gizmo
            sp.overlay.show_overlays = show_overlays

@contextlib.contextmanager
def override_metadata_stamp_settings(self, context,):
        rd = context.scene.render
        # Get first last name for stamp note text.
        session = prefs.session_get(context)
        first_name = session.data.user["first_name"]
        last_name = session.data.user["last_name"]
        # Remember current render settings in order to restore them later.

        # Stamp metadata settings.
        metadata_input = rd.metadata_input
        use_stamp_date = rd.use_stamp_date
        use_stamp_time = rd.use_stamp_time
        use_stamp_render_time = rd.use_stamp_render_time
        use_stamp_frame = rd.use_stamp_frame
        use_stamp_frame_range = rd.use_stamp_frame_range
        use_stamp_memory = rd.use_stamp_memory
        use_stamp_hostname = rd.use_stamp_hostname
        use_stamp_camera = rd.use_stamp_camera
        use_stamp_lens = rd.use_stamp_lens
        use_stamp_scene = rd.use_stamp_scene
        use_stamp_marker = rd.use_stamp_marker
        use_stamp_marker = rd.use_stamp_marker
        use_stamp_note = rd.use_stamp_note
        stamp_note_text = rd.stamp_note_text
        use_stamp = rd.use_stamp
        stamp_font_size = rd.stamp_font_size
        stamp_foreground = rd.stamp_foreground
        stamp_background = rd.stamp_background
        use_stamp_labels = rd.use_stamp_labels
        try:

            # Stamp metadata settings.
            rd.metadata_input = "SCENE"
            rd.use_stamp_date = False
            rd.use_stamp_time = False
            rd.use_stamp_render_time = False
            rd.use_stamp_frame = True
            rd.use_stamp_frame_range = False
            rd.use_stamp_memory = False
            rd.use_stamp_hostname = False
            rd.use_stamp_camera = False
            rd.use_stamp_lens = True
            rd.use_stamp_scene = False
            rd.use_stamp_marker = False
            rd.use_stamp_marker = False
            rd.use_stamp_note = True
            rd.stamp_note_text = f"Animator: {first_name} {last_name}"
            rd.use_stamp = True
            rd.stamp_font_size = 12
            rd.stamp_foreground = (0.8, 0.8, 0.8, 1)
            rd.stamp_background = (0, 0, 0, 0.25)
            rd.use_stamp_labels = True

            yield

        finally:
            # Stamp metadata settings.
            rd.metadata_input = metadata_input
            rd.use_stamp_date = use_stamp_date
            rd.use_stamp_time = use_stamp_time
            rd.use_stamp_render_time = use_stamp_render_time
            rd.use_stamp_frame = use_stamp_frame
            rd.use_stamp_frame_range = use_stamp_frame_range
            rd.use_stamp_memory = use_stamp_memory
            rd.use_stamp_hostname = use_stamp_hostname
            rd.use_stamp_camera = use_stamp_camera
            rd.use_stamp_lens = use_stamp_lens
            rd.use_stamp_scene = use_stamp_scene
            rd.use_stamp_marker = use_stamp_marker
            rd.use_stamp_marker = use_stamp_marker
            rd.use_stamp_note = use_stamp_note
            rd.stamp_note_text = stamp_note_text
            rd.use_stamp = use_stamp
            rd.stamp_font_size = stamp_font_size
            rd.stamp_foreground = stamp_foreground
            rd.stamp_background = stamp_background
            rd.use_stamp_labels = use_stamp_labels
         
@contextlib.contextmanager
def override_viewport_shading(self, context):
        """Overrides the render settings for playblast creation"""
        rd = context.scene.render
        sps = context.space_data.shading
        sp = context.space_data

        # Space data settings.
        shading_type = sps.type
        shading_light = sps.light
        studio_light = sps.studio_light
        color_type = sps.color_type
        background_type = sps.background_type

        show_backface_culling = sps.show_backface_culling
        show_xray = sps.show_xray
        show_shadows = sps.show_shadows
        show_cavity = sps.show_cavity
        show_object_outline = sps.show_object_outline
        show_specular_highlight = sps.show_specular_highlight

        try:
            # Space data settings.
            sps.type = "SOLID"
            sps.light = "STUDIO"
            sps.studio_light = "Default"
            sps.color_type = "MATERIAL"
            sps.background_type = "THEME"

            sps.show_backface_culling = False
            sps.show_xray = False
            sps.show_shadows = False
            sps.show_cavity = False
            sps.show_object_outline = False
            sps.show_specular_highlight = True

            yield

        finally:
            # Space data settings.
            sps.type = shading_type
            sps.light = shading_light
            sps.studio_light = studio_light
            sps.color_type = color_type
            sps.background_type = background_type

            sps.show_backface_culling = show_backface_culling
            sps.show_xray = show_xray
            sps.show_shadows = show_shadows
            sps.show_cavity = show_cavity
            sps.show_object_outline = show_object_outline
            sps.show_specular_highlight = show_specular_highlight


def playblast_with_shading_settings(self, context, file_path):
    # Render and save playblast
    with override_render_path(self, context, file_path):
        with override_render_format(self, context,):
            with override_metadata_stamp_settings(self, context):
                with override_hide_viewport_gizmos(self, context):
                    with override_viewport_shading(self, context):

                        # Get output path.
                        output_path = Path(file_path)

                        # Ensure folder exists.
                        Path(context.scene.kitsu.playblast_dir).mkdir(
                            parents=True, exist_ok=True)

                        # Make opengl render.
                        bpy.ops.render.opengl(animation=True)
                        return output_path


def playblast_user_shading_settings(self, context, file_path):
    # Render and save playblast
    with override_render_path(self, context, file_path):
        with override_render_format(self, context,):
            with override_metadata_stamp_settings(self, context):
                with override_hide_viewport_gizmos(self, context):
                    # Get output path.
                    output_path = Path(file_path)

                    # Ensure folder exists.
                    Path(context.scene.kitsu.playblast_dir).mkdir(
                        parents=True, exist_ok=True)

                    # Make opengl render.
                    bpy.ops.render.opengl(animation=True)
                    return output_path
