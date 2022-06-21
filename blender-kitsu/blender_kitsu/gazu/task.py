import string
import json

from gazu.exception import TaskStatusNotFound

from . import client as raw
from .sorting import sort_by_name
from .helpers import (
    download_file,
    normalize_model_parameter,
    normalize_list_of_models_for_links,
)

from .cache import cache

default = raw.default_client


@cache
def all_task_statuses(client=default):
    """
    Returns:
        list: Task statuses stored in database.
    """
    task_statuses = raw.fetch_all("task-status", client=client)
    return sort_by_name(task_statuses)


@cache
def all_task_types(client=default):
    """
    Returns:
        list: Task types stored in database.
    """
    task_types = raw.fetch_all("task-types", client=client)
    return sort_by_name(task_types)


@cache
def all_task_types_for_project(project, client=default):
    """
    Returns:
        list: Task types stored in database.
    """
    project = normalize_model_parameter(project)
    task_types = raw.fetch_all(
        "projects/%s/task-types" % project["id"], client=client
    )
    return sort_by_name(task_types)


@cache
def all_task_statuses_for_project(project, client=default):
    """
    Returns:
        list: Task status stored in database.
    """
    project = normalize_model_parameter(project)
    task_statuses = raw.fetch_all(
        "projects/%s/settings/task-status" % project["id"], client=client
    )
    return sort_by_name(task_statuses)


@cache
def all_tasks_for_shot(shot, relations=False, client=default):
    """
    Args:
        shot (str / dict): The shot dict or the shot ID.

    Returns:
        list: Tasks linked to given shot.
    """
    shot = normalize_model_parameter(shot)
    params = {}
    if relations:
        params = {"relations": "true"}
    tasks = raw.fetch_all("shots/%s/tasks" % shot["id"], params, client=client)
    return sort_by_name(tasks)


@cache
def all_tasks_for_sequence(sequence, relations=False, client=default):
    """
    Args:
        sequence (str / dict): The sequence dict or the sequence ID.

    Returns
        list: Tasks linked to given sequence.
    """
    sequence = normalize_model_parameter(sequence)
    params = {}
    if relations:
        params = {"relations": "true"}
    path = "sequences/%s/tasks" % sequence["id"]
    tasks = raw.fetch_all(path, params, client=client)
    return sort_by_name(tasks)


@cache
def all_tasks_for_scene(scene, relations=False, client=default):
    """
    Args:
        sequence (str / dict): The scene dict or the scene ID.

    Returns:
        list: Tasks linked to given scene.
    """
    scene = normalize_model_parameter(scene)
    params = {}
    if relations:
        params = {"relations": "true"}
    path = "scenes/%s/tasks" % scene["id"]
    tasks = raw.fetch_all(path, params, client=client)
    return sort_by_name(tasks)


@cache
def all_tasks_for_asset(asset, relations=False, client=default):
    """
    Args:
        asset (str / dict): The asset dict or the asset ID.

    Returns:
        list: Tasks directly linked to given asset.
    """
    asset = normalize_model_parameter(asset)
    params = {}
    if relations:
        params = {"relations": "true"}
    path = "assets/%s/tasks" % asset["id"]
    tasks = raw.fetch_all(path, params, client=client)
    return sort_by_name(tasks)


@cache
def all_tasks_for_episode(episode, relations=False, client=default):
    """
    Retrieve all tasks directly linked to given episode.
    """
    episode = normalize_model_parameter(episode)
    params = {}
    if relations:
        params = {"relations": "true"}
    path = "episodes/%s/tasks" % episode["id"]
    tasks = raw.fetch_all(path, params, client=client)
    return sort_by_name(tasks)


@cache
def all_shot_tasks_for_sequence(sequence, relations=False, client=default):
    """
    Retrieve all tasks directly linked to all shots of given sequence.
    """
    sequence = normalize_model_parameter(sequence)
    params = {}
    if relations:
        params = {"relations": "true"}
    path = "sequences/%s/shot-tasks" % sequence["id"]
    tasks = raw.fetch_all(path, params, client=client)
    return sort_by_name(tasks)


@cache
def all_shot_tasks_for_episode(episode, relations=False, client=default):
    """
    Retrieve all tasks directly linked to all shots of given episode.
    """
    episode = normalize_model_parameter(episode)
    params = {}
    if relations:
        params = {"relations": "true"}
    path = "episodes/%s/shot-tasks" % episode["id"]
    tasks = raw.fetch_all(path, params, client=client)
    return sort_by_name(tasks)


