from typing import Tuple, List, Optional
import re
from bpy.utils import flip_name

separators = "-_."


def get_name(thing) -> str:
    if hasattr(thing, 'name'):
        return thing.name
    else:
        return str(thing)


def make_name(prefixes=[], base="", suffixes=[],
              prefix_separator="-", suffix_separator=".") -> str:
    """Make a name from a list of prefixes, a base, and a list of suffixes."""
    name = ""
    for pre in prefixes:
        if pre == "":
            continue
        name += pre + prefix_separator
    name += base
    for suf in suffixes:
        if suf == "":
            continue
        name += suffix_separator + suf
    return name


def slice_name(name, prefix_separator="-", suffix_separator="."):
    """Break up a name into its prefix, base, suffix components."""
    prefixes = name.split(prefix_separator)[:-1]
    suffixes = name.split(suffix_separator)[1:]
    base = name.split(prefix_separator)[-1].split(suffix_separator)[0]
    return [prefixes, base, suffixes]


def has_trailing_zeroes(thing):
    name = get_name(thing)
    regex = "\.[0-9][0-9][0-9]$"
    search = re.search(regex, name)
    return search != None


def strip_trailing_numbers(name) -> Tuple[str, str]:
    if "." in name:
        # Check if there are only digits after the last period
        slices = name.split(".")
        after_last_period = slices[-1]
        before_last_period = ".".join(slices[:-1])

        # If there are only digits after the last period, discard them
        if all([c in "0123456789" for c in after_last_period]):
            return before_last_period, "."+after_last_period

    return name, ""


def get_side_lists(with_separators=False) -> Tuple[List[str], List[str], List[str]]:
    left = ['left',  'Left',  'LEFT',  'l',  'L',]
    right_placehold = ['*rgt*', '*Rgt*', '*RGT*', '*r*', '*R*']
    right = ['right', 'Right', 'RIGHT', 'r',  'R']

    # If the name is longer than 2 characters, only swap side identifiers if they
    # are next to a separator.
    if with_separators:
        for l in [left, right_placehold, right]:
            l_copy = l[:]
            for side in l_copy:
                if len(side) < 4:
                    l.remove(side)
                for sep in separators:
                    l.append(side+sep)
                    l.append(sep+side)

    return left, right_placehold, right


def side_is_left(name) -> Optional[bool]:
    """Identify whether a name belongs to the left or right side or neither."""

    flipped_name = flip_name(name)
    if flipped_name == name:
        return None  # Return None to indicate neither side.

    stripped_name, number_suffix = strip_trailing_numbers(name)

    def check_start_side(side_list, name):
        for side in side_list:
            if name.startswith(side):
                return True
        return False

    def check_end_side(side_list, name):
        for side in side_list:
            if name.endswith(side):
                return True
        return False

    left, right_placehold, right = get_side_lists(with_separators=True)

    is_left_prefix = check_start_side(left, stripped_name)
    is_left_suffix = check_end_side(left, stripped_name)

    is_right_prefix = check_start_side(right, stripped_name)
    is_right_suffix = check_end_side(right, stripped_name)

    # Prioritize suffix for determining the name's side.
    if is_left_suffix or is_right_suffix:
        return is_left_suffix

    # If no relevant suffix found, try prefix.
    if is_left_prefix or is_right_prefix:
        return is_left_prefix

    # If no relevant suffix or prefix found, try anywhere.
    any_left = any([side in name for side in left])
    any_right = any([side in name for side in right])
    if not any_left and not any_right:
        # If neither side found, return None.
        return None
    if any_left and not any_right:
        return True
    if any_right and not any_left:
        return False

    # If left and right were both found somewhere, I give up.
    return None
