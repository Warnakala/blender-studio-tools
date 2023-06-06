from blender_kitsu import gazu
from . import client as raw
from .sorting import sort_by_name

from .cache import cache
from .helpers import normalize_model_parameter

default = raw.default_client

@cache
def get_all_edits(relations=False, client=default):
    """
    Retrieve all edit entries.
    """
    params = {}
    if relations:
        params = {"relations": "true"}
    path = "edits/all"
    edits = raw.fetch_all(path, params, client=client)
    return sort_by_name(edits)

@cache
def get_edit(edit_id, relations=False, client=default):
    """
    Retrieve all edit entries.
    """
    edit_entry = normalize_model_parameter(edit_id)
    params = {}
    if relations:
        params = {"relations": "true"}
    path = f"edits/{edit_entry['id']}"
    edit_entry = raw.fetch_all(path, params, client=client)
    return edit_entry

@cache
def get_all_edits_with_tasks(relations=False, client=default):
    """
    Retrieve all edit entries.
    """
    params = {}
    if relations:
        params = {"relations": "true"}
    path = "edits/with-tasks"
    edits_with_tasks = raw.fetch_all(path, params, client=client)
    return sort_by_name(edits_with_tasks)

@cache
def get_all_previews_for_edit(edit, client=default):
    """
    Args:
        episode (str / dict): The episode dict or the episode ID.

    Returns:
        list: Shots which are children of given episode.
    """
    edit = normalize_model_parameter(edit)
    edit_previews = (raw.fetch_all(f"edits/{edit['id']}/preview-files", client=client))
    for key in [key for key in enumerate(edit_previews.keys())]:
        return edit_previews[key[1]]