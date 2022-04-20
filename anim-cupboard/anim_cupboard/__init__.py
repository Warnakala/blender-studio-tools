import importlib
from bpy.utils import register_class, unregister_class

from .operators import select_similar_curves
from .operators import lock_curves
from .operators import bake_anim_across_armatures

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
    bake_anim_across_armatures
)

def register():
    for m in modules:
        importlib.reload(m)
        if hasattr(m, 'registry'):
            for c in m.registry:
                register_class(c)
        if hasattr(m, 'register'):
            m.register()

def unregister():
    for m in reversed(modules):
        if hasattr(m, 'unregister'):
            m.unregister()
        if hasattr(m, 'registry'):
            for c in m.registry:
                unregister_class(c)