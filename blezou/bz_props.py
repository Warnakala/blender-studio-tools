import bpy 

class BZ_PopertyGroup_VSEQ_Shot(bpy.types.PropertyGroup):

    shot: bpy.props.StringProperty(
        name='Shot',
        default=''
        # options={'HIDDEN', 'SKIP_SAVE'}
    )

    sequence: bpy.props.StringProperty(
        name='Seq',
        default=''
        # options={'HIDDEN', 'SKIP_SAVE'}
    )
    

classes = [
    BZ_PopertyGroup_VSEQ_Shot
]

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