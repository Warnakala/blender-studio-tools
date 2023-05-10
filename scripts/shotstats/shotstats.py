#!/usr/bin/env python3

"""Generate visual render stats for a frame sequence.

Overlap a render time line chart to a video. Display a red playhead
corresponding to the current frame in the video.

This is some vintage code from 2017, written by fsiddi during the Agent 327
film project, to visually detect spikes in render time.
"""

import argparse
import csv
import datetime
import json
import os
import re
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


parser = argparse.ArgumentParser(description='Generate shots stats.')
parser.add_argument('-i', '--in_path', help='Input path', required=True)
parser.add_argument('-o', '--out_path', help='Output directory')
parser.add_argument('-y', '--skip_confirmation', help='Skip confirmation', action='store_true')
parser.add_argument('-f', '--framerate', help='Framerate', default=24)
parser.add_argument('--image_format', help='Either PNG or EXR', default='PNG')
parser.add_argument('--memory_unit', default='G')
parser.add_argument('--render_time_unit', help='How display render time', default='m')
args = parser.parse_args()


def which(command):
    """Check if command is available and return its path."""
    command_path = shutil.which(command)
    if command_path is None:
        print(f'{command} is required to run this script it, but it was not found.')
        sys.exit()
    return command_path


toolset = {
    'ffmpeg': os.environ.get('FFMPEG_BIN', 'ffmpeg'),
    'ffprobe': os.environ.get('FFPROBE_BIN', 'ffprobe'),
    'exrheader': os.environ.get('EXRHEADER_BIN', 'exrheader'),
    'gnuplot': os.environ.get('GNUPLOT_BIN', 'gnuplot'),
    'identify': os.environ.get('IDENTIFY_BIN', 'identify'),
}

# Get render time and memory from frames

# If exr, use exrheader (we will also need jpeg previews later)


def parse_metadata(metadata_string: str):
    if args.image_format == 'EXR':
        # Metadata looks like this:
        # Memory (type string): "0.00M"
        re_result = re.search('"(.*)"', metadata_string)
        return re_result.group(1)
    elif args.image_format == 'PNG':
        # Metadata looks like this:
        #     Memory: 0.00M
        return metadata_string.split(':', 1)[1].strip()


def parse_memory(memory: str):
    """Get the amount of memory used.

    We strip the last char, and assume it's M. Then we cast to float.
    """
    memory = parse_metadata(memory)
    memory_in_mb = float(memory[:-1])
    if args.memory_unit == 'G':
        m = memory_in_mb / 1024
    else:
        m = memory_in_mb
    return m


def parse_render_time(time_metadata):
    """Get the render time in seconds."""
    time_metadata = parse_metadata(time_metadata)
    time_array = time_metadata.split(':')
    if len(time_array) < 2:  # Only seconds
        time_in_seconds = float(time_metadata)
    elif len(time_array) < 3:  # Minutes and seconds
        time_in_seconds = int(time_array[0]) * 60 + float(time_array[1])
    elif len(time_array) < 4:  # Hours, minutes and seconds
        time_in_seconds = int(time_array[0]) * 3600 + int(time_array[1]) * 60 + float(time_array[2])
    else:
        time_in_seconds = float(0)

    if args.render_time_unit == 'm':
        t = time_in_seconds / 60
    else:
        t = time_in_seconds
    return t


def parse_frame_number(frame_number_metadata):
    """Get the frame number."""
    frame_number_metadata = parse_metadata(frame_number_metadata)
    return int(frame_number_metadata)


