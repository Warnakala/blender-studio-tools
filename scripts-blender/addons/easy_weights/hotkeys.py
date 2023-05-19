import bpy

def register_hotkey(bl_idname, hotkey_kwargs, *, key_cat='Window', space_type='EMPTY', **op_kwargs):
    wm = bpy.context.window_manager
    addon_keyconfig = wm.keyconfigs.addon
    if not addon_keyconfig:
        # This happens when running Blender in background mode.
        return
    keymaps = addon_keyconfig.keymaps

    km = keymaps.get(key_cat)
    if not km:
        km = keymaps.new(name=key_cat, space_type=space_type)

    if bl_idname not in km.keymap_items:
        kmi = km.keymap_items.new(bl_idname, **hotkey_kwargs)
    else:
        kmi = km.keymap_items[bl_idname]

    kmi = km.keymap_items.new(bl_idname, **hotkey_kwargs)

    for key in op_kwargs:
        value = op_kwargs[key]
        setattr(kmi.properties, key, value)

def delayed_register_easyweight_hotkeys():
    register_hotkey(
        'paint.weight_paint',
        hotkey_kwargs={
            'type': 'LEFTMOUSE',
            'value': 'PRESS'
        },
        key_cat='Weight Paint',
        space_type='VIEW_3D',
        mode='NORMAL'
    )
    register_hotkey(
        'paint.weight_paint',
        hotkey_kwargs={
            'type': 'LEFTMOUSE',
            'value': 'PRESS', 'ctrl': True
        },
        key_cat='Weight Paint',
        space_type='VIEW_3D',
        mode='INVERT'
    )
    register_hotkey(
        'paint.weight_paint',
        hotkey_kwargs={
            'type': 'LEFTMOUSE',
            'value': 'PRESS',
            'shift': True
        },
        key_cat='Weight Paint',
        space_type='VIEW_3D',
        mode='SMOOTH'
    )

    register_hotkey(
        'object.custom_weight_paint_context_menu',
        hotkey_kwargs={
            'type': 'W',
            'value': 'PRESS',
        },
        key_cat='Weight Paint',
        space_type='VIEW_3D',
    )

    print("Registered EasyWeight Hotkeys.")

def register():
    bpy.app.timers.register(delayed_register_easyweight_hotkeys, first_interval=3)