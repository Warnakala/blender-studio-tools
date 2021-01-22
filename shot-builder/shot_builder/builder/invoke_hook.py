from shot_builder.builder.build_step import BuildStep, BuildContext
from shot_builder.hooks import HookFunction
import bpy

import typing
import types
import logging

logger = logging.getLogger(__name__)


class InvokeHookStep(BuildStep):
    def __init__(self, hook: HookFunction):
        self._hook = hook

    def __str__(self) -> str:
        return f"invoke hook [{self._hook.__name__}]"

    def execute(self, build_context: BuildContext) -> None:
        params = build_context.as_dict()
        self._hook(**params)  # type: ignore
