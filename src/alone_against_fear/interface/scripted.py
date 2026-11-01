"""A scripted interface (E4): it gives prepared answers in order, for tests."""

from __future__ import annotations

from collections.abc import Iterable

from ..engine.protocol import Event, Request


class ScriptError(Exception):
    """The script has no answer left for a request."""


class ScriptedInterface:
    """Answers each request with the next prepared answer, and remembers what the engine
    asked and told."""

    def __init__(self, answers: Iterable[object]) -> None:
        self._answers = list(answers)
        self.asked: list[Request] = []
        self.told: list[Event] = []

    @property
    def remaining(self) -> int:
        return len(self._answers)

    def ask(self, request: Request) -> object:
        self.asked.append(request)
        if not self._answers:
            raise ScriptError(f"no answer left for {request}")
        return self._answers.pop(0)

    def tell(self, event: Event) -> None:
        self.told.append(event)
