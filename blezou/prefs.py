import bpy
from .auth import ZSession
from .util import prefs_get


class BZ_AddonPreferences(bpy.types.AddonPreferences):
    """
    Addon preferences to blezou. Holds variables that are important for authentification.
    During runtime new attributes are created that get initialized in: bz_prefs_init_properties()
    """

    bl_idname = __package__

    host: bpy.props.StringProperty(
        name="host", default="", options={"HIDDEN", "SKIP_SAVE"}
    )

    email: bpy.props.StringProperty(
        name="email", default="", options={"HIDDEN", "SKIP_SAVE"}
    )

    passwd: bpy.props.StringProperty(
        name="passwd", default="", options={"HIDDEN", "SKIP_SAVE"}, subtype="PASSWORD"
    )
    category: bpy.props.EnumProperty(
        items=(
            ("ASSETS", "Assets", "Asset related tasks", "FILE_3D", 0),
            ("SHOTS", "Shots", "Shot related tasks", "FILE_MOVIE", 1),
        ),
        default="SHOTS",
    )
    session: ZSession = ZSession()

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        layout.label(text="Preferences for Blezou Addon")
        box = layout.box()
        box.row().prop(self, "host")
        box.row().prop(self, "email")
        box.row().prop(self, "passwd")


def bz_prefs_init_properties(context: bpy.types.Context) -> None:
    prefs = prefs_get(context)

    # TODO: is this the correct way to initialize dynamic properties?
    # we need properties that can hold dicts/nested dicts as value

    # id properties
    prefs["project_active"] = {}
    prefs["sequence_active"] = {}
    prefs["shot_active"] = {}
    prefs["sqe_track_props"] = {}


# ---------REGISTER ----------

classes = [BZ_AddonPreferences]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    # additional setup
    bz_prefs_init_properties(bpy.context)


def unregister():
    # additional setup
    bz_prefs_init_properties(bpy.context)

    # log user out
    prefs = prefs_get(bpy.context)
    prefs.session.end()

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)