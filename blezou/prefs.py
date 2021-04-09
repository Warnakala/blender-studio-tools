import sys
import hashlib
from pathlib import Path
import bpy
from bpy.app.handlers import persistent
from .auth import ZSession
from .types import ZProject
from .logger import ZLoggerFactory
from .ops import BZ_OT_ProductionsLoad, BZ_OT_SessionStart, BZ_OT_SessionEnd

logger = ZLoggerFactory.getLogger(name=__name__)

_ZPROJECT_ACTIVE: ZProject = ZProject()


class BZ_AddonPreferences(bpy.types.AddonPreferences):
    """
    Addon preferences to blezou. Holds variables that are important for authentification.
    During runtime new attributes are created that get initialized in: bz_prefs_init_properties()
    """

    def get_datadir(self) -> Path:
        """Returns a Path where persistent application data can be stored.

        # linux: ~/.local/share
        # macOS: ~/Library/Application Support
        # windows: C:/Users/<USER>/AppData/Roaming
        """

        home = Path.home()

        if sys.platform == "win32":
            return home / "AppData/Roaming"
        elif sys.platform == "linux":
            return home / ".local/share"
        elif sys.platform == "darwin":
            return home / "Library/Application Support"

    def get_thumbnails_dir(self) -> str:
        """Generate a path based on get_datadir and the current file name.

        The path is constructed by combining the OS application data dir,
        "blender-edit-breakdown" and a hashed version of the filepath.

        Note: If a file is moved, the thumbnails will need to be recomputed.
        """
        hashed_filename = hashlib.md5(bpy.data.filepath.encode()).hexdigest()
        storage_dir = self.get_datadir() / "blezou" / hashed_filename
        # storage_dir.mkdir(parents=True, exist_ok=True)
        return storage_dir.as_posix()

    bl_idname = __package__

    host: bpy.props.StringProperty(  # type: ignore
        name="host", default="", options={"HIDDEN", "SKIP_SAVE"}
    )

    email: bpy.props.StringProperty(  # type: ignore
        name="email", default="", options={"HIDDEN", "SKIP_SAVE"}
    )

    passwd: bpy.props.StringProperty(  # type: ignore
        name="passwd", default="", options={"HIDDEN", "SKIP_SAVE"}, subtype="PASSWORD"
    )
    category: bpy.props.EnumProperty(  # type: ignore
        items=(
            ("ASSETS", "Assets", "Asset related tasks", "FILE_3D", 0),
            ("SHOTS", "Shots", "Shot related tasks", "FILE_MOVIE", 1),
        ),
        default="SHOTS",
    )
    folder_thumbnail: bpy.props.StringProperty(  # type: ignore
        name="thumbnail folder",
        description="Folder in which thumbnails will be saved",
        default="",
        subtype="DIR_PATH",
        get=get_thumbnails_dir,
    )

    project_active_id: bpy.props.StringProperty(  # type: ignore
        name="previous project id",
        description="GazouId that refers to the last active project",
        default="",
        options={"HIDDEN", "SKIP_SAVE"},
    )

    shot_pattern: bpy.props.StringProperty(  # type: ignore
        name="Shot Pattern",
        description="Pattern to define how Bulk Init will name the shots. Supported wildcards: <Project>, <Sequence>, <Counter>",
        default="<Sequence>_<Counter>",
    )

    enable_debug: bpy.props.BoolProperty(  # type: ignore
        name="Enable Debug Operators",
        description="Enables Operatots that provide debug functionality.",
    )

    session: ZSession = ZSession()

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        layout.label(text="Login and Host Settings")
        box = layout.box()

        # login
        box.row().prop(self, "host")
        box.row().prop(self, "email")
        box.row().prop(self, "passwd")
        if not context.preferences.addons["blezou"].preferences.session.is_auth():
            box.row().operator(BZ_OT_SessionStart.bl_idname, text="Login", icon="PLAY")
        else:
            box.row().operator(
                BZ_OT_SessionEnd.bl_idname, text="Logout", icon="PANEL_CLOSE"
            )
        # Production
        layout.label(text="Active Production")
        box = layout.box()
        row = box.row(align=True)

        if not _ZPROJECT_ACTIVE:
            prod_load_text = "Select Production"
        else:
            prod_load_text = _ZPROJECT_ACTIVE.name

        row.operator(
            BZ_OT_ProductionsLoad.bl_idname, text=prod_load_text, icon="DOWNARROW_HLT"
        )
        # misc settings
        layout.label(text="Misc")
        box = layout.box()
        box.row().prop(self, "enable_debug")
        box.row().prop(self, "folder_thumbnail")


def init_cache_variables(context: bpy.types.Context = bpy.context) -> None:
    global _ZPROJECT_ACTIVE

    addon_prefs = context.preferences.addons["blezou"].preferences
    project_active_id = addon_prefs.project_active_id

    if project_active_id:
        _ZPROJECT_ACTIVE = ZProject.by_id(project_active_id)
        logger.info(f"Initialized Active Project Cache to: {_ZPROJECT_ACTIVE.name}")


def clear_cache_variables():
    global _ZPROJECT_ACTIVE

    _ZPROJECT_ACTIVE = ZProject()
    logger.info("Cleared Active Project Cache")


@persistent
def load_post_handler(dummy):
    addon_prefs = bpy.context.preferences.addons["blezou"].preferences
    if addon_prefs.session.is_auth():
        addon_prefs.session.end()
    clear_cache_variables()


# ---------REGISTER ----------

classes = [BZ_AddonPreferences]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.app.handlers.load_post.append(load_post_handler)


def unregister():

    # log user out
    addon_prefs = bpy.context.preferences.addons["blezou"].preferences
    if addon_prefs.session.is_auth():
        addon_prefs.session.end()

    # clear cache
    clear_cache_variables()

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
