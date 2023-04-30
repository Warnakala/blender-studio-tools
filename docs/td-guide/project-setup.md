# Project Setup

::: warning Work in Progress
30 Apr. 2023 - The content of this page is currently being edited/updated.
:::

* Setup SVN (access for users)
* Setup Kitsu project
* Commit intial folder structure

## Project Directory

```python
.
├── config
│   └── asset_pipeline_config
├── previz # Anything related to early development or pre-production tests
└── pro # All files from the production
    ├── promo # Promotional material. Often created near the end of production
    ├── animation_test # For pre-production
    ├── shot_builder # Studio tool configs
    ├── lib # All assets from the production
    │   ├── brushes
    │   ├── cam # Camera rig & setup
    │   ├── char # Characters & character variations
    │   ├── env # Environment asset libraries
    │   ├── fx # Effects
    │   ├── lgt # Lighting setups
    │   ├── maps # General textures and HDRIs
    │   ├── matlib # Materials
    │   ├── nodes # General Node groups
    │   ├── poselib # Pose libraries for animation
    │   ├── props
    │   ├── scripts
    │   └── sets
    └── shots #Structured into sequences
  ```

## Render Directory

```
.
├── chaches
├── delivery
│   ├── audio
│   ├── color_preview
│   ├── mux
│   └── video
├── editorial
│   ├── edit
│   ├── export
│   ├── fonts
│   ├── score
│   └── sfx
├── farm_output
│   ├── lib
│   └── shots
├── plates
├── shot_frames
└── shot_previews
```

## Shared Directory

```python
.
├── bts # Behind the scenes
├── concepts # Concept art and paintings
├── development # Piches and boards
├── inspiration # Various inspirations & references
├── music 
├── planning 
├── pr
├── resources 
├── script # Latest scripts for the movie
├── shot_packs # Shots for sharing online
├── training # Training produced for the production
└── videoref # Video shoots from animators
```
