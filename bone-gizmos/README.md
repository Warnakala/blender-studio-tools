# What are Bone Gizmos?
Bone Gizmos is a Blender addon that attempts an initial implementation of a feature which allows animators to interact with a character more conveniently, by using Blender's Gizmo API to create hoverable and clickable surfaces on the character which can be used to transform the rig.

This addon is in early experimental stages, the current goal is to gather feedback and to help guide the implementation of these features in core Blender, with the hopes that a developer is willing and able to take on the project. This is because certain UX and performance limitations are likely to be impossible to overcome in Python, or at the very least the Python Gizmo API would need some improvements from Blender's side.

# Using Bone Gizmos
The UI for Bone Gizmos can be found under Properties Editor->Bone->Viewport Display->Custom Gimzo. You need to be in pose mode and have an active bone. You just need to select a mesh and optionally, a vertex group or face map that the gizmo should be bound to.

### Rigger UX
- Enable Custom Gizmo on the bone. Gizmos are not mutually exclusive with Custom Shapes. You should either assign an empty object as the Custom Shape, or simply disable the Bones overlay.
- Select an object. Until a vertex group or face map is selected, the whole object will be used. In this case, the Custom Shape Offset values will affect the gizmo. If you do select a face map or vertex group, the offset will not be used.
- Assign default interaction behaviour for when the animator click&drags the gizmo: None, Translate, Rotate, Scale.
    The purpose of this setting is to make the most common way of interacting with an individual bone as fast as possible, but it is NOT to restrict the bone to only that method of interaction. This is different from bone transformation locks. This can actually be used **instead of** transformation locks, because they give the animator a **suggestion** without restricting them.
    - None: Just select the gizmo when clicked. Dragging will do nothing.
    - Translate & Scale: Optionally locked to one or two axes (Until you press G,R,S or X,Y,Z).
    - Rotate: Along View, Trackball, or along the bone's local X, Y, or Z

- **Colors**: The gizmo's color is determined by the bone group "normal" color. Selected/Active/Hovered states are marked by different opacity levels, which can be controlled in the addon preferences.
- Custom operators can be hooked up to each gizmo: The provided operator will be executed when the gizmo is clicked. This allows automatic IK/FK switching and snapping to happen when certain gizmos are interacted with. There's no UI for providing the operator's name and arguments. Instead, you have to feed all that data into a custom property, stored on the rig data. See [this](https://developer.blender.org/F12799095) example file.

### Animator UX

- Gizmos are only visible for armatures which you are in pose mode on.
- Clicking the gizmo always selects the bone, and starts the default transformation, if one is assigned in the rig. 
- Shift+Clicking toggles the selection.

### Possible future features

- Holding a key to make all gizmos visible.
- Let gizmo opacity increase based on distance from mouse cursor. This could result in less aimless wandering of the mouse when trying to find the right gizmo.
- Although more of a separate project, a 2D picker system could potentially further complement this system.
