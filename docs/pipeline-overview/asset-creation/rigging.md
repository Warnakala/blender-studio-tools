---
outline: deep
---

# Rigging

::: info
Original doc by Demeter, copied over from studio.blender.org. The original doc should be retired once this goes live.
:::


Our rigging workflow is based on procedurally generating control rigs, then manually weight painting and authoring corrective shape keys. We've built some custom tools to make these processes more efficient, foolproof and as iterative as possible. We try to tailor each rig to the needs of the animators on any given production.

We generally don't use any fancy tech like muscle systems or physics simulations for our character deformations. Just good old bones and shape key correctives. This is partially due to technical limitations, but also because the art styles we've aimed for didn't rely on anything more complex, so far.

## Generating Control Rigs
When a character model is fresh out of modeling/retopo, generating the control rig is the first step in rigging it. The control rig is generated using CloudRig, our extension to Blender's Rigify add-on. Features in CloudRig are tweaked and added according to the needs of our production, which means we often get to re-use old procedurally generating rig elements, thereby making our work more efficient and flexible over time as we get more and more varied productions under our belt.

* [CloudRig Repo/Download](https://gitlab.com/blender/CloudRig)  
* [CloudRig Video Documentation](https://studio.blender.org/training/blender-studio-rigging-tools/)   
* Example Character Rigs: [Settlers](https://studio.blender.org/films/settlers/5e8f16fd9e1df355918c30e9/), [Sprite Fright](https://studio.blender.org/characters/)

## Weight Painting
Weight painting character meshes to the generated rig has so far happened simply manually, as there hasn't been a need to mass produce characters with high quality deformation. Still, the **Easy Weight** add-on helps to make this manual weight painting workflow efficient and foolproof. There is also a short series about this add-on combined with the fundamentals of weight painting, where I also describe my personal preferred painting workflow.  

* [Easy Weight Repo/Download](https://gitlab.com/blender/easy_weight)  
* [Weight Painting Course](https://studio.blender.org/training/weight-painting/)

## Corrective Shape Keys
Normally, the control rig and the weight painting has to be finalized before corrective shape keys can be authored, but our workflow with the **Pose Shape Keys** add-on allows us to make changes to the rig and the weights while preserving the resulting corrective shapes.

* Pose Shape Keys is part of the [blender-studio-tools repo](https://projects.blender.org/studio/blender-studio-tools)  
* [Pose Shape Keys Tutorial Video](https://studio.blender.org/training/blender-studio-rigging-tools/pose-shape-keys/)