@cache
def all_assets_tasks_for_episode(episode, relations=False, client=default):
    """
    Retrieve all tasks directly linked to all assets of given episode.
    """
    episode = normalize_model_parameter(episode)
    params = {}
    if relations:
        params = {"relations": "true"}
    path = "episodes/%s/asset-tasks" % episode["id"]
    tasks = raw.fetch_all(path, params, client=client)
    return sort_by_name(tasks)


@cache
def all_tasks_for_task_status(project, task_type, task_status, client=default):
    """
    Args:
        project (str / dict): The project dict or the project ID.
        task_type (str / dict): The task type dict or ID.
        task_status (str / dict): The task status dict or ID.

    Returns:
        list: Tasks set at given status for given project and task type.
    """
    project = normalize_model_parameter(project)
    task_type = normalize_model_parameter(task_type)
    task_status = normalize_model_parameter(task_status)
    return raw.fetch_all(
        "tasks",
        {
            "project_id": project["id"],
            "task_type_id": task_type["id"],
            "task_status_id": task_status["id"],
        },
        client=client,
    )


@cache
def all_tasks_for_task_type(project, task_type, client=default):
    """
    Args:
        project (str / dict): The project dict or the project ID.
        task_type (str / dict): The task type dict or ID.

    Returns:
        list: Tasks for given project and task type.
    """
    project = normalize_model_parameter(project)
    task_type = normalize_model_parameter(task_type)
    return raw.fetch_all(
        "tasks",
        {
            "project_id": project["id"],
            "task_type_id": task_type["id"],
        },
        client=client,
    )


@cache
def all_task_types_for_shot(shot, client=default):
    """
    Args:
        shot (str / dict): The shot dict or the shot ID.

    Returns
        list: Task types of task linked to given shot.
    """
    shot = normalize_model_parameter(shot)
    path = "shots/%s/task-types" % shot["id"]
    task_types = raw.fetch_all(path, client=client)
    return sort_by_name(task_types)


@cache
def all_task_types_for_asset(asset, client=default):
    """
    Args:
        asset (str / dict): The asset dict or the asset ID.

    Returns:
        list: Task types of tasks related to given asset.
    """
    asset = normalize_model_parameter(asset)
    task_types = raw.fetch_all(
        "assets/%s/task-types" % asset["id"], client=client
    )
    return sort_by_name(task_types)


@cache
def all_task_types_for_scene(scene, client=default):
    """
    Args:
        scene (str / dict): The scene dict or the scene ID.

    Returns:
        list: Task types of tasks linked to given scene.
    """
    scene = normalize_model_parameter(scene)
    path = "scenes/%s/task-types" % scene["id"]
    task_types = raw.fetch_all(path, client=client)
    return sort_by_name(task_types)


@cache
def all_task_types_for_sequence(sequence, client=default):
    """
    Args:
        sequence (str / dict): The sequence dict or the sequence ID.

    Returns:
        list: Task types of tasks linked directly to given sequence.
    """
    sequence = normalize_model_parameter(sequence)
    path = "sequences/%s/task-types" % sequence["id"]
    task_types = raw.fetch_all(path, client=client)
    return sort_by_name(task_types)


@cache
def all_task_types_for_episode(episode, client=default):
    """
    Returns:
        list: Task types of tasks linked directly to given episode.
    """
    episode = normalize_model_parameter(episode)
    path = "episodes/%s/task-types" % episode["id"]
    task_types = raw.fetch_all(path, client=client)
    return sort_by_name(task_types)


@cache
def all_tasks_for_entity_and_task_type(entity, task_type, client=default):
    """
    Args:
        entity (str / dict): The entity dict or the entity ID.
        task_type (str / dict): The task type dict or ID.

    Returns:
        list: Tasks for given entity or task type.
    """
    entity = normalize_model_parameter(entity)
    task_type = normalize_model_parameter(task_type)
    task_type_id = task_type["id"]
    entity_id = entity["id"]
    path = "entities/%s/task-types/%s/tasks" % (entity_id, task_type_id)
    return raw.fetch_all(path, client=client)


@cache
def all_tasks_for_person(person, client=default):
    """
    Returns:
        list: Tasks that are not done for given person (only for open projects).
    """
    person = normalize_model_parameter(person)
    return raw.fetch_all("persons/%s/tasks" % person["id"], client=client)


