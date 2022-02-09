import importlib
from . import context

BUILD_CONTEXT = context.BuildContext()


def reload() -> None:
    global context
    global BUILD_CONTEXT

    context = importlib.reload(context)
    BUILD_CONTEXT = context.BuildContext()
