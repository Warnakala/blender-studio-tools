from . import client as raw

from .cache import cache
from .sorting import sort_by_name
from .helpers import normalize_model_parameter

default = raw.default_client


@cache
def all_entities(client=default):
    """
    Returns:
        list: Retrieve all entities
    """
    return raw.fetch_all("entities", client=client)


@cache
def all_entity_types(client=default):
    """
    Returns:
        list: Entity types listed in database.
    """
    return sort_by_name(raw.fetch_all("entity-types", client=client))


@cache
def get_entity(entity_id, client=default):
    """
    Args:
        id (str, client=default): ID of claimed entity.

    Returns:
        dict: Retrieve entity matching given ID (It can be an entity of any
        kind: asset, shot, sequence or episode).
    """
    return raw.fetch_one("entities", entity_id, client=client)


@cache
def get_entity_by_name(entity_name, client=default):
    """
    Args:
        name (str, client=default): The name of the claimed entity.

    Returns:
        Retrieve entity matching given name.
    """
    return raw.fetch_first("entities", {"name": entity_name}, client=client)


@cache
def get_entity_type(entity_type_id, client=default):
    """
        Args:
            id (str, client=default): ID of claimed entity type.
    , client=client
        Returns:
            Retrieve entity type matching given ID (It can be an entity type of any
            kind).
    """
    return raw.fetch_one("entity-types", entity_type_id, client=client)


@cache
def get_entity_type_by_name(entity_type_name, client=default):
    """
    Args:
        name (str, client=default): The name of the claimed entity type

    Returns:
        Retrieve entity type matching given name.
    """
    return raw.fetch_first(
        "entity-types", {"name": entity_type_name}, client=client
    )


def new_entity_type(name, client=default):
    """
    Creates an entity type with the given name.

    Args:
        name (str, client=default): The name of the entity type

    Returns:
        dict: The created entity type
    """
    data = {"name": name}
    return raw.create("entity-types", data, client=client)


def remove_entity(entity, force=False, client=default):
    """
    Remove given entity from database.

    Args:
        entity (dict): Entity to remove.
    """
    entity = normalize_model_parameter(entity)
    path = "data/entities/%s" % entity["id"]
    params = {}
    if force:
        params = {"force": "true"}
    return raw.delete(path, params, client=client)

def update_entity(entity, client=default):
    """
    Save given shot data into the API. Metadata are fully replaced by the ones
    set on given shot.

    Args:
        Entity (dict): The shot dict to update.

    Returns:
        dict: Updated entity.
    """
    return raw.put(f"data/entities/{entity['id']}", entity, client=client)