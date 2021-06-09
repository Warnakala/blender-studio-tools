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
]  # list of assets that gets duplicated and therefore follows another naming sheme

ASSET_COLL_PREFIXES = ["CH-", "PR-", "SE-"]
