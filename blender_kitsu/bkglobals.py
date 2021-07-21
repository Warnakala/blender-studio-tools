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

import os
from pathlib import Path

FPS = 24
VERSION_PATTERN = r"v\d\d\d"
FRAME_START = 101

SHOT_DIR_NAME = "shots"
ASSET_DIR_NAME = "lib"

ASSET_TASK_MAPPING = {
    "geometry": "Geometry",
    "grooming": "Grooming",
    "modeling": "Modeling",
    "rigging": "Rigging",
    "sculpting": "Sculpting",
    "shading": "Shading",
}

ASSET_TYPE_MAPPING = {
    "char": "Character",
    "set": "Set",
    "props": "Prop",
    "env": "Library",
}

SHOT_TASK_MAPPING = {
    "anim": "Animation",
    "comp": "Compositing",
    "fx": "FX",
    "layout": "Layout",
    "lighting": "Lighting",
    "previz": "Previz",
    "rendering": "Rendering",
    "smear_to_mesh": "Smear to mesh",
    "storyboard": "Storyboard",
}

PREFIX_RIG = "RIG-"

MULTI_ASSETS = [
    "sprite",
    "snail",
    "spider",
    "peanut",
    "peanut_box",
    "pretzel",
    "corn_dart",
    "corn_darts_bag",
    "meat_stick",
    "salty_twists_bag",
    "salt_stick",
    "salt_stix_package",
    "briny_bear",
    "briny_bears_bag",
]  # list of assets that gets duplicated and therefore follows another naming sheme

ASSET_COLL_PREFIXES = ["CH-", "PR-", "SE-"]


RES_DIR_PATH = Path(os.path.abspath(__file__)).parent.joinpath("res")

SCENE_NAME_PLAYBLAST = "playblast_playback"
PLAYBLAST_DEFAULT_STATUS = "Todo"