@cache
def all_done_tasks_for_person(person, client=default):
    """
    Returns:
        list: Tasks that are done for given person (only for open projects).
    """
    person = normalize_model_parameter(person)
    return raw.fetch_all("persons/%s/done-tasks" % person["id"], client=client)


@cache
def get_task_by_entity(entity, task_type, client=default):
    return get_task_by_name(entity, task_type, client=client)


@cache
def get_task_by_name(entity, task_type, name="main", client=default):
    """
    Args:
        entity (str / dict): The entity dict or the entity ID.
        task_type (str / dict): The task type dict or ID.
        name (str): Name of the task to look for.

    Returns:
        Task matching given name for given entity and task type.
    """
    entity = normalize_model_parameter(entity)
    task_type = normalize_model_parameter(task_type)
    return raw.fetch_first(
        "tasks",
        {
            "name": name,
            "task_type_id": task_type["id"],
            "entity_id": entity["id"],
        },
        client=client,
    )


@cache
def get_task_type(task_type_id, client=default):
    """
    Args:
        task_type_id (str): Id of claimed task type.

    Returns:
        dict: Task type matching given ID.
    """
    return raw.fetch_one("task-types", task_type_id, client=client)


@cache
def get_task_type_by_name(task_type_name, client=default):
    """
    Args:
        task_type_name (str): Name of claimed task type.

    Returns:
        dict: Task type object for given name.
    """
    return raw.fetch_first(
        "task-types", {"name": task_type_name}, client=client
    )


@cache
def get_task_by_path(project, file_path, entity_type="shot", client=default):
    """
    Args:
        project (str / dict): The project dict or the project ID.
        file_path (str): The file path to find a related task.
        entity_type (str): asset, shot or scene.

    Returns:
        dict: A task from given file path. This function requires context:
        the project related to the given path and the related entity type.
    """
    project = normalize_model_parameter(project)
    data = {
        "file_path": file_path,
        "project_id": project["id"],
        "type": entity_type,
    }
    return raw.post("data/tasks/from-path/", data, client=client)


@cache
def get_task_status(task_status_id, client=default):
    """
    Args:
        task_status_id (str): Id of claimed task status.

    Returns:
        dict: Task status matching given ID.
    """
    return raw.fetch_one("task-status", task_status_id, client=client)


@cache
def get_task_status_by_name(name, client=default):
    """
    Args:
        name (str / dict): The name of claimed task status.

    Returns:
        dict: Task status matching given name.
    """
    return raw.fetch_first("task-status", {"name": name}, client=client)


@cache
def get_default_task_status(client=default):
    """
    Args:
        name (str / dict): The name of claimed task status.

    Returns:
        dict: Task status matching given name.
    """
    return raw.fetch_first("task-status", {"is_default": True}, client=client)


@cache
def get_task_status_by_short_name(task_status_short_name, client=default):
    """
    Args:
        short_name (str / dict): The short name of claimed task status.

    Returns:
        dict: Task status matching given short name.
    """
    return raw.fetch_first(
        "task-status", {"short_name": task_status_short_name}, client=client
    )


def remove_task_type(task_type, client=default):
    """
    Remove given task type from database.

    Args:
        task_type (str / dict): The task type dict or ID.
    """
    task_type = normalize_model_parameter(task_type)
    return raw.delete(
        "data/task-types/%s" % task_type["id"],
        {"force": "true"},
        client=client,
    )


def remove_task_status(task_status, client=default):
    """
    Remove given task status from database.

    Args:
        task_status (str / dict): The task status dict or ID.
    """
    task_status = normalize_model_parameter(task_status)
    return raw.delete(
        "data/task-status/%s" % task_status["id"],
        {"force": "true"},
        client=client,
    )


@cache
def get_task(task_id, client=default):
    """
    Args:
        task_id (str): Id of claimed task.

    Returns:
        dict: Task matching given ID.
    """
    task_id = normalize_model_parameter(task_id)
    return raw.get("data/tasks/%s/full" % task_id["id"], client=client)


