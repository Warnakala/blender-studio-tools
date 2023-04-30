# In-file Prefixes

::: warning Work in Progress
30 Apr. 2023 - The content of this page is currently being edited/updated.
:::

## Collection names

We use prefixes only for top level collections of an asset. This is important to distinguish types of assets. The name of the asset itself should be lowercase.

- `CH` : Character
- `PR` : Prop
- `EN` : Environment asset
- `SE` : set
- `LG` : light rig

Example: `CH-phileas`

Sub-collections should start with the character's name and have dots as separators: `phileas.rig.widgets`

## Object naming

All objects should have a prefix, followed by a dash that determines their type:

- `WGT` : bone shapes
- `LGT` : light objects and mesh-lights, also shadow casters
- `HLP` : Empties and other helper objects that are not rendered
- `GEO` : Geometry, meshes, curves that contribute to the rendered appearance of the asset
- `RIG` : Rig and rig specific objects that do not appear in rendering
- `ENV` : matte paintings, sky-domes, fog volume objects
- `GPL` : grease pencil stroke objects (need to differentiate from GEO because can not be rendered on the farm)

Use dot uppercase L or R for objects that belong to one side and are mirrored 

Example: `GEO-dresser_drawer.L`

If a name contains a *of* relationship - in the above example the `drawer` of the `dresser` - these should not be separated by a dot, but rather with an underscore.

Another example: `GEO-ellie_watch_screw` and not `GEO-ellie_watch.screw`

If the watch had a variant of type `clean` and `dirty`, these would be using a dot to express the nature of the variant: `GEO-ellie_watch.clean` and `GEO-ellie_watch.dirty` 

## Actions

### Prefixes

Example: `PLB-spring.hand`

- `PLB` Pose library actions to be linked into animation files
- `RIG` Actions used by the rig's Action constraints
- `ANI` Animation to be used in a shot

More examples:

```txt
- ANI-rex.140_0020_A.v001
- ANI-ellie.060_scratch.layout.v001
- ANI-sprite_A.110_0100_A.v001
- PLB-rex_face.scared
- PLB-rex_face.happy
- PLB-rex_hand.closed
```
