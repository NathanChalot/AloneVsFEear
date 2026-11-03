"""E7: rolls and effects (design/effects.md, design/rolls.md).

Max values and the other parameters are a base plus the effects held. Every Skill is written
as effects: each one is tested here, from the rules text (`gameRules/1_2_skills.md`) and the
rulings (design/rulings.md, Character).
"""

import pytest

from alone_against_fear.content import load_content
from alone_against_fear.dice import ScriptedDice
from alone_against_fear.effect_targets import Parameter
from alone_against_fear.engine import Game, GameError, Stat
from alone_against_fear.engine.game import Purchase
from alone_against_fear.engine.state import SkillLevel


@pytest.fixture(scope="module")
def content():
    return load_content()


def character(content, *skills, expert=(), life=10, sanity=9):
    """A character holding these Skills at Basic, the ones in `expert` at Expert."""
    game = Game(dice=ScriptedDice([]), content=content)
    game.create_character(life=life, sanity=sanity, food=3, skills=skills)
    for skill in expert:
        game.character.skills[skill] = SkillLevel.EXPERT
    return game


# --- Every Skill's parameters ------------------------------------------------------------


@pytest.mark.parametrize(
    ("skill", "parameter", "base", "basic", "expert"),
    [
        ("skill.danger_sense", Parameter.SURPRISE_CHANCE, 3, 2, 1),
        ("skill.danger_sense", Parameter.SURPRISE_CHANCE, 1, 0, 0),  # "no chance to surprise"
        ("skill.investigator", Parameter.CLUE_COST, 3, 2, 1),
        ("skill.investigator", Parameter.CLUE_COST, 2, 1, 1),  # "to a minimum of 1"
        ("skill.resistant_to_hunger", Parameter.FOOD_INTERVAL, None, 6, 7),
        ("skill.strong", Parameter.CARRY_LIMIT, None, 13, 15),
        ("skill.tough", Parameter.MAX_LIFE, None, 12, 13),
        ("skill.strong_grip_on_reality", Parameter.MAX_SANITY, None, 10, 11),
    ],
)
def test_a_skill_changes_its_parameter(content, skill, parameter, base, basic, expert):
    assert character(content, skill).parameter(parameter, base) == basic
    assert character(content, skill, expert=[skill]).parameter(parameter, base) == expert


@pytest.mark.parametrize(
    ("parameter", "value"),
    [
        (Parameter.MAX_LIFE, 10),
        (Parameter.MAX_SANITY, 9),
        (Parameter.CARRY_LIMIT, 10),
        (Parameter.FOOD_INTERVAL, 5),
    ],
)
def test_a_parameter_without_effects_is_its_base(content, parameter, value):
    assert character(content).parameter(parameter) == value


@pytest.mark.parametrize("parameter", [Parameter.SURPRISE_CHANCE, Parameter.CLUE_COST])
def test_a_parameter_whose_base_comes_from_the_text_needs_it(content, parameter):
    with pytest.raises(GameError, match="needs a base"):
        character(content).parameter(parameter)


# --- Max values ------------------------------------------------------------------------------


def test_the_max_is_calculated_from_the_effects(content):
    game = character(content, "skill.tough", "skill.strong_grip_on_reality")
    assert (game.max(Stat.LIFE), game.max(Stat.SANITY)) == (12, 10)


def test_a_character_created_with_tough_starts_at_the_raised_max(content):
    # the starting Life is the base; Tough raises the max and the current Life
    game = character(content, "skill.tough", "skill.strong_grip_on_reality", life=9, sanity=10)
    assert (game.character.life, game.character.sanity) == (11, 11)
    assert (game.character.base_life, game.character.base_sanity) == (9, 10)


def test_buying_tough_raises_max_and_current_life_without_healing(content):
    # design/character.md: 6/10 becomes 8/12
    game = character(content)
    game.lose(Stat.LIFE, 4)
    game.character.xp = 8
    game.buy(Purchase("skill.tough", SkillLevel.BASIC, 8))
    assert (game.character.life, game.max(Stat.LIFE)) == (8, 12)


def test_raising_tough_to_expert_adds_the_difference(content):
    # an Expert amount replaces the Basic one (ruling): +3 in all, so 1 more
    game = character(content, "skill.tough")
    game.character.xp = 8
    game.buy(Purchase("skill.tough", SkillLevel.EXPERT, 8))
    assert (game.character.life, game.max(Stat.LIFE)) == (13, 13)


def test_buying_strong_grip_on_reality_raises_max_and_current_sanity(content):
    game = character(content)
    game.character.xp = 6
    game.buy(Purchase("skill.strong_grip_on_reality", SkillLevel.BASIC, 6))
    assert (game.character.sanity, game.max(Stat.SANITY)) == (10, 10)


def test_healing_stops_at_the_raised_max(content):
    game = character(content, "skill.tough")
    game.lose(Stat.LIFE, 5)
    assert game.gain(Stat.LIFE, 9) == 12
