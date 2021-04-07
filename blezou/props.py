import bpy


class BZ_PopertyGroup_VSEQ_Shot(bpy.types.PropertyGroup):
    """
    Property group that will be registered on sequence strips.
    They hold metadata that will be used to compose a data structure that can
    be pushed to backend.
    """

    # shot
    shot_id: bpy.props.StringProperty(name="Shot ID")
    shot_name: bpy.props.StringProperty(name="Shot", default="")
    shot_description: bpy.props.StringProperty(name="Description", default="")

    # sequence
    sequence_name: bpy.props.StringProperty(name="Seq", default="")
    sequence_id: bpy.props.StringProperty(name="Seq ID", default="")

    # project
    project_name: bpy.props.StringProperty(name="Project", default="")
    project_id: bpy.props.StringProperty(name="Project ID", default="")

    # meta
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
        self.shot_id = ""
        self.shot_name = ""
        self.shot_description = ""

        self.sequence_id = ""
        self.sequence_name = ""

        self.project_name = ""
        self.project_id = ""

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