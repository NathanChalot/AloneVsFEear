"""E6: the character (design/character.md): Life and Sanity with a max, Skills at Basic or
Expert, XP spent on Skills at any time, and the items held.

Max values are calculated: the sheet keeps the base values; the effects that raise them
(Tough, Strong Grip on Reality) are tested with the Skills' effects (test_effects.py, E7).
"""

import pytest

from alone_against_fear.content import load_content
from alone_against_fear.dice import ScriptedDice
from alone_against_fear.engine import Game, GameError, Stat
from alone_against_fear.engine.game import Purchase
from alone_against_fear.engine.state import Item, SkillLevel


@pytest.fixture(scope="module")
def content():
    return load_content()


@pytest.fixture
def game(content):
    game = Game(dice=ScriptedDice([]), content=content)
    game.create_character(life=10, sanity=9, food=3, name="Ann")
    return game


# --- Life and Sanity have a max -------------------------------------------------------------


def test_the_starting_life_and_sanity_are_the_max(game):
    assert (game.character.life, game.character.sanity) == (10, 9)
    assert (game.max(Stat.LIFE), game.max(Stat.SANITY)) == (10, 9)
    assert game.character.name == "Ann"


def test_food_xp_and_clues_have_no_max_here(game):
    # the Food limit comes with the inventory (E9)
    assert [game.max(stat) for stat in (Stat.FOOD, Stat.XP, Stat.CLUES)] == [None] * 3


@pytest.mark.parametrize("stat", [Stat.LIFE, Stat.SANITY])
def test_healing_stops_at_max(game, stat):
    # given a character who lost 2 points
    game.lose(stat, 2)
    # when they gain 5
    value = game.gain(stat, 5)
    # then they are back at max, no higher
    assert value == getattr(game.character, stat) == game.max(stat)


def test_a_gain_at_max_changes_nothing(game):
    assert game.gain(Stat.LIFE, 3) == 10


# --- Skills -----------------------------------------------------------------------------------


def test_a_new_character_may_start_with_basic_skills(content):
    game = Game(dice=ScriptedDice([]), content=content)
    character = game.create_character(
        life=8, sanity=11, food=2, skills=["skill.agile", "skill.tough"]
    )
    assert character.skills == {"skill.agile": SkillLevel.BASIC, "skill.tough": SkillLevel.BASIC}


def test_a_new_character_cannot_start_with_an_arcane_skill(content):
    game = Game(dice=ScriptedDice([]), content=content)
    with pytest.raises(GameError):
        game.create_character(life=8, sanity=11, food=2, skills=["arcane_skill.curse"])


def test_nothing_can_be_bought_without_xp(game):
    assert game.purchases() == ()


def test_a_skill_is_bought_at_basic_for_its_xp_cost(game):
    # given a character with 8 XP (Agile costs 8)
    game.gain(Stat.XP, 8)
    agile = Purchase("skill.agile", SkillLevel.BASIC, 8)
    assert agile in game.purchases()
    # when they buy Agile
    game.buy(agile)
    # then they have it at Basic and no XP left
    assert game.character.skills["skill.agile"] is SkillLevel.BASIC
    assert game.character.xp == 0


def test_only_affordable_skills_are_offered(game):
    game.gain(Stat.XP, 3)
    offered = game.purchases()
    assert offered  # Bow costs 3
    assert all(p.cost <= 3 for p in offered)
    assert all(p.level is SkillLevel.BASIC for p in offered)


def test_expert_costs_the_skill_cost_again(game):
    # given a character with Agile at Basic and 8 XP (design/rulings.md)
    game.gain(Stat.XP, 16)
    game.buy(Purchase("skill.agile", SkillLevel.BASIC, 8))
    # when they buy Agile at Expert
    expert = Purchase("skill.agile", SkillLevel.EXPERT, 8)
    assert expert in game.purchases()
    game.buy(expert)
    # then Agile is Expert and the XP spent
    assert game.character.skills["skill.agile"] is SkillLevel.EXPERT
    assert game.character.xp == 0
    assert all(p.skill_id != "skill.agile" for p in game.purchases())


def test_arcane_skills_are_not_offered(game):
    # they need their prerequisite: a book or a ritual (E18)
    game.gain(Stat.XP, 99)
    assert all(p.skill_id.startswith("skill.") for p in game.purchases())


def test_a_purchase_not_offered_is_refused(game):
    game.gain(Stat.XP, 2)
    with pytest.raises(GameError):
        game.buy(Purchase("skill.agile", SkillLevel.BASIC, 8))
    with pytest.raises(GameError):
        game.buy(Purchase("skill.agile", SkillLevel.BASIC, 1))  # the wrong cost


# --- Items ----------------------------------------------------------------------------------


def test_an_item_held_keeps_where_it_came_from_and_how_many(game):
    garlic = Item("item.garlic_heads", "table.random_objects.15", count=4)
    kit = Item("item.first_aid_kit", "table.random_objects.13", uses=5)
    game.add_item(garlic)
    game.add_item(kit)
    assert game.character.items == [garlic, kit]
    game.remove_item(garlic)
    assert game.character.items == [kit]


def test_an_item_that_is_not_held_cannot_be_removed(game):
    with pytest.raises(GameError):
        game.remove_item(Item("weapon.axe", "table.random_objects.14"))
