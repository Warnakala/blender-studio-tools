#!/usr/bin/env python3

"""Tool to generate a grid of frames from a video file.

In order to have a quick overview of a film, it's sometimes useful to have a
grid of images, collected at regular intervals within the film.

How does it work? We use ffmpeg, ffprobe and montage to do the heavy lifting.
1. Gather basic info about the video (duration) with ffprobe
2. Generate scaled thumbnails at regular intervals with ffmpeg
3. Combine the thumbnails in a grid with montage

More info in:
* https://trac.ffmpeg.org/wiki/Seeking


Todo:
    * Testing!

This is some vintage code from 2018, written by fsiddi during the Spring
Open Movie project. 
"""

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


parser = argparse.ArgumentParser(description='Generate film grids.')
parser.add_argument('-i', '--in_file', help='Input movie file', required=True)
parser.add_argument('-g', '--grid_size', help='Grid size, for example 5x5', default='5x5')
parser.add_argument('-t', '--thumbnail_size', help='Thumbnail size', default='320:-1')
parser.add_argument('-o', '--output_file', help='Output file path', default='out_grid.png')
parser.add_argument('-y', '--skip_confirmation', help='Skip confirmation', action='store_true')
parser.add_argument('-ss', '--ss', help='Trim start', default='00:00:00')
parser.add_argument('-to', '--to', help='Trim end')
args = parser.parse_args()


def which(command):
    """Check if command is available and return its path."""
    command_path = shutil.which(command)
    if command_path is None:
        print(f'{command} is required to run this script it, but it was not found.')
        sys.exit()
    return command_path


def query_yes_no(question, default="yes"):
    """Ask a yes/no question via raw_input() and return their answer.

    "question" is a string that is presented to the user.
    "default" is the presumed answer if the user just hits <Enter>.
        It must be "yes" (the default), "no" or None (meaning
        an answer is required of the user).

    The "answer" return value is True for "yes" or False for "no".
    """
    valid = {"yes": True, "y": True, "ye": True,
             "no": False, "n": False}
    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while True:
        sys.stdout.write(question + prompt)
        try:
            choice = input().lower()
        except KeyboardInterrupt:
            print('')
            sys.exit()
        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' "
                             "(or 'y' or 'n').\n")


def get_sec(time_str):
    h, m, s = time_str.split(':')
    return int(h) * 3600 + int(m) * 60 + int(s)


def get_time_str(time_in_seconds: float):
    hours = int(time_in_seconds // 3600)
    minutes = int(time_in_seconds // 60)
    seconds = time_in_seconds - (60 * minutes)
    return f'{hours:02d}:{minutes:02d}:{seconds:02.5f}'

toolset = {
    'ffmpeg': os.environ.get('FFMPEG_BIN', 'ffmpeg'),
    'ffprobe': os.environ.get('FFPROBE_BIN', 'ffprobe'),
    'montage': os.environ.get('MONTAGE_BIN', 'montage'),
}

for s in toolset:
    which(toolset[s])

# Get current directory
cwd = Path(os.getcwd())

# Get absolute path of input file (if relative it will be combined with cwd)
in_file_absolute_path = cwd.joinpath(args.in_file)


def gather_video_info():
    ffprobe_command = [
        toolset['ffprobe'],
        '-v',
        'error',
        '-print_format',
        'json',
        '-show_format',
        '-show_streams',
        in_file_absolute_path,
    ]

    p = subprocess.Popen(ffprobe_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p.communicate()

    info_json = json.loads(out)

    video_stream = None

    for stream in info_json['streams']:
        if stream['codec_type'] == 'video':
            # We get the first video stream we find and continue
            video_stream = stream
            break

    if video_stream is None:
        print('Video stream not found.')
        sys.exit()

    return info_json


# Calculate the amount of thumbnails
grid_size = args.grid_size.split('x')
try:
    thumbnails_count = int(grid_size[0]) * int(grid_size[1])
except ValueError:
    print(f'Invalid input for --grid_size: {args.grid_size}')
    sys.exit()

info = gather_video_info()
video_duration = float(info['format']['duration'])

if args.to:
    # Adjust video duration taking into account the -ss and -to arguments
    video_duration = get_sec(args.to) - get_sec(args.ss)
    video_end_time = args.to
else:
    video_duration -= get_sec(args.ss)
    video_end_time = get_time_str(video_duration)

video_start_time = args.ss

# Calculate every how many seconds we need a thumbnails
interval = video_duration / thumbnails_count

print('Summary:')
print(f'Video duration:          {video_duration} seconds')
print(f'Thumbnails count:        {thumbnails_count}')
print(f'Thumbnail interval:      every {interval} second')
print(f'Thumbnail resolution:    {args.thumbnail_size}')
print(f'Video start:             {video_start_time}')
print(f'Video end:               {video_end_time}')

# Confirm output image size before proceeding, unless we run with -y
if not args.skip_confirmation:
    confirm = query_yes_no('Confirm process?')
    if not confirm:
        sys.exit()

tmp_dir = tempfile.TemporaryDirectory()


ffmpeg_command = [
    toolset['ffmpeg'],
    '-ss',
    f'{video_start_time}',
    '-i',
    f'{in_file_absolute_path}',
    '-to',
    f'{video_end_time}',
    '-vf',
    f'fps=1/{interval},scale={args.thumbnail_size}',
    '-copyts',  # With this option -to refers to the original timestamp
    f'{tmp_dir.name}/%3d.jpg'
]

# Generate scaled thumbnails from video file
subprocess.call(ffmpeg_command)

montage_command = [
    toolset['montage'],
    '-geometry',
    '+0+0',
    '-tile',
    f'{args.grid_size}',
    f'{tmp_dir.name}/*.jpg',
    f'{args.output_file}'
]

# Build grid from the thumbnails stored in tmp_dir
subprocess.call(montage_command)
