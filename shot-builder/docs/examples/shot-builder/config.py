from shot_builder.connectors.kitsu import KitsuConnector

PRODUCTION_NAME = KitsuConnector
SHOTS = KitsuConnector
ASSETS = KitsuConnector
RENDER_SETTINGS = KitsuConnector

KITSU_PROJECT_ID = "fc77c0b9-bb76-41c3-b843-c9b156f9b3ec"

# Formatting rules
# ----------------

# The name of the scene in blender where the shot is build in.
# SCENE_NAME_FORMAT = "{shot.sequence_code}_{shot.code}.{task_type}"

# The path where the build shot is saved.
# FILE_NAME_FORMAT = "{production.path}shots/{shot.code}/{shot.code}.{task_type}.blend"