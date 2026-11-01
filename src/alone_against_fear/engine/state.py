"""The game state (E2): plain data only, content referred to by ID, never code.

Three nested levels, each forgotten at its own time (design/encounters.md, What the game
remembers): the campaign is never forgotten, a character is forgotten at death or insanity,
a mission when a new one is rolled. Only the engine (`Game`) changes the state.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from enum import StrEnum
from typing import NamedTuple


class Level(StrEnum):
    CAMPAIGN = "campaign"
    CHARACTER = "character"
    MISSION = "mission"


class Happened(StrEnum):
    """What a history counts."""

    PLAYED = "played"
    FOUND = "found"
    KILLED = "killed"


class MoveKind(StrEnum):
    """Moves whose choice of box differs (design/town-map.md). Led astray, forced and jump
    come with the events that use them."""

    NORMAL = "normal"
    ESCAPE = "escape"


class Upkeep(StrEnum):
    """What the Food upkeep did on a box number."""

    ATE = "ate"
    STARVED = "starved"
    """No Food: 1 Life lost instead."""


class Stat(StrEnum):
    """The character's plain numbers. Max values, Skills and limits come later (E6, E9)."""

    LIFE = "life"
    SANITY = "sanity"
    FOOD = "food"
    XP = "xp"
    CLUES = "clues"


class Mark(StrEnum):
    """What a box can be marked as. Hell Gates, the stash and left-behind encounters come with
    their tasks; other marks a text gives are plain strings until then."""

    SAFE_HOUSE = "safe_house"


class End(StrEnum):
    """Why a game ended."""

    DEAD = "dead"
    """Life went to 0."""
    INSANE = "insane"
    """Sanity went to 0."""
    QUIT = "quit"
    """The player left; the campaign can go on later."""


@dataclass(frozen=True)
class Note:
    """A note the player keeps (E5b), with the box number it was written at: a lasting effect
    "for N boxes" ends N boxes later. The engine stores and shows it, never reads it."""

    text: str
    box: int


@dataclass
class History:
    """What happened at one level: how many times each ID was played, found or killed, and
    the keywords. The rules ask "has it happened?" and "how many times?", never "when"."""

    counts: dict[Happened, Counter[str]] = field(
        default_factory=lambda: {happened: Counter() for happened in Happened}
    )
    keywords: set[str] = field(default_factory=set)

    def count(self, happened: Happened, id_: str) -> int:
        return self.counts[happened][id_]

    def has(self, happened: Happened, id_: str) -> bool:
        return self.count(happened, id_) > 0


class Position(NamedTuple):
    """A box's (column, row) in the town grid, or a sheet's in the grid of sheets."""

    column: int
    row: int


@dataclass
class Box:
    position: Position
    numbers: list[int] = field(default_factory=list)
    """Every box number written in it, one per entry."""
    places: list[str] = field(default_factory=list)
    """IDs of every place table rolled in it (a haunted clinic holds both)."""
    searched: bool = False
    marks: set[str] = field(default_factory=set)
    """Safe House, Hell Gate, deconsecrated church... Left-behind encounters and the stash
    come with the tasks that model them."""


@dataclass
class TownMap:
    boxes: dict[Position, Box] = field(default_factory=dict)
    """The boxes entered so far."""
    sheets: set[Position] = field(default_factory=set)
    """The sheets attached so far, by position in the grid of sheets."""


@dataclass
class Mission:
    id: str
    history: History = field(default_factory=History)


@dataclass
class Character:
    life: int
    sanity: int
    food: int
    xp: int = 0
    clues: int = 0
    items: list[str] = field(default_factory=list)
    """Item names, until items get IDs (R3)."""
    notes: list[Note] = field(default_factory=list)
    """The player's notes (E5b): lasting effects and modifiers of texts the engine cannot
    read, kept as a reminder."""
    history: History = field(default_factory=History)
    mission: Mission | None = None


@dataclass
class Campaign:
    map: TownMap = field(default_factory=TownMap)
    box_counter: int = 0
    """The last box number written: the clock, never reset."""
    home: Position | None = None
    position: Position | None = None
    """The box the character stands in."""
    history: History = field(default_factory=History)
    character: Character | None = None
