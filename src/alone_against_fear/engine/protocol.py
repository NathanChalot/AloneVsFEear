"""The engine/interface protocol (E4): the engine asks, the interface answers.

The engine holds an `Interface` and calls it while the rules run: `ask` when the player has a
choice to make, `tell` when something happened. Requests, answers and events are plain data,
so an interface can show them any way it likes and a scripted one can play them in tests.
The answer must fit the request: one of the options of a `Choose`, a whole number within the
bounds of a `Number`, a text that is not empty for a `Text` (E5b). The engine refuses anything
else.

An interface raises `Quit` at any request when the player leaves the game.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol

from .game import Arrival, GameError, Rolled, RolledVsL, Searched
from .state import End, Note, Position, Stat

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
    STAT = "stat"
    """Which of the character's numbers a manual action changes."""
    AMOUNT = "amount"
    """How much is gained or lost (a `Number`)."""
    LEVEL = "level"
    """The L of a roll, from the text (a `Number`)."""
    MODIFIER = "modifier"
    """The modifier the text gives a roll or a Search, 0 if none (a `Number`)."""
    NOTE = "note"
    """The text of a note to write (a `Text`)."""
    NOTES = "notes"
    """Which note to remove."""
    APPLY = "apply"
    """Which effect to apply, as a free action (the manual actions about the character)."""


class Action(StrEnum):
    """The free actions, once the box is resolved; moving or quitting ends the turn.
    Inventory, spending XP and aborting a mission come with their tasks."""

    MOVE = "move"
    SEARCH = "search"
    """The Search roll; offered while the box may be Searched."""
    APPLY = "apply"
    """Apply an effect: opens the manual actions about the character."""
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


@dataclass(frozen=True)
class Number:
    """Type a whole number, within the bounds given (None: no bound)."""

    topic: Topic
    minimum: int | None = None
    maximum: int | None = None

    def fits(self, answer: object) -> bool:
        if not isinstance(answer, int) or isinstance(answer, bool):
            return False
        too_low = self.minimum is not None and answer < self.minimum
        too_high = self.maximum is not None and answer > self.maximum
        return not (too_low or too_high)


@dataclass(frozen=True)
class Text:
    """Type a text that is not empty; the spaces around it are dropped."""

    topic: Topic


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


@dataclass(frozen=True)
class Changed:
    """One of the character's numbers changed: by how much (negative for a loss) and its new
    value."""

    stat: Stat
    amount: int
    value: int


@dataclass(frozen=True)
class NoteWritten:
    note: Note


@dataclass(frozen=True)
class NoteRemoved:
    note: Note


@dataclass(frozen=True)
class Marked:
    """A box was marked (a Safe House)."""

    position: Position
    mark: str


type Request = Choose | Number | Text
type Event = (
    Arrival
    | Rolled
    | Wandering
    | LeadRolled
    | EventPlayed
    | SheetAttached
    | Changed
    | RolledVsL
    | Marked
    | NoteWritten
    | NoteRemoved
    | Searched
    | Ended
)


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
    """Ask the interface, refuse an answer that does not fit the request, and log it."""
    answer = interface.ask(request)
    match request:
        case Choose(options=options):
            if answer not in options:
                raise GameError(f"{answer!r} is not one of the options for {request.topic}")
            answer = options[options.index(answer)]  # the option itself, not a copy
        case Number():
            if not request.fits(answer):
                raise GameError(f"{answer!r} does not fit {request}")
        case Text():
            if not isinstance(answer, str) or not answer.strip():
                raise GameError(f"{answer!r} is not a text for {request.topic}")
            answer = answer.strip()
    log.info("answer %s: %s", request.topic, _shown(answer))
    return answer


def _shown(answer: object) -> str:
    if isinstance(answer, Position):
        return str(tuple(answer))
    return str(answer)
