import importlib
from . import context

PROD_CONTEXT = context.ProductionContext()
ASSET_CONTEXT = context.AssetContext()
BUILD_CONTEXT = context.BuildContext()

_need_reload = "context" in locals()


def reload() -> None:
    global context
    global PROD_CONTEXT
    global ASSET_CONTEXT
    global BUILD_CONTEXT

    importlib.reload(context)
    PROD_CONTEXT = context.ProductionContext()
    ASSET_CONTEXT = context.AssetContext()
    BUILD_CONTEXT = context.BuildContext()


if _need_reload:
    reload()
