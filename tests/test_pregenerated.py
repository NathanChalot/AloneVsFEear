"""T1: the two sample pregenerated characters, copied into YAML from their filled-in sheets
(`gameRules/14_pregenerated_characters.md`), and a character made from one. The drills
start from them."""

import pytest

from alone_against_fear.content import Gear, load_content, reference_problems
from alone_against_fear.dice import ScriptedDice
from alone_against_fear.engine import creation
from alone_against_fear.engine.game import Game
from alone_against_fear.engine.state import Item, SkillLevel, Stat

CONTENT = load_content()
ANNA = "pregenerated.anna_miller"
DOUGLAS = "pregenerated.douglas_harrison"

# --- The content ---------------------------------------------------------------


def test_both_sheets_are_copied_in_the_book_order():
    assert list(CONTENT.pregenerated) == [ANNA, DOUGLAS]
    assert [c.name for c in CONTENT.pregenerated.values()] == ["Anna Miller", "Douglas Harrison"]
    assert {c.source for c in CONTENT.pregenerated.values()} == {
        "gameRules/14_pregenerated_characters.md"
    }


def test_anna_miller_as_printed():
    anna = CONTENT.pregenerated[ANNA]
    assert (anna.sanity, anna.life, anna.food) == (9, 10, 4)
    assert anna.skills == ("skill.will", "skill.occultist")
    # Pistol with 6 ammo, the hammer once (Weapons and Equipment), 3 stakes, a 3-point kit.
    assert anna.gear == (
        Gear("weapon.pistol", count=6),
        Gear("weapon.hammer"),
        Gear("item.wooden_stakes", count=3),
        Gear("item.first_aid_kit", uses=3),
    )


def test_douglas_harrison_as_printed():
    douglas = CONTENT.pregenerated[DOUGLAS]
    assert (douglas.sanity, douglas.life, douglas.food) == (8, 11, 4)
    # Strong at its Basic level: the rules win over the sheet's "+2" (the Markdown says so).
    assert douglas.skills == ("skill.slippery", "skill.strong")
    assert douglas.gear == (
        Gear("weapon.knife"),
        Gear("weapon.chainsaw"),
        Gear("item.salt", uses=6),
    )


def test_their_skills_and_gear_exist():
    assert reference_problems(CONTENT) == []
    for character in CONTENT.pregenerated.values():
        assert all(skill in CONTENT.skills for skill in character.skills)
        assert all(gear.id in CONTENT for gear in character.gear)


# --- A character made from one ---------------------------------------------------


def new_game():
    return Game(dice=ScriptedDice([]), content=CONTENT)


def test_a_pregenerated_character_is_made_as_printed():
    # Given a new campaign
    game = new_game()
    # When Anna Miller is taken
    anna = creation.pregenerated(game, ANNA)
    # Then she holds what her sheet says, at its values, and continues the campaign
    assert game.campaign.character is anna
    assert anna.name == "Anna Miller"
    assert (anna.life, anna.sanity, anna.food, anna.xp) == (10, 9, 4, 0)
    assert (game.max(Stat.LIFE), game.max(Stat.SANITY)) == (10, 9)
    assert anna.skills == {
        "skill.will": SkillLevel.BASIC,
        "skill.occultist": SkillLevel.BASIC,
    }
    assert anna.items == [
        Item("weapon.pistol", count=6),
        Item("weapon.hammer"),
        Item("item.wooden_stakes", count=3),
        Item("item.first_aid_kit", uses=3),
    ]


def test_an_unknown_pregenerated_character_is_refused():
    with pytest.raises(KeyError):
        creation.pregenerated(new_game(), "pregenerated.nobody")
