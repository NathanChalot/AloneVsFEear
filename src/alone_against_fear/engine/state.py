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


class Stat(StrEnum):
    """The character's plain numbers. Max values, Skills and limits come later (E6, E9)."""

    LIFE = "life"
    SANITY = "sanity"
    FOOD = "food"
    XP = "xp"
    CLUES = "clues"


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
    """A box's place in the town grid. Sheets, neighbours and distance come in E3."""

    column: int
    row: int


@dataclass
class Box:
    position: Position
    numbers: list[int] = field(default_factory=list)
    """Every box number written in it, one per entry."""


@dataclass
class TownMap:
    boxes: dict[Position, Box] = field(default_factory=dict)
    """The boxes entered so far."""


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
    history: History = field(default_factory=History)
    mission: Mission | None = None


@dataclass
class Campaign:
    map: TownMap = field(default_factory=TownMap)
    box_counter: int = 0
    """The last box number written: the clock, never reset."""
    history: History = field(default_factory=History)
    character: Character | None = None