def new_task(
    entity,
    task_type,
    name="main",
    task_status=None,
    assigner=None,
    assignees=[],
    client=default,
):
    """
    Create a new task for given entity and task type.

    Args:
        entity (dict): Entity for which task is created.
        task_type (dict): Task type of created task.
        name (str): Name of the task (default is "main").
        task_status (dict): The task status to set (default status is Todo).
        assigner (dict): Person who assigns the task.
        assignees (list): List of people assigned to the task.

    Returns:
        Created task.
    """
    entity = normalize_model_parameter(entity)
    task_type = normalize_model_parameter(task_type)
    if task_status is None:
        task_status = get_default_task_status()

    data = {
        "project_id": entity["project_id"],
        "entity_id": entity["id"],
        "task_type_id": task_type["id"],
        "task_status_id": task_status["id"],
        "assignees": normalize_list_of_models_for_links(assignees),
        "name": name,
    }

    if assigner is not None:
        data["assigner_id"] = normalize_model_parameter(assigner)["id"]

    task = get_task_by_name(entity, task_type, name, client=client)
    if task is None:
        task = raw.post("data/tasks", data, client=client)
    return task


def remove_task(task, client=default):
    """
    Remove given task from database.

    Args:
        task (str / dict): The task dict or the task ID.
    """
    task = normalize_model_parameter(task)
    raw.delete("data/tasks/%s" % task["id"], {"force": "true"}, client=client)


def start_task(task, started_task_status=None, client=default):
    """
    Create a comment to change task status to started_task_status
    (by default WIP) and set its real start date to now.

    Args:
        task (str / dict): The task dict or the task ID.

    Returns:
        dict: Created comment.
    """
    if started_task_status is None:
        started_task_status = get_task_status_by_short_name(
            "wip", client=client
        )
        if started_task_status is None:
            raise TaskStatusNotFound(
                (
                    "started_task_status is None : 'wip' task status is "
                    "non-existent. You have to create it or to set an other "
                    "task status for started_task_status in the parameters "
                    "of the function."
                )
            )

    return add_comment(task, started_task_status, client=client)


def task_to_review(
    task, person, comment, revision=1, change_status=True, client=default
):
    """
    Deprecated.
    Mark given task as pending, waiting for approval. Author is given through
    the person argument.

    Args:
        task (str / dict): The task dict or the task ID.
        person (str / dict): The person dict or the person ID.
        comment (str): Comment text
        revision (int): Force revision of related preview file
        change_status (bool): If set to false, the task status is not changed.

    Returns:
        dict: Modified task
    """
    task = normalize_model_parameter(task)
    person = normalize_model_parameter(person)
    path = "actions/tasks/%s/to-review" % task["id"]
    data = {
        "person_id": person["id"],
        "comment": comment,
        "revision": revision,
        "change_status": change_status,
    }

    return raw.put(path, data, client=client)


@cache
def get_time_spent(task, date, client=default):
    """
    Get the time spent by CG artists on a task at a given date. A field contains
    the total time spent.  Durations are given in seconds. Date format is
    YYYY-MM-DD.

    Args:
        task (str / dict): The task dict or the task ID.
        date (str): The date for which time spent is required.

    Returns:
        dict: A dict with person ID as key and time spent object as value.
    """
    task = normalize_model_parameter(task)
    path = "actions/tasks/%s/time-spents/%s" % (task["id"], date)
    return raw.get(path, client=client)


def set_time_spent(task, person, date, duration, client=default):
    """
    Set the time spent by a CG artist on a given task at a given date. Durations
    must be set in seconds. Date format is YYYY-MM-DD.

    Args:
        task (str / dict): The task dict or the task ID.
        person (str / dict): The person who spent the time on given task.
        date (str): The date for which time spent must be set.
        duration (int): The duration of the time spent on given task.

    Returns:
        dict: Created time spent entry.
    """
    task = normalize_model_parameter(task)
    person = normalize_model_parameter(person)
    path = "actions/tasks/%s/time-spents/%s/persons/%s" % (
        task["id"],
        date,
        person["id"],
    )
    return raw.post(path, {"duration": duration}, client=client)


def add_time_spent(task, person, date, duration, client=default):
    """
    Add given duration to the already logged duration for given task and person
    at a given date. Durations must be set in seconds. Date format is
    YYYY-MM-DD.

    Args:
        task (str / dict): The task dict or the task ID.
        person (str / dict): The person who spent the time on given task.
        date (str): The date for which time spent must be added.
        duration (int): The duration to add on the time spent on given task.

    Returns:
        dict: Updated time spent entry.
    """
    task = normalize_model_parameter(task)
    person = normalize_model_parameter(person)
    path = "actions/tasks/%s/time-spents/%s/persons/%s/add" % (
        task["id"],
        date,
        person["id"],
    )
    return raw.post(path, {"duration": duration}, client=client)


