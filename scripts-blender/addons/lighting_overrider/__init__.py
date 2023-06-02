from . import categories
from .categories import *
from . import templates, json_io, execution, ui, override_picker


bl_info = {
	"name": "Lighting Overrider",
	"author": "Simon Thommes",
	"version": (0, 1, 0),
	"blender": (3, 0, 0),
	"location": "3D Viewport > Sidebar > Overrides",
	"description": "Tool for the Blender Studio to create, manage and store local python overrides of linked data on a shot and sequence level.",
	"category": "Workflow",
}

modules = [templates]
modules += [globals()[mod] for mod in categories.__all__]
modules += [json_io, execution, ui, override_picker]

def register():
	for m in modules:
	    m.register()
    
def unregister():
	for m in modules:
	    m.unregister()