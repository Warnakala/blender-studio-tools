from typing import List, Dict, Tuple, Optional, Type
import bpy
from bpy.types import KeyMapItem, Operator


def get_enum_values(bpy_type, enum_prop_name: str) -> Dict[str, Tuple[str, str]]:
    if isinstance(bpy_type, Operator):
        try:
            enum_items = bpy_type.__annotations__[
                enum_prop_name].keywords['items']
            return {e[0]: (e[1], e[2]) for e in enum_items}
        except:
            return

    enum_items = bpy_type.bl_rna.properties[enum_prop_name].enum_items
    return {e.identifier: (e.name, e.description) for e in enum_items}


def is_valid_key_id(key_id: str) -> bool:
    all_valid_key_identifiers = get_enum_values(KeyMapItem, 'type')
    is_valid = key_id in all_valid_key_identifiers
    if not is_valid:
        print("All valid key identifiers and names:")
        print("\n".join(list(all_valid_key_identifiers.items())))
        print(
            f'\nShortcut error: "{key_id}" is not a valid key identifier. Must be one of the above.')
    return is_valid


def is_valid_event_type(event_type: str) -> bool:
    all_valid_event_types = get_enum_values(KeyMapItem, 'value')
    is_valid = event_type in all_valid_event_types
    if not is_valid:
        print("All valid event names:")
        print("\n".join(list(all_valid_event_types.keys())))
        print(
            f'\nShortcut Error: "{event_type}" is not a valid event type. Must be one of the above.')
    return is_valid


def get_all_keymap_names() -> List[str]:
    return bpy.context.window_manager.keyconfigs.default.keymaps.keys()


def is_valid_keymap_name(km_name: str) -> bool:
    all_km_names = get_all_keymap_names()
    is_valid = km_name in all_km_names
    if not is_valid:
        print("All valid keymap names:")
        print("\n".join(all_km_names))
        print(
            f'\nShortcut Error: "{km_name}" is not a valid keymap name. Must be one of the above.')
    return is_valid


def get_space_type_of_keymap(km_name: str) -> str:
    return bpy.context.window_manager.keyconfigs.default.keymaps[km_name].space_type


def find_operator_class_by_bl_idname(bl_idname: str) -> Type[Operator]:
    for cl in Operator.__subclasses__():
        if cl.bl_idname == bl_idname:
            return cl


def find_keymap_item_by_trigger(
    keymap,
    bl_idname: str,
    key_id: str,
    ctrl=False,
    alt=False,
    shift=False,
    oskey=False
) -> Optional[KeyMapItem]:

    for kmi in keymap.keymap_items:
        if (
            kmi.idname == bl_idname and
            kmi.type == key_id and
            kmi.ctrl == ctrl and
            kmi.alt == alt and
            kmi.shift == shift and
            kmi.oskey == oskey
        ):
            return kmi


def find_keymap_item_by_op_kwargs(
    keymap,
    bl_idname: str,
    op_kwargs={}
) -> Optional[KeyMapItem]:

    for kmi in keymap.keymap_items:
        if kmi.idname != bl_idname:
            continue

        op_class = find_operator_class_by_bl_idname(bl_idname)

        if set(kmi.properties.keys()) != set(op_kwargs.keys()):
            continue

        any_mismatch = False
        for prop_name in kmi.properties.keys():
            # Check for enum string
            enum_dict = get_enum_values(op_class, prop_name)
            if enum_dict:
                value = enum_dict[op_kwargs[prop_name]]
            else:
                value = kmi.properties[prop_name]

            if value != op_kwargs[prop_name]:
                any_mismatch = True
                break

        if any_mismatch:
            continue

        return kmi


def register_hotkey(
        *,
        bl_idname: str,
        km_name='Window',
        key_id: str,

        event_type='PRESS',

        any=False,
        ctrl=False,
        alt=False,
        shift=False,
        oskey=False,
        key_modifier='NONE',
        direction='ANY',
        repeat=False,

        op_kwargs={}
):
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if not kc:
        # This happens when running Blender in background mode.
        return

    if not is_valid_keymap_name(km_name):
        return
    if not is_valid_key_id(key_id):
        return
    if not is_valid_event_type(event_type):
        return

    # If this keymap already exists, new() will return the existing one, which is confusing but ideal.
    km = kc.keymaps.new(
        name=km_name, space_type=get_space_type_of_keymap(km_name))

    kmi_existing = find_keymap_item_by_trigger(
        km,
        bl_idname=bl_idname,
        key_id=key_id,
        ctrl=ctrl,
        alt=alt,
        shift=shift,
        oskey=oskey
    )
    if kmi_existing:
        return

    kmi = km.keymap_items.new(
        bl_idname,
        type=key_id,
        value=event_type,

        any=any,
        ctrl=ctrl,
        alt=alt,
        shift=shift,
        oskey=oskey,
        key_modifier=key_modifier,

        direction=direction,
        repeat=repeat,
    )

    for key in op_kwargs:
        value = op_kwargs[key]
        setattr(kmi.properties, key, value)
