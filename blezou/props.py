import bpy


class BZ_PopertyGroup_VSEQ_Shot(bpy.types.PropertyGroup):
    """
    Property group that will be registered on sequence strips.
    They hold metadata that will be used to compose a data structure that can
    be pushed to backend.
    """

    id: bpy.props.StringProperty(name="ID")
    shot: bpy.props.StringProperty(name="Shot", default="")
    sequence: bpy.props.StringProperty(name="Seq", default="")
    description: bpy.props.StringProperty(name="Desciption", default="")
    initialized: bpy.props.BoolProperty(name="Is Blezou shot", default=False)


classes = [BZ_PopertyGroup_VSEQ_Shot]


def register():

    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Sequence.blezou = bpy.props.PointerProperty(
        name="Blezou",
        type=BZ_PopertyGroup_VSEQ_Shot,
        description="Metadata that is required for blezou",
    )


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)