from typing import Any, Dict, List, Set, Union, Optional
import bpy

from asset_pipeline.api import hook, Wildcard, DoNotMatch

"""
Hooks can be matched with the following parameters.
As match input you can use str, list, WildCard, DoNotMatch

Examples:
- Global Hooks (No match filter):                  @hook()
- Hooks for an asset type only:                    @hook(match_asset_type="Character")
- Hooks for a specific asset:                      @hook(match_asset: "Sprite")
- Hooks for a task layer only                      @hook(match_task_layers: ["ShadingTaskLayer", "RiggingTaskLayer"]
- Hooks for an asset and a task layer combination: @hook(macth_asset: "Sprite", match_task_layers: "ShadingTaskLayer")
Note: the decorator needs to be executed.

It is important to note that the asset-pipeline follows a certain order to execute the hooks. And that is exactly the one of the examples hook described above:

1. Global hooks
2. Asset Type Hooks
3. Task Layer Hooks
4. Asset Hooks
5. Asset + TaskLayer specific Hooks


The function itself should always have **\*\*kwargs** as a parameter. The asset-pipeline automatically passes a couple of useful keyword arguments to the function:
- `asset_collection`: bpy.types.Collection
- `context`: bpy.types.Context
- `asset_task`: asset_pipeline.asset_files.AssetTask
- `asset_dir`: asset_pipeline.asset_files.AssetDir

By exposing these parameters in the hook function you can use them in your code.
"""

@hook(
	match_task_layers="ModelingTaskLayer",
)
def geometry_cleanup(context: bpy.types.Context, asset_collection: bpy.types.Collection, **kwargs) -> None:
	for ob in asset_collection.all_objects:
		if not ob.data:
			continue
		if not ob.type == 'MESH': # TODO: Support other object types
			continue
		# make meshes single user
		if ob.data.users > 1:
			ob.data = ob.data.copy()

		# check for modifiers to apply
		if not [mod for mod in ob.modifiers if mod.name.split('-')[0]=='APL']:
			continue

		# remember modifier visibility
		mod_vis = []
		for i, mod in enumerate(ob.modifiers):
			if mod.name.split('-')[0] != 'APL':
				if mod.show_viewport:
					mod_vis += [i]
				mod.show_viewport = False

		# apply modifiers
		depsgraph = context.evaluated_depsgraph_get()
		old_mesh = ob.data
		ob.data = bpy.data.meshes.new_from_object(ob.evaluated_get(depsgraph))
		ob.data.name = old_mesh.name
		bpy.data.meshes.remove(old_mesh)

		for i in mod_vis[::-1]:
			ob.modifiers[i].show_viewport = True
		for mod in ob.modifiers:
			if mod.name.split('-')[0] == 'APL':
				ob.modifiers.remove(mod)


@hook(
	match_task_layers="ShadingTaskLayer",
)
def set_preview_shading(context: bpy.types.Context, asset_collection: bpy.types.Collection, **kwargs) -> None:
	for ob in asset_collection.all_objects:
		if not ob.data:
			continue
		if not ob.type == 'MESH':
			continue

		# Set 'PREVIEW' vertex color layer as active
		for idx, vcol in enumerate(ob.data.vertex_colors):
			if vcol.name == "PREVIEW":
				ob.data.vertex_colors.active_index = idx
				break

		# Set 'Baking' or 'UVMap' uv layer as active
		for idx, uvlayer in enumerate(ob.data.uv_layers):
			if uvlayer.name == "Baking":
				ob.data.uv_layers.active_index = idx
				break
			if uvlayer.name == "UVMap":
				ob.data.uv_layers.active_index = idx

		# Select preview texture as active if found
		for mslot in ob.material_slots:
			if not mslot.material or not mslot.material.node_tree:
				continue
			for node in mslot.material.node_tree.nodes:
				if not node.type == "TEX_IMAGE":
					continue
				if not node.image:
					continue
				if "preview" in node.image.name:
					mslot.material.node_tree.nodes.active = node
					break
