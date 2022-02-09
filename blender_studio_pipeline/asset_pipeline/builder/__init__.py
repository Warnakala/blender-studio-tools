import importlib
from . import context

BUILD_CONTEXT = context.BuildContext()
_need_reload = "context" in locals()


def reload() -> None:
    global context
    global BUILD_CONTEXT

    importlib.reload(context)
    BUILD_CONTEXT = context.BuildContext()


if _need_reload:
    reload()
