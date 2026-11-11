"""E8: moments and reactions (design/effects.md, Moments; design/rulings.md, Map and Effects).

A moment is a point in play that the engine announces: its reactions run, then the lifetimes
that count it go down, and the effects that end are told. Moving to a box is a box of time.
The Food upkeep is a reaction to it: one meal once the Food interval has passed since the last
meal, the interval read when time passes (Resistant to Hunger, Eating Disorder). A lasting
effect "for the next N boxes" holds through the next N boxes and ends when the one after starts.
"""

import pytest

from alone_against_fear.content import Effect, load_content
from alone_against_fear.dice import ScriptedDice
from alone_against_fear.effect_targets import RollType, Tag
from alone_against_fear.engine import Game, GameError, Position, Stat, Upkeep
from alone_against_fear.engine.effects import PLAYER, Modifier
from alone_against_fear.engine.moments import announce
from alone_against_fear.engine.protocol import EffectEnded, FoodUpkeep
from alone_against_fear.engine.state import Moment, SkillLevel
from alone_against_fear.interface.scripted import ScriptedInterface

HOME, NEXT_DOOR = Position(2, 2), Position(3, 2)


@pytest.fixture(scope="module")
def content():
    return load_content()


def at_home(content, food=10, life=8, skills=(), faces=()):
    """A character at Home, box 1."""
    game = Game(dice=ScriptedDice(list(faces)), content=content)
    game.create_character(life=life, sanity=8, food=food, skills=skills)
    game.choose_home(HOME)
    return game


def walk_to(game, interface, box):
    """Move back and forth between Home and next door until `box` is entered; each move is a
    box of time."""
    while game.campaign.box_counter < box:
        here = game.campaign.position
        game.move(NEXT_DOOR if here == HOME else HOME)
        announce(game, interface, Moment.TIME_PASSES)


def meals(interface):
    return [event.result for event in interface.told if isinstance(event, FoodUpkeep)]


def eaten_at(content, box, setup=lambda game: None, food=10):
    """The box numbers where the character ate, walking from Home to `box`."""
    game = at_home(content, food=food)
    setup(game)
    eaten, interface = [], ScriptedInterface([])
    while game.campaign.box_counter < box:
        before = game.character.food
        walk_to(game, interface, game.campaign.box_counter + 1)
        if game.character.food < before:
            eaten.append(game.campaign.box_counter)
    return eaten


# --- The Food upkeep -----------------------------------------------------------------------


def test_the_character_eats_every_five_boxes(content):
    # given Home is box 1, with nothing eaten yet; when walking to box 15
    # then a meal comes on boxes 5, 10 and 15
    assert eaten_at(content, 15) == [5, 10, 15]


def test_a_meal_is_told_as_it_happens(content):
    game, interface = at_home(content, food=3), ScriptedInterface([])

    walk_to(game, interface, 5)

    assert meals(interface) == [Upkeep.ATE]
    assert game.character.food == 2


def test_without_food_the_character_loses_1_life_instead(content):
    # given a character with no Food
    game, interface = at_home(content, food=0, life=7), ScriptedInterface([])

    # when box 5 is entered
    walk_to(game, interface, 5)

    # then 1 Life is lost and Food stays at 0
    assert meals(interface) == [Upkeep.STARVED]
    assert (game.character.life, game.character.food) == (6, 0)


def test_starving_is_an_upkeep_too_the_next_one_comes_five_boxes_later(content):
    game, interface = at_home(content, food=0, life=7), ScriptedInterface([])

    walk_to(game, interface, 10)

    assert meals(interface) == [Upkeep.STARVED] * 2
    assert game.character.life == 5


def test_the_meal_follows_the_campaign_clock_not_the_character(content):
    # given a campaign at box 3 whose character dies; a new one continues it
    game, interface = at_home(content), ScriptedInterface([])
    walk_to(game, interface, 3)
    game.create_character(life=7, sanity=6, food=2)

    # when the new character walks to box 5
    walk_to(game, interface, 5)

    # then the boxes do not reset: box 5 is a meal for the newcomer too
    assert game.character.food == 1


def test_resistant_to_hunger_spaces_the_meals(content):
    def learn(game, expert=False):
        game.character.skills["skill.resistant_to_hunger"] = (
            SkillLevel.EXPERT if expert else SkillLevel.BASIC
        )

    assert eaten_at(content, 14, learn) == [6, 12]
    assert eaten_at(content, 14, lambda game: learn(game, expert=True)) == [7, 14]


def test_eating_disorder_brings_the_meals_closer(content):
    def scar(game):
        game.gain_mental_scar("mental_scar.eating_disorder")

    assert eaten_at(content, 9, scar) == [3, 6, 9]


def test_a_skill_learned_between_meals_changes_the_interval_already_running(content):
    # given the character ate at box 5 (design/rulings.md, Map)
    game, interface = at_home(content), ScriptedInterface([])
    walk_to(game, interface, 7)
    assert game.next_meal() == 10

    # when Resistant to Hunger is learned at box 7
    game.character.skills["skill.resistant_to_hunger"] = SkillLevel.BASIC

    # then the next meal moves from 10 to 11
    assert game.next_meal() == 11
    walk_to(game, interface, 10)
    assert game.character.food == 9
    walk_to(game, interface, 11)
    assert game.character.food == 8


