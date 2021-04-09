import bpy
from bpy.app.handlers import persistent
from .types import ZProject, ZSequence, ZShot, ZAssetType, ZAsset
from dataclasses import asdict
from .logger import ZLoggerFactory
from typing import Optional, Any

logger = ZLoggerFactory.getLogger(name=__name__)

_ZSEQUENCE_ACTIVE: ZSequence = ZSequence()
_ZSHOT_ACTIVE: ZShot = ZShot()
_ZASSET_ACTIVE: ZAsset = ZAsset()
_ZASSET_TYPE_ACTIVE: ZAssetType = ZAssetType()


class BZ_PopertyGroupSequence(bpy.types.PropertyGroup):
    """
    Property group that will be registered on sequence strips.
    They hold metadata that will be used to compose a data structure that can
    be pushed to backend.
    """

    # shot
    shot_id: bpy.props.StringProperty(name="Shot ID")  # type: ignore
    shot_name: bpy.props.StringProperty(name="Shot", default="")  # type: ignore
    shot_description: bpy.props.StringProperty(name="Description", default="")  # type: ignore

    # sequence
    sequence_name: bpy.props.StringProperty(name="Sequence", default="")  # type: ignore
    sequence_id: bpy.props.StringProperty(name="Seq ID", default="")  # type: ignore

    # project
    project_name: bpy.props.StringProperty(name="Project", default="")  # type: ignore
    project_id: bpy.props.StringProperty(name="Project ID", default="")  # type: ignore

    # meta
    initialized: bpy.props.BoolProperty(  # type: ignore
        name="Initialized", default=False, description="Is Blezou shot"
    )
    linked: bpy.props.BoolProperty(  # type: ignore
        name="Linked", default=False, description="Is linked to an ID in gazou"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.shot,
            "sequence_name": self.sequence,
            "description": self.description,
        }

    def clear(self):
        self.shot_id = ""
        self.shot_name = ""
        self.shot_description = ""

        self.sequence_id = ""
        self.sequence_name = ""

        self.project_name = ""
        self.project_id = ""

        self.initialized = False
        self.linked = False


class BZ_PopertyGroupScene(bpy.types.PropertyGroup):
    """"""

    sequence_active_id: bpy.props.StringProperty(  # type: ignore
        name="Active Sequence ID",
        description="ID that refers to the active sequence on server",
        default="",
        options={"HIDDEN", "SKIP_SAVE"},
    )
    shot_active_id: bpy.props.StringProperty(  # type: ignore
        name="Active Shot ID",
        description="IDthat refers to the active project on server",
        default="",
        options={"HIDDEN", "SKIP_SAVE"},
    )
    asset_active_id: bpy.props.StringProperty(  # type: ignore
        name="Active Asset ID",
        description="ID that refers to the active asset on server",
        default="",
        options={"HIDDEN", "SKIP_SAVE"},
    )
    asset_type_active_id: bpy.props.StringProperty(  # type: ignore
        name="Active Asset Type ID",
        description="ID that refers to the active asset type on server",
        default="",
        options={"HIDDEN", "SKIP_SAVE"},
    )

    def clear(self):
        self.sequence_active_id = ""
        self.shot_active_id = ""
        self.asset_active_id = ""
        self.asset_type_active_id = ""


class BZ_PopertyGroupWindow(bpy.types.PropertyGroup):
    """"""

    multi_edit_seq: bpy.props.StringProperty(  # type: ignore
        name="Sequence",
        description="",
        default="",
    )

    def clear(self):
        self.multi_edit_seq = ""


def init_cache_variables(context: bpy.types.Context = bpy.context) -> None:
    global _ZSEQUENCE_ACTIVE
    global _ZSHOT_ACTIVE
    global _ZASSET_ACTIVE
    global _ZASSET_TYPE_ACTIVE

    sequence_active_id = context.scene.blezou.sequence_active_id
    shot_active_id = context.scene.blezou.shot_active_id
    asset_active_id = context.scene.blezou.asset_active_id
    asset_type_active_id = context.scene.blezou.asset_type_active_id

    if sequence_active_id:
        _ZSEQUENCE_ACTIVE = ZSequence.by_id(sequence_active_id)
        logger.info(f"Initialized active aequence cache to: {_ZSEQUENCE_ACTIVE.name}")

    if shot_active_id:
        _ZSHOT_ACTIVE = ZShot.by_id(shot_active_id)
        logger.info(f"Initialized active shot cache to: {_ZSHOT_ACTIVE.name}")

    if asset_active_id:
        _ZASSET_ACTIVE = ZAsset.by_id(asset_active_id)
        logger.info(f"Initialized active asset cache to: {_ZASSET_ACTIVE.name}")

    if asset_type_active_id:
        _ZASSET_TYPE_ACTIVE = ZAssetType.by_id(asset_type_active_id)
        logger.info(
            f"Initialized active asset type cache to: {_ZASSET_TYPE_ACTIVE.name}"
        )


def clear_cache_variables():
    global _ZSEQUENCE_ACTIVE
    global _ZSHOT_ACTIVE
    global _ZASSET_ACTIVE
    global _ZASSET_TYPE_ACTIVE

    _ZSEQUENCE_ACTIVE = ZSequence()
    logger.info("Cleared active aequence cache")
    _ZSHOT_ACTIVE = ZShot()
    logger.info("Cleared active shot cache")
    _ZASSET_ACTIVE = ZAsset()
    logger.info("Cleared active asset cache")
    _ZASSET_TYPE_ACTIVE = ZAssetType()
    logger.info("Cleared active asset type cache")


@persistent
def load_post_handler(dummy):
    clear_cache_variables()


# ----------------REGISTER--------------

classes = [BZ_PopertyGroupSequence, BZ_PopertyGroupScene]


def register():

    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Sequence.blezou = bpy.props.PointerProperty(
        name="Blezou",
        type=BZ_PopertyGroupSequence,
        description="Metadata that is required for blezou",
    )
    bpy.types.Scene.blezou = bpy.props.PointerProperty(
        name="Blezou",
        type=BZ_PopertyGroupScene,
        description="Metadata that is required for blezou",
    )

    bpy.app.handlers.load_post.append(load_post_handler)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    # clear cache
    clear_cache_variables()
