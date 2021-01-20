from shot_builder.connectors.kitsu import KitsuConnector

PRODUCTION_NAME = KitsuConnector
SHOTS = KitsuConnector
ASSETS = KitsuConnector
RENDER_SETTINGS = KitsuConnector

KITSU_PROJECT_ID = "fc77c0b9-bb76-41c3-b843-c9b156f9b3ec"

# Formatting rules
SCENE_NAME_FORMAT = "{shot.sequence_code}_{shot.code}.{task_type}"
