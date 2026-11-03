"""What an effect can change (E7): a roll, by its type and context tags, or a parameter.

The names the YAML and the engine share (design/rolls.md): the loader checks every effect of
the content against them, the engine rolls and calculates with them. Names only: a
parameter's value is calculated by the engine, its base plus the effects held. Tags are added
when the content first needs them.
"""

from __future__ import annotations

from enum import StrEnum


class RollType(StrEnum):
    """What a roll is for (design/rolls.md, Roll types)."""

    ATTACK = "attack"
    DEFENSE = "defense"
    SAVE = "save"
    ESCAPE = "escape"
    STEALTH = "stealth"
    CHARISMA = "charisma"
    STRENGTH = "strength"
    MAGIC = "magic"
    """Casting a spell or a ritual."""
    WILL = "will"
    SEARCH = "search"
    """The Search roll: not vs L, a natural 1 stays 1."""


class Tag(StrEnum):
    """What a roll is about: its weapon, its opponent, the danger it avoids."""

    HAND_TO_HAND = "hand_to_hand"
    """A hand-to-hand weapon; unarmed is not one."""
    RANGED = "ranged"
    BOW = "bow"
    UNARMED = "unarmed"
    VAMPIRE = "vampire"
    ZOMBIE = "zombie"
    POISON = "poison"
    INFECTION = "infection"
    DISEASE = "disease"
    FEAR = "fear"
    MAGIC = "magic"
    """Saves against magic; casting is a Magic roll."""
    HYPNOTISM = "hypnotism"
    PSIONICS = "psionics"
    CLIMB = "climb"
    JUMP = "jump"
    AVOID_DANGER = "avoid_danger"


IMPLIED: dict[Tag, frozenset[Tag]] = {Tag.BOW: frozenset({Tag.RANGED})}
"""A roll with the key tag carries these too: a bow is a ranged weapon (design/rolls.md)."""


def with_implied(tags: frozenset[Tag]) -> frozenset[Tag]:
    """The tags and every tag they imply."""
    return tags.union(*(IMPLIED.get(tag, ()) for tag in tags))


class Parameter(StrEnum):
    """A number the rules read that effects change: its base plus the effects held
    (design/rolls.md, Parameters)."""

    MAX_LIFE = "max_life"
    MAX_SANITY = "max_sanity"
    CARRY_LIMIT = "carry_limit"
    FOOD_INTERVAL = "food_interval"
    """How many boxes between two meals."""
    SURPRISE_CHANCE = "surprise_chance"
    """The x of a creature's x in 6 chance of surprising the character."""
    CLUE_COST = "clue_cost"
    """What a text charges in Clues."""
