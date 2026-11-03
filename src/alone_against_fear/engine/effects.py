"""Effects in play (E7, design/effects.md): collected from what the character holds.

Effects are not stored: they are read from their sources whenever a rule needs them, so
removing a source removes its effects and a max is never out of date. The sources are the
Skills for now; items (E9), Injuries and Mental Scars (E13) and effects with a lifetime of
their own (E8) join them with their tasks.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from ..content import Content, Effect
from ..effect_targets import Parameter
from .state import Character, SkillLevel


@dataclass(frozen=True)
class Held:
    """An effect in play: its source (a Skill ID) and the amount at the level held."""

    source: str
    effect: Effect
    amount: int


def held(character: Character, content: Content) -> tuple[Held, ...]:
    """Every effect the character holds, in the order of their Skills."""
    return tuple(
        Held(skill_id, effect, effect.amount(expert=level is SkillLevel.EXPERT))
        for skill_id, level in character.skills.items()
        for effect in content.skill(skill_id).effects
    )


def parameter_change(effects: Iterable[Held], parameter: Parameter) -> int:
    """How much the effects held change a parameter."""
    return sum(h.amount for h in effects if h.effect.parameter is parameter)