def add_comment(
    task,
    task_status,
    comment="",
    person=None,
    checklist=[],
    attachments=[],
    created_at=None,
    client=default,
):
    """
    Add comment to given task. Each comment requires a task_status. Since the
    addition of comment triggers a task status change. Comment text can be
    empty.

    Args:
        task (str / dict): The task dict or the task ID.
        task_status (str / dict): The task status dict or ID.
        comment (str): Comment text
        person (str / dict): Comment author
        date (str): Comment date

    Returns:
        dict: Created comment.
    """
    task = normalize_model_parameter(task)
    task_status = normalize_model_parameter(task_status)
    data = {
        "task_status_id": task_status["id"],
        "comment": comment,
        "checklist": checklist,
    }

    if person is not None:
        person = normalize_model_parameter(person)
        data["person_id"] = person["id"]

    if created_at is not None:
        data["created_at"] = created_at

    if len(attachments) == 0:
        return raw.post(
            "actions/tasks/%s/comment" % task["id"], data, client=client
        )
    else:
        attachment = attachments.pop()
        data["checklist"] = json.dumps(checklist)
        return raw.upload(
            "actions/tasks/%s/comment" % task["id"],
            attachment,
            data=data,
            extra_files=attachments,
            client=client,
        )


def add_attachment_files_to_comment(
    task, comment, attachments=[], client=default
):
    """
    Add attachments files to a given comment.

    Args:
        task (dict / ID): The task dict or the task ID.
        comment (dict / ID): The comment dict or the comment ID.
        attachments (list / str) : A list of path for attachments or directly the path.

    Returns:
        dict: Added attachment files.
    """
    if isinstance(attachments, str):
        attachments = [attachments]
    if len(attachments) == 0:
        raise ValueError("The attachments list is empty")
    task = normalize_model_parameter(task)
    comment = normalize_model_parameter(comment)
    attachment = attachments.pop()
    return raw.upload(
        "actions/tasks/%s/comments/%s/add-attachment"
        % (task["id"], comment["id"]),
        attachment,
        extra_files=attachments,
        client=client,
    )


def get_comment(comment_id, client=default):
    """
    Get comment instance

    Args:
        comment_id (ID): The comment ID.

    Returns:
        dict: Given comment instance.
    """
    return raw.fetch_one("comments", comment_id, client=client)


def remove_comment(comment, client=default):
    """
    Remove given comment and related (previews, news, notifications) from
    database.

    Args:
        comment (str / dict): The comment dict or the comment ID.
    """
    comment = normalize_model_parameter(comment)
    return raw.delete("data/comments/%s" % (comment["id"]), client=client)


def create_preview(task, comment, client=default):
    """
    Create a preview into given comment.

    Args:
        task (str / dict): The task dict or the task ID.
        comment (str / dict): The comment or the comment ID.

    Returns:
        dict: Created preview file model.
    """
    task = normalize_model_parameter(task)
    comment = normalize_model_parameter(comment)
    path = "actions/tasks/%s/comments/%s/add-preview" % (
        task["id"],
        comment["id"],
    )
    return raw.post(path, {}, client=client)


def upload_preview_file(
    preview, file_path, normalize_movie=True, client=default
):
    """
    Create a preview into given comment.

    Args:
        task (str / dict): The task dict or the task ID.
        file_path (str): Path of the file to upload as preview.
    """
    path = (
        "pictures/preview-files/%s" % normalize_model_parameter(preview)["id"]
    )
    if not normalize_movie:
        path += "?normalize=false"
    return raw.upload(path, file_path, client=client)


def add_preview(
    task,
    comment,
    preview_file_path=None,
    preview_file_url=None,
    normalize_movie=True,
    client=default,
):
    """
    Add a preview to given comment.

    Args:
        task (str / dict): The task dict or the task ID.
        comment (str / dict): The comment or the comment ID.
        preview_file_path (str): Path of the file to upload as preview.

    Returns:
        dict: Created preview file model.
    """
    if preview_file_url is not None:
        preview_file_path = download_file(
            preview_file_url,
        )

    preview_file = create_preview(task, comment, client=client)
    return upload_preview_file(
        preview_file,
        preview_file_path,
        normalize_movie=normalize_movie,
        client=client,
    )


