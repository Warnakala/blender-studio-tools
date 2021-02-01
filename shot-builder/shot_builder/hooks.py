import typing
import types

import logging
logger = logging.getLogger(__name__)


class Wildcard:
    pass


class DoNotMatch:
    pass


MatchCriteriaType = typing.Union[str, typing.List[str],
                                 typing.Type[Wildcard], typing.Type[DoNotMatch]]
"""
The MatchCriteriaType is a type definition for the parameters of the `hook` decorator.

The matching parameters can use multiple types to detect how the matching criteria
would work.

* `str`: would perform an exact string match.
* `typing.List[str]`: would perform an exact string match with any of the given strings.
* `typing.Type[Wildcard]`: would match any type for this parameter. This would be used so a hook
  is called for any value.
* `typing.Type[DoNotMatch]`: would ignore this hook when matching the hook parameter. This is the default
  value for the matching criteria and would normally not be set directly in a
  production configuration.
"""

MatchingRulesType = typing.Dict[str, MatchCriteriaType]
"""
Hooks are stored as `_shot_builder_rules' attribute on the function.
The MatchingRulesType is the type definition of the `_shot_builder_rules` attribute.
"""

HookFunction = typing.Callable[[typing.Any], None]


def _match_hook_parameter(hook_criteria: MatchCriteriaType, match_query: typing.Optional[str]) -> bool:
    if hook_criteria == DoNotMatch:
        return match_query is None
    if hook_criteria == Wildcard:
        return True
    if isinstance(hook_criteria, str):
        return match_query == hook_criteria
    if isinstance(hook_criteria, list):
        return match_query in hook_criteria
    logger.error(f"Incorrect matching criteria {hook_criteria}, {match_query}")
    return False


class Hooks:
    def __init__(self):
        self._hooks: typing.List[HookFunction] = []

    def register(self, func: HookFunction) -> None:
        logger.info(f"registering hook '{func.__name__}'")
        self._hooks.append(func)

    def matches(self, hook: HookFunction, match_task_type: typing.Optional[str] = None, match_asset_type: typing.Optional[str] = None, **kwargs: typing.Optional[str]) -> bool:
        assert(not kwargs)
        rules = typing.cast(MatchingRulesType, getattr(
            hook, '_shot_builder_rules'))

        return all((
            _match_hook_parameter(rules['match_task_type'], match_task_type),
            _match_hook_parameter(rules['match_asset_type'], match_asset_type),
        ))

    def filter(self, **kwargs: typing.Optional[str]) -> typing.Iterator[HookFunction]:
        for hook in self._hooks:
            if self.matches(hook=hook, **kwargs):
                yield hook


def _register_hook(func: types.FunctionType) -> None:
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


def hook(match_task_type: MatchCriteriaType = DoNotMatch, match_asset_type: MatchCriteriaType = DoNotMatch) -> typing.Callable[[types.FunctionType], types.FunctionType]:
    """
    Decorator to add custom logic when building a shot.

    Hooks are used to extend the configuration that would be not part of the core logic of the shot builder tool.
    """
    rules = {
        'match_task_type': match_task_type,
        'match_asset_type': match_asset_type,
    }

    def wrapper(func: types.FunctionType) -> types.FunctionType:
        setattr(func, '_shot_builder_rules', rules)
        return func
    return wrapper
