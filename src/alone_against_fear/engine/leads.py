"""How the entries of the arrival tables lead on (E5a): behaviour keyed by entry ID.

A copied entry names the tables it sends you to (`refs`), not how it uses them. Here is how, for
the two tables arriving rolls, as their text says: roll on the one table named, choose between
the tables named, or roll a die to pick one. A transitional step: the result scripts of E10
replace this with the whole Town Exploration and Random Encounter.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass


@dataclass(frozen=True)
class Auto:
    """ "Roll on the X table.": no choice."""

    ref: str

    @property
    def refs(self) -> tuple[str, ...]:
        return (self.ref,)


@dataclass(frozen=True)
class Choice:
    """ "The X table or the Y table, your choice.\""""

    refs: tuple[str, ...]


@dataclass(frozen=True)
class DieRoll:
    """ "Roll d6. On a 1-5, X. On a 6, Y.": the highest face of each range, then its table."""

    ranges: tuple[tuple[int, str], ...]

    def ref_for(self, face: int) -> str:
        return next(ref for high, ref in self.ranges if face <= high)

    @property
    def refs(self) -> tuple[str, ...]:
        return tuple(ref for _, ref in self.ranges)


type Lead = Auto | Choice | DieRoll

_TE = "table.town_exploration"
_RE = "table.random_encounter"

LEADS: Mapping[str, Lead] = {
    f"{_TE}.2": Auto(_RE),
    f"{_TE}.3": Choice(("table.military_installation_or_lab", "table.clinic")),
    f"{_TE}.4": Choice(("table.farm", "table.cemetery")),
    f"{_TE}.5": Auto("table.place_of_worship"),
    f"{_TE}.6": Auto("table.street"),
    f"{_TE}.7": DieRoll(((5, "table.house"), (6, "table.special_events"))),
    f"{_TE}.8": Choice(("table.store", "table.street")),
    f"{_TE}.9": Auto("table.sewers"),
    f"{_TE}.10": Choice(("table.railways", "table.woods_or_park")),
    f"{_TE}.11": Choice(("table.school", "table.woods_or_park")),
    f"{_TE}.12": Auto("table.woods_or_park"),
    f"{_RE}.1.1-2": Auto("table.slashers"),
    f"{_RE}.1.3-6": Auto("table.witch_children"),
    f"{_RE}.2.1-3": Auto("table.demonic_horrors"),
    f"{_RE}.2.4-6": Auto("table.beasts"),
    f"{_RE}.3.1-2": Auto("table.lab_horrors"),
    f"{_RE}.3.3-5": Auto("table.undead"),
    f"{_RE}.3.6": Auto("table.unique_vampires"),
    f"{_RE}.4.1-4": Auto("table.possessed"),
    f"{_RE}.4.5-6": Auto("table.living_dolls"),
    f"{_RE}.5.1-5": Auto("table.ghosts"),
    f"{_RE}.5.6": Auto("table.aliens"),
    f"{_RE}.6.1-3": Auto("table.unique_vampires"),
    f"{_RE}.6.4-6": Auto("table.unique_zombies"),
}
