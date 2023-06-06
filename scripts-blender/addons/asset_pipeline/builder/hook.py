# ***** BEGIN GPL LICENSE BLOCK *****
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
# ***** END GPL LICENCE BLOCK *****
#
# (c) 2021, Blender Foundation - Paul Golter


# The Hook system for the Asset Builder is copied over from the shot-builder, developed by @Jeroen Bakker
# https://developer.blender.org/diffusion/BSTS/browse/master/shot-builder/

import logging
from typing import (
    Optional,
    Any,
    Set,
    Tuple,
    List,
    Type,
    Callable,
    Dict,
    cast,
    Union,
    Iterator,
)
from types import FunctionType, ModuleType
from pathlib import Path

from .. import constants

logger = logging.getLogger(name="BSP")


class Wildcard:
    pass


class DoNotMatch:
    pass


MatchCriteriaType = Union[str, List[str], Type[Wildcard], Type[DoNotMatch]]
"""
The MatchCriteriaType is a type definition for the parameters of the `hook` decorator.

The matching parameters can use multiple types to detect how the matching criteria
would work.

* `str`: would perform an exact string match.
* `Iterator[str]`: would perform an exact string match with any of the given strings.
* `Type[Wildcard]`: would match any type for this parameter. This would be used so a hook
  is called for any value.
* `Type[DoNotMatch]`: would ignore this hook when matching the hook parameter. This is the default
  value for the matching criteria and would normally not be set directly in a
  production configuration.
"""

MatchingRulesType = Dict[str, MatchCriteriaType]
"""
Hooks are stored as `constants.HOOK_ATTR_NAME' attribute on the function.
The MatchingRulesType is the type definition of the `constants.HOOK_ATTR_NAME` attribute.
"""

HookFunction = Callable[[Any], None]


def _match_hook_parameter(
    hook_criteria: MatchCriteriaType, match_query: Optional[str]
) -> bool:

    # print(f"hook_criteria: {hook_criteria} | match_query: {match_query}")

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
        self._hooks: List[HookFunction] = []

    def register(self, func: HookFunction) -> None:
        # logger.info(f"Registering hook '{func.__name__}'")
        self._hooks.append(func)

    @property
    def callables(self) -> List[HookFunction]:
        return self._hooks

    def matches(
        self,
        hook: HookFunction,
        match_asset_type: Optional[str] = None,
        match_asset: Optional[str] = None,
        match_task_layers: Optional[str] = None,  # Could be List[str]
        **kwargs: Optional[str],
    ) -> bool:
        assert not kwargs
        rules = cast(MatchingRulesType, getattr(hook, constants.HOOK_ATTR_NAME))
        return all(
            (
                _match_hook_parameter(rules["match_asset_type"], match_asset_type),
                _match_hook_parameter(rules["match_asset"], match_asset),
                _match_hook_parameter(rules["match_task_layers"], match_task_layers),
            )
        )

    def filter(self, **kwargs: Optional[str]) -> Iterator[HookFunction]:
        for hook in self._hooks:
            if self.matches(hook=hook, **kwargs):
                yield hook

    def __bool__(self) -> bool:
        return bool(self._hooks)


def hook(
    match_asset_type: MatchCriteriaType = DoNotMatch,
    match_asset: MatchCriteriaType = DoNotMatch,
    match_task_layers: MatchCriteriaType = DoNotMatch,
) -> Callable[[FunctionType], FunctionType]:
    """
    Decorator to add custom logic when building a shot.

    Hooks are used to extend the configuration that would be not part of the core logic of the shot builder tool.
    """
    rules = {
        "match_asset_type": match_asset_type,
        "match_asset": match_asset,
        "match_task_layers": match_task_layers,
    }

    def wrapper(func: FunctionType) -> FunctionType:
        setattr(func, constants.HOOK_ATTR_NAME, rules)
        return func

    return wrapper