def set_main_preview(preview_file, client=default):
    """
    Set given preview as thumbnail of given entity.

    Args:
        preview_file (str / dict): The preview file dict or ID.

    Returns:
        dict: Created preview file model.
    """
    preview_file = normalize_model_parameter(preview_file)
    path = "actions/preview-files/%s/set-main-preview" % preview_file["id"]
    return raw.put(path, {}, client=client)


@cache
def all_comments_for_task(task, client=default):
    """
    Args:
        task (str / dict): The task dict or the task ID.

    Returns:
        Comments linked to the given task.
    """
    task = normalize_model_parameter(task)
    return raw.fetch_all("tasks/%s/comments" % task["id"], client=client)


@cache
def get_last_comment_for_task(task, client=default):
    """
    Args:
        task (str / dict): The task dict or the task ID.

    Returns:
        Last comment posted for given task.
    """
    task = normalize_model_parameter(task)
    return raw.fetch_first("tasks/%s/comments" % task["id"], client=client)


@cache
def assign_task(task, person, client=default):
    """
    Assign one Person to a Task.
    Args:
        task (str / dict): The task dict or the task ID.
        person (str / dict): The person dict or the person ID.

    Returns:
        (dict) the affected Task
    """
    person = normalize_model_parameter(person)
    task = normalize_model_parameter(task)
    path = "/actions/persons/%s/assign" % person["id"]
    return raw.put(path, {"task_ids": task["id"]}, client=client)


def new_task_type(name, client=default):
    """
    Create a new task type with the given name.

    Args:
        name (str): The name of the task type

    Returns:
        dict: The created task type
    """
    data = {"name": name}
    return raw.post("data/task-types", data, client=client)


def new_task_status(name, short_name, color, client=default):
    """
    Create a new task status with the given name, short name and color.

    Args:
        name (str): The name of the task status
        short_name (str): The short name of the task status
        color (str): The color of the task status has an hexadecimal string
        with # as first character. ex : #00FF00

    Returns:
        dict: The created task status
    """
    assert color[0] == "#"
    assert all(c in string.hexdigits for c in color[1:])

    data = {"name": name, "short_name": short_name, "color": color}
    return raw.post("data/task-status", data, client=client)


def update_task(task, client=default):
    """
    Save given task data into the API. Metadata are fully replaced by the ones
    set on given task.

    Args:
        task (dict): The task dict to update.

    Returns:
        dict: Updated task.
    """
    if "assignees" in task:
        task["assignees"] = normalize_list_of_models_for_links(
            task["assignees"]
        )
    return raw.put("data/tasks/%s" % task["id"], task, client=client)


def update_task_data(task, data={}, client=default):
    """
    Update the metadata for the provided task. Keys that are not provided are
    not changed.

    Args:
        task (dict / ID): The task dict or ID to save in database.
        data (dict): Free field to set metadata of any kind.

    Returns:
        dict: Updated task.
    """
    task = normalize_model_parameter(task)
    current_task = get_task(task["id"], client=client)

    updated_task = {"id": current_task["id"], "data": current_task["data"]}
    if updated_task["data"] is None:
        updated_task["data"] = {}
    updated_task["data"].update(data)
    return update_task(updated_task, client=client)


@cache
def get_task_url(task, client=default):
    """
    Args:
        task (str / dict): The task dict or the task ID.

    Returns:
        url (str): Web url associated to the given task
    """
    task = normalize_model_parameter(task)
    path = "{host}/productions/{project_id}/shots/tasks/{task_id}/"
    return path.format(
        host=raw.get_api_url_from_host(client=client),
        project_id=task["project_id"],
        task_id=task["id"],
    )


def all_tasks_for_project(project, client=default):
    """
    Args:
        project (str / dict): The project

    Returns:
        dict: Tasks related to given project.
    """
    project = normalize_model_parameter(project)
    path = "/data/projects/%s/tasks" % project["id"]
    return raw.get(path, client=client)


def update_comment(comment, client=default):
    """
    Save given comment data into the API. Metadata are fully replaced by the ones
    set on given comment.

    Args:
        comment (dict): The comment dict to update.

    Returns:
        dict: Updated comment.
    """
    return raw.put("data/comments/%s" % comment["id"], comment, client=client)
