import typing
import types

import logging
logger = logging.getLogger(__name__)


MatchingRulesType = typing.Dict[str, typing.Optional[str]]


class Hooks:
    def __init__(self):
        self._hooks = []

    def register(self, func: types.FunctionType) -> None:
        logger.info(f"registering hook '{func.__name__}'")
        self._hooks.append(func)

    def matches(self, hook: types.FunctionType, is_global=False, match_task_type=None) -> bool:
        rules = typing.cast(MatchingRulesType, hook._shot_builder_rules)
        if is_global:
            return rules['match_task_type'] is None

        if match_task_type is not None and rules['match_task_type'] != match_task_type:
            return False

        return True

    def filter(self, **kwargs) -> typing.Iterator[types.FunctionType]:
        for hook in self._hooks:
            if self.matches(hook=hook, **kwargs):
                yield hook


def _register_hook(func: types.FunctionType):
    from shot_builder.project import get_active_production
    production = get_active_production()
    production.hooks.register(func)


def register_hooks(module: types.ModuleType) -> None:
    """
    Register all hooks inside the given module.
    """
    for module_item_str in dir(module):
        module_item = getattr(module, module_item_str)
        if not isinstance(module_item, types.FunctionType):
            continue
        if module_item.__module__ != module.__name__:
            continue
        if not hasattr(module_item, "_shot_builder_rules"):
            continue
        _register_hook(module_item)


def hook(match_task_type: typing.Optional[str] = None) -> types.FunctionType:
    rules = {
        'match_task_type': match_task_type
    }

    def wrapper(func) -> types.FunctionType:
        func._shot_builder_rules = rules
        return func
    return wrapper
