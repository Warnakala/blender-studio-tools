# File Naming

::: warning Work in Progress
30 Apr. 2023 - The content of this page is currently being edited/updated.
:::

## Characters

**Location:** `{project root}/lib/char/{char subfolder}/{char name}.blend`

A character asset is a collection which contains shaded geometry, rigs, rigging objects such as mesh deformers and lattices. All of these are needed to give animators control over their movement and make up the final rendered representation of the character in the movie

## Props

**Location:** `{project root}/lib/prop/{prop subfolder}/{prop name}.blend`

A prop in real life is a rigged, animatable object which characters interact with or can be constrained to. An environment library asset can sometimes be turned into a prop (e.g. Autumn picks up a branch from the ground and breaks it into pieces).

## Environment library assets

**Location:** `{project root}/lib/env/{env subfolder}/{env name}.blend`

The building blocks needed to turn over sets and construct the movie stage. These are either static, or can be animated in a more limited way than props. Typically a larger set of them is needed with different variations, so we group them into asset library files. For example on *Spring* there was **trees.blend, rocks.blend**, etc. Each asset is in its own collection, but is also placed in a library collection that groups them together for easier linking access.

## Sets

**Location:** `{project root}/lib/set/{set subfolder}/{set name}.blend`

Sets are more tricky to define, since they can differ even on a shot level. In practice they are formed by a ground plane and dressed with environment assets. They can also contain individually created assets (*Spring* example: `riverbed.blend` contained two non-library trees which were modelled and shaded uniquely in this set). Sets can be connected together to build a larger world if necessary. Sets are contained in a main collection which has sub-collections for visibility management)

## Shots

**Location:** `{project root}**/**shots**/**{sequence number}**/**{shot identifier}/{shot identifier}.{task identifier}.blend`

## Textures and maps

**Location:** 

- `{project root}/lib/maps/` for general textures which are used across the entire project
- `{asset folder}/maps/` for specific textures related to an asset



Example: `dresser_wood.faded.col.png`

- As for all other files, format the entire name in lowercase, separated by `_` instead of spaces.
- Textures which are specific to a prop should include the name of the prop and THEN the name (if it's a label, or tex type such as metal or wood e.g.)
- If there's more than one type, Textures should also include the type (col, bump, nor, disp, spec) LAST in the filename (separated by a dot)
- make sure to clean up texture file names coming from the Blender Cloud according to these conventions. Sometimes there can be a .png.png at the end or files can have an uppercase first letter.