def parse_exr_frames(frames_list):
    """Parse EXR frames using the 'exrheader' command."""
    frames_stats = []
    for frame in frames_list:
        exrheader_command = [
            toolset['exrheader'],
            frame
        ]
        p = subprocess.Popen(exrheader_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = p.communicate()

        lines = iter(out.decode('utf-8').splitlines())
        frame_stats = {
            'name': frame.stem,
            'frame_number': 0,
            'memory_in_mb': 0,
            'render_time_in_s': 0
        }
        for line in lines:
            if line.startswith('Memory'):
                frame_stats['memory_in_mb'] = parse_memory(line)
            elif line.startswith('RenderTime'):
                frame_stats['render_time_in_s'] = parse_render_time(line)
            elif line.startswith('Frame'):
                frame_stats['frame_number'] = parse_frame_number(line)
        frames_stats.append(frame_stats)

    return frames_stats


# If png use identify -verbose
def parse_png_frames(frames_list):
    frames_stats = []
    for frame in frames_list:
        identify_command = [
            toolset['identify'],
            '-verbose',
            frame
        ]
        p = subprocess.Popen(identify_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = p.communicate()
        lines = iter(out.decode('utf-8').splitlines())
        frame_stats = {
            'name': frame.stem,
            'frame_number': 0,
            'memory_in_mb': 0,
            'render_time_in_s': 0
        }
        for line in lines:
            line = line.strip()
            if line.startswith('Memory'):
                frame_stats['memory_in_mb'] = parse_memory(line)
            elif line.startswith('RenderTime'):
                frame_stats['render_time_in_s'] = parse_render_time(line)
            # elif line.startswith('Frame'):
            #     frame_stats['frame_number'] = parse_frame_number(line)
            frame_stats['frame_number'] = int(frame.stem)
        print(f"Frame {frame_stats['frame_number']}: {frame_stats['memory_in_mb']} - {frame_stats['render_time_in_s']}")
        frames_stats.append(frame_stats)

    return frames_stats


# Get current directory
cwd = Path.cwd()

# Get absolute path of input dir (if relative it will be combined with cwd)
in_dir_absolute_path = cwd.joinpath(args.in_path)

# Look for files (png or exr)
frames = sorted(in_dir_absolute_path.glob(f'*.{args.image_format.lower()}'))


frames_stats_path = in_dir_absolute_path.parent / f'{in_dir_absolute_path.name}-frames_stats.csv'


def get_frame_stats():
    if frames_stats_path.exists():
        with open(frames_stats_path) as csvfile:
            reader = csv.DictReader(csvfile, delimiter='\t')
            return [row for row in reader]
    if frames:
        if args.image_format == 'EXR':
            stats = parse_exr_frames(frames)
        elif args.image_format == 'PNG':
            stats = parse_png_frames(frames)
        with open(frames_stats_path, 'w', newline='') as csvfile:
            fieldnames = ['frame_number', 'name', 'memory_in_mb', 'render_time_in_s']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter='\t')

            writer.writeheader()
            for s in stats:
                writer.writerow(s)
            print(f'{frames_stats_path} is ready.')
            return stats
    else:
        print(f'No {args.image_format} images found.')
        sys.exit()


stats = get_frame_stats()
# Get frame resolution

# TODO(fsiddi) handle missing image
first_frame = frames[0]
# If we are working with exr, look for a .jpg file
if args.image_format == 'EXR':
    first_frame = frames[0].with_suffix('.jpg')

identify_format = '%[fx:w]x%[fx:h]'

identify_command = [
    'identify',
    '-format',
    identify_format,
    first_frame
]

p = subprocess.Popen(identify_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
out, err = p.communicate()

result = out.decode('utf-8').splitlines()[0]
frame_width, frame_height = result.split('x')

# Make chart with memory usage and render time, using the size of frame

# tmp_dir = tempfile.TemporaryDirectory()
# tmp_dir_path = Path(tmp_dir.name)
gnuplot_chart_config_path = in_dir_absolute_path.parent / f'{in_dir_absolute_path.name}-gnuplot_chart'
chart_file_path = in_dir_absolute_path.parent / f'{in_dir_absolute_path.name}-chart.png'

template_vars = {
    'tmp_chart_file': chart_file_path,
    'frames_stats_file': frames_stats_path,
    'frame_start_number': stats[0]['frame_number'],
    'width': frame_width,
    'height': frame_height,
}

with open('gnuplot_chart.tpl') as fp:
    line = fp.readline()
    with open(gnuplot_chart_config_path, 'w') as fc:
        while line:
            parsed_line = line.format(**template_vars)
            fc.write(parsed_line)
            line = fp.readline()

gnuplot_command = [
    'gnuplot',
    '-c',
    gnuplot_chart_config_path,
]

subprocess.call(gnuplot_command)

#sys.exit()

# Combine the chart with images sequence and overlay the playhead
# For instance if we have a 260 frames clip
#
# 260 frames = 260 / <args.framerate> = 10.83333 seconds
# video_width / video_duration = 2048 / 10.83333 = 189.04621 pixels / second.

# Arbitrary offset defined by the chart
chart_margin_x_pixel = 45

chart_width = int(frame_width) - chart_margin_x_pixel - 17

pixel_per_second = chart_width / (len(frames) / args.framerate)

overlay_string = f"overlay, overlay=x='if(gte(t,0), -w+{chart_margin_x_pixel}+(t)*{pixel_per_second}, NAN)':y=0"

# Get the number of the first frame of the sequence
start_number = stats[0]['frame_number']

output_file_name = f'{in_dir_absolute_path.name}-{datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")}.mp4'
output_file_path = Path(args.out_path) / output_file_name

extension = 'png' if args.image_format == 'PNG' else 'jpg'
input_path = in_dir_absolute_path.joinpath(f'%6d.{extension}')

ffmpeg_command = [
    'ffmpeg',
    '-framerate',
    f'{args.framerate}',
    '-start_number',
    f'{start_number}',
    '-i',
    f'{input_path}',
    '-i',
    f'{chart_file_path}',
    '-i',
    'playhead.png',
    '-filter_complex',
    f'{overlay_string}',
    str(output_file_path)
]

subprocess.call(ffmpeg_command)