def test_a_meal_overdue_after_the_interval_drops_comes_at_the_next_box(content):
    # given the character ate at box 5 and gains Eating Disorder in box 9: the meal was due at 8
    game, interface = at_home(content), ScriptedInterface([])
    walk_to(game, interface, 9)
    game.gain_mental_scar("mental_scar.eating_disorder")
    assert game.next_meal() == 8
    assert game.character.food == 9

    # when box 10 is entered: one meal, the only one owed
    walk_to(game, interface, 10)

    # then the next comes 3 boxes later
    assert game.character.food == 8
    assert game.next_meal() == 13


def test_home_is_box_1_and_no_meal_is_eaten_there(content):
    game = at_home(content, food=3)

    assert game.campaign.box_counter == 1
    assert game.character.food == 3
    assert game.next_meal() == 5


# --- Lasting effects -----------------------------------------------------------------------


MINUS_1_ON_ALL_ROLLS = Effect(basic=-1)
"""An effect with no roll type and no parameter: every roll (design/rulings.md, Effects)."""


def test_a_lasting_effect_holds_through_the_next_n_boxes(content):
    # given painkillers taken in box 10: -1 on all rolls for the next 3 boxes
    game, interface = at_home(content), ScriptedInterface([])
    walk_to(game, interface, 10)
    lasting = game.add_lasting(MINUS_1_ON_ALL_ROLLS, boxes=3)

    # then it holds for the rest of box 10 and through boxes 11, 12 and 13
    for box in (10, 11, 12, 13):
        walk_to(game, interface, box)
        assert lasting in game.character.lasting
        assert game.roll_modifiers(RollType.SAVE).applied == (Modifier(PLAYER, -1),)
    assert not any(isinstance(event, EffectEnded) for event in interface.told)

    # when box 14 starts, it ends, and the interface is told
    walk_to(game, interface, 14)
    assert game.character.lasting == []
    assert game.roll_modifiers(RollType.SAVE).applied == ()
    assert [e for e in interface.told if isinstance(e, EffectEnded)] == [EffectEnded(lasting)]


def test_a_lasting_effect_ends_after_its_box(content):
    game = at_home(content)
    lasting = game.add_lasting(MINUS_1_ON_ALL_ROLLS, boxes=3)

    assert game.ends_at(lasting) == 5


@pytest.mark.parametrize("roll", list(RollType))
def test_a_modifier_on_all_rolls_changes_every_roll_type(content, roll):
    # the Search too (design/rulings.md, Effects)
    game = at_home(content)
    game.add_lasting(MINUS_1_ON_ALL_ROLLS, boxes=3)

    assert game.roll_modifiers(roll).applied == (Modifier(PLAYER, -1),)


def test_a_modifier_on_all_rolls_changes_no_parameter(content):
    game = at_home(content)
    game.add_lasting(MINUS_1_ON_ALL_ROLLS, boxes=3)

    assert game.max(Stat.LIFE) == 8


def test_a_lasting_effect_on_one_roll_type_leaves_the_others_alone(content):
    game = at_home(content)
    game.add_lasting(Effect(basic=-1, roll=RollType.STEALTH), boxes=3)

    assert game.roll_modifiers(RollType.STEALTH).applied == (Modifier(PLAYER, -1),)
    assert game.roll_modifiers(RollType.ATTACK, frozenset({Tag.BOW})).applied == ()


def test_a_lasting_effect_stacks_with_the_skills(content):
    game = at_home(content, skills=("skill.investigator",))
    game.add_lasting(MINUS_1_ON_ALL_ROLLS, boxes=3)

    assert sum(m.amount for m in game.roll_modifiers(RollType.SEARCH).applied) == 0


def test_the_search_collects_a_lasting_modifier(content):
    # given -1 on all rolls; the die shows 4
    game = at_home(content, faces=[4])
    game.add_lasting(MINUS_1_ON_ALL_ROLLS, boxes=3)

    searched = game.search()

    assert searched.rolled.results == (3,)


def test_a_lasting_effect_until_removed_never_ends_on_its_own(content):
    game, interface = at_home(content), ScriptedInterface([])
    lasting = game.add_lasting(MINUS_1_ON_ALL_ROLLS)

    walk_to(game, interface, 30)

    assert game.character.lasting == [lasting]
    assert game.ends_at(lasting) is None
    game.remove_lasting(lasting)
    assert game.character.lasting == []


def test_a_lasting_effect_lasts_at_least_one_box(content):
    with pytest.raises(GameError):
        at_home(content).add_lasting(MINUS_1_ON_ALL_ROLLS, boxes=0)


def test_a_lasting_effect_belongs_to_the_character(content):
    game = at_home(content)
    game.add_lasting(MINUS_1_ON_ALL_ROLLS, boxes=3)

    game.create_character(life=8, sanity=8, food=3)

    assert game.character.lasting == []
