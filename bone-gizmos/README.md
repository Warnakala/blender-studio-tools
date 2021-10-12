# What are Bone Gizmos?
Bone Gizmos is a Blender addon that attempts an initial implementation of a feature which allows animators to interact with a character more conveniently, by using Blender's Gizmo API to create hoverable and clickable surfaces on the character which can be used to transform the rig.

This addon is in early experimental stages, and mainly made with the purpose to help guide the implementation of these features in core Blender, with the hopes that a developer is willing and able to take on the project. This is because certain UX and performance limitations are likely to be impossible to overcome in Python.

# Using Bone Gizmos
![](docs/armature_generate.gif)

The UI for Bone Gizmos can be found in the Properties Editor, under the Bone Tab->Viewport Display panel, when you're in pose mode and have an active bone. You just need to select a mesh and optionally, a vertex group or face map that the gizmo should be bound to.

# Report problems
If you run into errors or have suggestions, feel free to [open an issue](/../issues/new).
