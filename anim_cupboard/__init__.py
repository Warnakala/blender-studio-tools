import importlib
from bpy.utils import register_class, unregister_class
from typing import List


from .operators import select_similar_curves
from .operators import lock_curves
from .operators import bake_anim_across_armatures
from . import easy_constraints
from . import warn_about_broken_libraries

bl_info = {
    'name' : "Animation Cupboard"
    ,'author': "Demeter Dzadik"
    ,'version' : (0, 0, 1)
    ,'blender' : (3, 2, 0)
    ,'description' : "Tools to improve animation workflows"
    ,'location': "Various"
    ,'category': 'Animation'
    # ,'doc_url' : "https://gitlab.com/blender/CloudRig/"
}

modules = (
    select_similar_curves,
    lock_curves,
    bake_anim_across_armatures,
    easy_constraints,
    warn_about_broken_libraries
)


def register_unregister_modules(modules: List, register: bool):
	"""Recursively register or unregister modules by looking for either
	un/register() functions or lists named `registry` which should be a list of 
	registerable classes.
	"""
	register_func = register_class if register else unregister_class

	for m in modules:
		if register:
			importlib.reload(m)
		if hasattr(m, 'registry'):
			for c in m.registry:
				try:
					register_func(c)
				except Exception as e:
					un = 'un' if not register else ''
					print(f"Warning: Failed to {un}register class: {c.__name__}")
					print(e)

		if hasattr(m, 'modules'):
			register_unregister_modules(m.modules, register)

		if register and hasattr(m, 'register'):
			m.register()
		elif hasattr(m, 'unregister'):
			m.unregister()

def register():
    register_unregister_modules(modules, True)

def unregister():
    register_unregister_modules(modules, False)
