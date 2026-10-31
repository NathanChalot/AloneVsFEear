"""Dice codes and dice sources (E1).

A dice code is plain data, parsed from the code the book prints ("2d6+1", "d6 x d6", "d66");
a chance is "x in 6". Rolling takes a dice source: `RandomDice` for play and seeded tests,
`ScriptedDice` for rule tests that state the faces shown. Every roll keeps the faces shown as
well as the total, and is written to the log.
"""

from __future__ import annotations

import itertools
import logging
import random
import re
from collections.abc import Iterable
from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol

log = logging.getLogger(__name__)

FACES = range(1, 7)


class DiceError(ValueError):
    """A dice code that cannot be read, or scripted dice used wrongly."""


class Dice(Protocol):
    """Where the dice come from: every roll is made of six-sided dice."""

    def d6(self) -> int: ...


class RandomDice:
    """Real dice. The same seed gives the same rolls."""

    def __init__(self, seed: int | None = None) -> None:
        self._random = random.Random(seed)

    def d6(self) -> int:
        return self._random.randint(1, 6)


class ScriptedDice:
    """Dice that show the given faces, in order. For tests."""

    def __init__(self, faces: Iterable[int]) -> None:
        self._faces = list(faces)
        for face in self._faces:
            if face not in FACES:
                raise DiceError(f"a die has no face {face}")

    @property
    def remaining(self) -> int:
        return len(self._faces)

    def d6(self) -> int:
        if not self._faces:
            raise DiceError("the scripted dice have run out")
        return self._faces.pop(0)


class Combine(StrEnum):
    SUM = "sum"
    PRODUCT = "product"
    """d6 x d6: one die times the other."""
    DIGITS = "digits"
    """d66: the first die as tens, the second as units."""


@dataclass(frozen=True)
class DiceRoll:
    total: int
    faces: tuple[int, ...]
    """The six-sided dice shown, in order (for a d3, the d6 that was halved)."""

    @property
    def natural(self) -> int:
        """The first die as shown, without modifiers: what natural 1s and 6s read."""
        return self.faces[0]


_SUM = re.compile(r"(\d*)d([36])([+-]\d+)?")
_PLUS_FIRST = re.compile(r"(\d+)\+(\d*)d([36])")


@dataclass(frozen=True)
class DiceCode:
    count: int = 1
    sides: int = 6
    """6, or 3 for a d3 (a d6 halved, rounding up)."""
    plus: int = 0
    combine: Combine = Combine.SUM

    @classmethod
    def parse(cls, code: str) -> DiceCode:
        text = code.lower().replace(" ", "").replace("×", "x")
        if text == "d66":
            return cls(count=2, combine=Combine.DIGITS)
        if text == "d6xd6":
            return cls(count=2, combine=Combine.PRODUCT)
        if match := _SUM.fullmatch(text):
            count, sides, plus = match.groups()
        elif match := _PLUS_FIRST.fullmatch(text):
            plus, count, sides = match.groups()
        else:
            raise DiceError(f"unknown dice code {code!r}")
        dice = cls(count=int(count or 1), sides=int(sides), plus=int(plus or 0))
        if dice.count < 1:
            raise DiceError(f"unknown dice code {code!r}")
        return dice

    def roll(self, dice: Dice) -> DiceRoll:
        faces = tuple(dice.d6() for _ in range(self.count))
        result = DiceRoll(self._total(faces), faces)
        log.debug("rolled %s: %s -> %d", self, ", ".join(map(str, faces)), result.total)
        return result

    def results(self) -> tuple[int, ...]:
        """Every total the code can give, in order."""
        combos = itertools.product(FACES, repeat=self.count)
        return tuple(sorted({self._total(faces) for faces in combos}))

    def _total(self, faces: tuple[int, ...]) -> int:
        if self.combine is Combine.DIGITS:
            return 10 * faces[0] + faces[1]
        if self.combine is Combine.PRODUCT:
            return faces[0] * faces[1]
        values = faces if self.sides == 6 else tuple((face + 1) // 2 for face in faces)
        return sum(values) + self.plus

    def __str__(self) -> str:
        if self.combine is Combine.DIGITS:
            return "d66"
        if self.combine is Combine.PRODUCT:
            return "d6xd6"
        count = str(self.count) if self.count > 1 else ""
        plus = f"{self.plus:+d}" if self.plus else ""
        return f"{count}d{self.sides}{plus}"


@dataclass(frozen=True)
class ChanceRoll:
    success: bool
    face: int


_CHANCE = re.compile(r"(\d+)in6")


@dataclass(frozen=True)
class Chance:
    """An "x in 6" chance: succeeds on a die showing x or less."""

    in_6: int

    def __post_init__(self) -> None:
        if self.in_6 not in range(0, 7):
            raise DiceError(f"no chance of {self.in_6} in 6")

    @classmethod
    def parse(cls, code: str) -> Chance:
        match = _CHANCE.fullmatch(code.lower().replace(" ", ""))
        if not match:
            raise DiceError(f"unknown chance {code!r}")
        return cls(int(match.group(1)))

    def roll(self, dice: Dice) -> ChanceRoll:
        face = dice.d6()
        result = ChanceRoll(face <= self.in_6, face)
        log.debug("rolled %s: %d -> %s", self, face, "yes" if result.success else "no")
        return result

    def __str__(self) -> str:
        return f"{self.in_6} in 6"
