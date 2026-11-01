"""The engine/interface protocol (E4): the engine asks, the interface answers.

The engine holds an `Interface` and calls it while the rules run: `ask` when the player has a
choice to make, `tell` when something happened. Requests, answers and events are plain data,
so an interface can show them any way it likes and a scripted one can play them in tests.
The answer to a `Choose` must be one of its options; the engine refuses anything else.

An interface raises `Quit` at any request when the player leaves the game.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol

from .game import Arrival


class Topic(StrEnum):
    """What a choice is about, so the interface knows how to show it."""

    HOME = "home"
    """Where Home is: a box of the first sheet."""
    ACTION = "action"
    """What the character does next this turn."""
    MOVE = "move"
    """Which box to move to."""


class Action(StrEnum):
    """What a turn can do. Search, inventory, spending XP and aborting a mission come with
    their tasks."""

    MOVE = "move"
    QUIT = "quit"


@dataclass(frozen=True)
class Choose:
    """Pick one of the options."""

    topic: Topic
    options: tuple


class End(StrEnum):
    """Why a game ended."""

    DEAD = "dead"
    """Life went to 0."""
    INSANE = "insane"
    """Sanity went to 0."""
    QUIT = "quit"
    """The player left; the campaign can go on later."""


@dataclass(frozen=True)
class Ended:
    end: End


type Request = Choose
type Event = Arrival | Ended


class Quit(Exception):
    """Raised by an interface when the player leaves the game, whatever was asked."""


class Interface(Protocol):
    def ask(self, request: Request) -> object:
        """The player's answer: one of the request's options."""
        ...

    def tell(self, event: Event) -> None:
        """Something happened."""
        ...
