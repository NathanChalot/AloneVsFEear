"""Effects in play (E7, design/effects.md): collected from what the character holds.

Effects are not stored: they are read from their sources whenever a rule needs them, so
removing a source removes its effects and a max is never out of date. The sources are the
Skills and, since E8, the Injuries and Mental Scars (their table entries' effects); items
(E9) join them with their task.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import NamedTuple

from ..content import Content, Effect
from ..effect_targets import Parameter, RollType, Tag
from .state import Character, SkillLevel


@dataclass(frozen=True)
class Held:
    """An effect in play: its source (a Skill or an entry ID) and the amount at the level
    held."""

    source: str
    effect: Effect
    amount: int


@dataclass(frozen=True)
class Modifier:
    """A number added to a roll, and where it comes from: a Skill ID, or None for the
    modifier the player typed from a text (a weapon until E12, a note)."""

    source: str | None
    amount: int


class RollModifiers(NamedTuple):
    """What a roll collected: the modifiers applied, and the ones set aside because they do
    not stack with a higher one (Agile and Dodge), so the player sees why."""

    applied: tuple[Modifier, ...]
    set_aside: tuple[Modifier, ...]


def held(character: Character, content: Content) -> tuple[Held, ...]:
    """Every effect the character holds: their Skills', then their Injuries' and Mental
    Scars', each in the order gained."""
    skills = (
        Held(skill_id, effect, effect.amount(expert=level is SkillLevel.EXPERT))
        for skill_id, level in character.skills.items()
        for effect in content.skill(skill_id).effects
    )
    harm = (
        Held(entry_id, effect, effect.amount(expert=False))
        for entry_id in (*character.injuries, *character.mental_scars)
        for effect in content.entry(entry_id).effects
    )
    return (*skills, *harm)


def matches(effect: Effect, roll: RollType, tags: frozenset[Tag]) -> bool:
    """The effect changes this roll: same type, and one of its tags if it names any."""
    return effect.roll is roll and (not effect.tags or bool(effect.tags & tags))


def roll_modifiers(effects: Iterable[Held], roll: RollType, tags: frozenset[Tag]) -> RollModifiers:
    """The modifiers of the effects that match the roll. Modifiers stack (design/rulings.md,
    Effects), except within a group, where only the highest applies (the first on a tie)."""
    applied: list[Modifier] = []
    set_aside: list[Modifier] = []
    best: dict[str, int] = {}
    for held_effect in effects:
        if not matches(held_effect.effect, roll, tags):
            continue
        modifier = Modifier(held_effect.source, held_effect.amount)
        group = held_effect.effect.group
        if group is None:
            applied.append(modifier)
        elif group not in best:
            best[group] = len(applied)
            applied.append(modifier)
        elif modifier.amount > applied[best[group]].amount:
            set_aside.append(applied[best[group]])
            applied[best[group]] = modifier
        else:
            set_aside.append(modifier)
    return RollModifiers(tuple(applied), tuple(set_aside))


def depending_on_tags(effects: Iterable[Held], roll: RollType) -> tuple[Held, ...]:
    """The effects on this roll type that apply only to some tags: what the player is asked
    about when a roll is made by hand (book mode)."""
    return tuple(h for h in effects if h.effect.roll is roll and h.effect.tags)


def parameter_change(effects: Iterable[Held], parameter: Parameter) -> int:
    """How much the effects held change a parameter."""
    return sum(h.amount for h in effects if h.effect.parameter is parameter)
