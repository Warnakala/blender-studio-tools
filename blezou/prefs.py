import hashlib
import bpy
from .auth import ZSession
from .util import prefs_get, get_datadir


class BZ_AddonPreferences(bpy.types.AddonPreferences):
    """
    Addon preferences to blezou. Holds variables that are important for authentification.
    During runtime new attributes are created that get initialized in: bz_prefs_init_properties()
    """

    def get_thumbnails_dir(self) -> str:
        """Generate a path based on get_datadir and the current file name.

        The path is constructed by combining the OS application data dir,
        "blender-edit-breakdown" and a hashed version of the filepath.

        Note: If a file is moved, the thumbnails will need to be recomputed.
        """
        hashed_filename = hashlib.md5(bpy.data.filepath.encode()).hexdigest()
        storage_dir = get_datadir() / "blezou" / hashed_filename
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
    session: ZSession = ZSession()

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        layout.label(text="Preferences for Blezou Addon")
        box = layout.box()
        box.row().prop(self, "host")
        box.row().prop(self, "email")
        box.row().prop(self, "passwd")
        box.row().prop(self, "folder_thumbnail")


# ---------REGISTER ----------

classes = [BZ_AddonPreferences]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():

    # log user out
    prefs = prefs_get(bpy.context)
    if prefs.session.is_auth():
        prefs.session.end()

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
