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

from .game import Arrival, GameError, Purchase, Rolled, RolledVsL, Searched
from .state import End, Item, Lasting, Note, Position, Stat, Upkeep

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
    ROLL = "roll"
    """What a roll vs L made by hand is for: an `effect_targets.RollType`."""
    TAG = "tag"
    """Whether a roll made by hand is about the tags of an effect held, True or False;
    `Choose.about` is the effect (an `effects.Held`)."""
    LEVEL = "level"
    """The L of a roll, from the text (a `Number`)."""
    MODIFIER = "modifier"
    """The modifier the text gives a roll, a Search or a lasting effect, 0 if none (a
    `Number`)."""
    TARGET = "target"
    """What a lasting effect added by hand changes: every roll (`manual.ALL_ROLLS`) or one
    `effect_targets.RollType` (E8)."""
    BOXES = "boxes"
    """For how many boxes a lasting effect holds, 0 for until removed (a `Number`)."""
    LASTING = "lasting"
    """Which lasting effect to remove."""
    NOTE = "note"
    """The text of a note to write (a `Text`)."""
    NOTES = "notes"
    """Which note to remove."""
    APPLY = "apply"
    """Which effect to apply, as a free action (the manual actions about the character)."""
    NAME = "name"
    """The character's name, at creation (a `Text`)."""
    PREGENERATED = "pregenerated"
    """Which sample pregenerated character a drill starts with (T1)."""
    POINTS = "points"
    """What the 3 creation points buy (see `creation.Points`)."""
    LIFE_POINTS = "life_points"
    """How many of the 3 points go to Life, the rest to Sanity (a `Number`)."""
    SKILL = "skill"
    """Which Skill the character starts with, by ID."""
    WEAPON = "weapon"
    """Which weapon the character takes, when the text gives a choice."""
    PURCHASE = "purchase"
    """What to spend XP on (a `game.Purchase`), or back."""


class Action(StrEnum):
    """The free actions, once the box is resolved; moving or quitting ends the turn.
    Inventory and aborting a mission come with their tasks."""

    MOVE = "move"
    SEARCH = "search"
    """The Search roll; offered while the box may be Searched."""
    APPLY = "apply"
    """Apply an effect: opens the manual actions about the character."""
    SPEND_XP = "spend_xp"
    """Buy a Skill or raise one to Expert; offered while the XP can buy one (E6)."""
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
    """Pick one of the options. `about` is what the question is about, when the topic alone
    does not say (the effect a `TAG` question asks about)."""

    topic: Topic
    options: tuple
    about: object = None


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
class FoodUpkeep:
    """A box of time brought a meal (E8): eaten, or 1 Life lost without Food."""

    result: Upkeep


@dataclass(frozen=True)
class EffectEnded:
    """A lasting effect ran its course (E8)."""

    lasting: Lasting


@dataclass(frozen=True)
class LastingAdded:
    """The player added a lasting effect by hand (E8)."""

    lasting: Lasting


@dataclass(frozen=True)
class LastingRemoved:
    """The player removed a lasting effect by hand."""

    lasting: Lasting


@dataclass(frozen=True)
class Wandering:
    """The 1 in 6 chance of a Random Encounter in a visited box: the die, and whether it came."""

    face: int
    encounter: bool


@dataclass(frozen=True)
class LeadRolled:
    """An entry rolled a die to pick the table it leads to ("Roll d6. On a 1-5…"), or the
    thing it gives (a samurai sword, authentic or a replica)."""

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
class ItemTaken:
    """The character took an item or a weapon."""

    item: Item


@dataclass(frozen=True)
class Duplicate:
    """At creation, the entry rolled gives nothing new: the table is rolled again."""

    entry_id: str


class Step(StrEnum):
    """A step of character creation (T2), so an interface can say what is being asked."""

    NAME = "name"
    POINTS = "points"
    """The 3 points: on Life and Sanity, or traded."""
    SKILLS = "skills"
    """The Skills, and the gear a Skill gives at creation."""
    WEAPONS = "weapons"
    """The Random Weapon roll (or two), and the knife or stick."""
    GEAR = "gear"
    """The Random Objects and Useful Stuff rolls, then the Food."""


@dataclass(frozen=True)
class StepStarted:
    """A step of character creation starts: told before what it asks or rolls."""

    step: Step


@dataclass(frozen=True)
class Created:
    """Character creation is over: the character is made (T2)."""


@dataclass(frozen=True)
class Bought:
    """XP was spent on a Skill."""

    purchase: Purchase


@dataclass(frozen=True)
class Marked:
    """A box was marked (a Safe House)."""

    position: Position
    mark: str


type Request = Choose | Number | Text
type Event = (
    Arrival
    | FoodUpkeep
    | EffectEnded
    | LastingAdded
    | LastingRemoved
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
    | ItemTaken
    | Duplicate
    | StepStarted
    | Created
    | Bought
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
