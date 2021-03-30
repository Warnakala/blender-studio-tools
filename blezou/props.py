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
    description: bpy.props.StringProperty(name="Description", default="")
    initialized: bpy.props.BoolProperty(
        name="Initialized", default=False, description="Is Blezou shot"
    )
    linked: bpy.props.BoolProperty(
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
        self.id = ""
        self.shot = ""
        self.sequence = ""
        self.description = ""
        self.initialized = False
        self.linked = False


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