"""The engine/interface protocol (E4): the engine asks, the interface answers.

The engine holds an `Interface` and calls it while the rules run: `ask` when the player has a
choice to make, `tell` when something happened. Requests, answers and events are plain data,
so an interface can show them any way it likes and a scripted one can play them in tests.
The answer to a `Choose` must be one of its options; the engine refuses anything else.

An interface raises `Quit` at any request when the player leaves the game.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol

from .game import Arrival, GameError, Rolled
from .state import Position

log = logging.getLogger(__name__)


class Topic(StrEnum):
    """What a choice is about, so the interface knows how to show it."""

    HOME = "home"
    """Where Home is: a box of the first sheet."""
    ACTION = "action"
    """What the character does next this turn."""
    MOVE = "move"
    """Which box to move to."""
    SHEET = "sheet"
    """Where to attach a new sheet, in the grid of sheets."""
    CHOICE = "choice"
    """Which of the tables an entry names, when its text says "your choice"."""
    BOOK = "book"
    """Book mode: where the text of an entry the engine cannot read leads (see `Book`)."""
    TABLE = "table"
    """Which table the text leads to: any table, copied or not."""
    EVENT = "event"
    """Which numbered event the text leads to."""


class Action(StrEnum):
    """The free actions, once the box is resolved; moving or quitting ends the turn. Search,
    the manual actions, inventory, spending XP and aborting a mission come with their
    tasks."""

    MOVE = "move"
    SHEET = "sheet"
    """Attach a new sheet; offered once a sheet is full."""
    QUIT = "quit"


class Book(StrEnum):
    """Where the text of an entry not copied yet leads: only the player has read it."""

    TABLE = "table"
    """To another table: the player picks it next."""
    EVENT = "event"
    """To a numbered event: the player picks it next."""
    DONE = "done"
    """Nowhere else: the box is resolved."""


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


@dataclass(frozen=True)
class Wandering:
    """The 1 in 6 chance of a Random Encounter in a visited box: the die, and whether it came."""

    face: int
    encounter: bool


@dataclass(frozen=True)
class LeadRolled:
    """An entry rolled a die to pick the table it leads to ("Roll d6. On a 1-5…")."""

    entry_id: str
    face: int
    ref: str


@dataclass(frozen=True)
class EventPlayed:
    """A numbered event was reached; until it is copied (R6), its source holds the text."""

    event_id: str


@dataclass(frozen=True)
class SheetAttached:
    sheet: Position


type Request = Choose
type Event = Arrival | Rolled | Wandering | LeadRolled | EventPlayed | SheetAttached | Ended


class Quit(Exception):
    """Raised by an interface when the player leaves the game, whatever was asked."""


class Interface(Protocol):
    def ask(self, request: Request) -> object:
        """The player's answer: one of the request's options."""
        ...

    def tell(self, event: Event) -> None:
        """Something happened."""
        ...


def ask(interface: Interface, request: Request) -> object:
    """Ask the interface, refuse an answer that is not an option, and log it."""
    answer = interface.ask(request)
    if answer not in request.options:
        raise GameError(f"{answer!r} is not one of the options for {request.topic}")
    log.info("answer %s: %s", request.topic, _shown(answer))
    return request.options[request.options.index(answer)]  # the option itself, not a copy


def _shown(answer: object) -> str:
    if isinstance(answer, Position):
        return str(tuple(answer))
    return str(answer)
