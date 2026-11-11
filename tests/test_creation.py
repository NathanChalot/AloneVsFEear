"""E6: creating a character (`1_1_main_rules.md`, Your Character; design/character.md).

A name; 3 points on Life and Sanity (8 each), or traded for 1 extra Skill or 1 extra roll on
the Random Weapon, Random Objects or Useful Stuff table; 2 Skills (no Arcane, no Expert); a
random weapon and a knife or stick; 1 Random Object and 1 Useful Stuff, duplicates rerolled;
d6 Food. Rulings (design/rulings.md): the knife or stick and Random Weapon 1 are the player's
choice; a duplicate is anything already given at creation.

Scenarios are played by a scripted interface; the dice are scripted, in the order rolled:
Random Weapon (and its count), Random Objects, Useful Stuff (each d66 is two dice, then its
count), then the Food.
"""

import pytest

from alone_against_fear.content import load_content
from alone_against_fear.dice import ScriptedDice
from alone_against_fear.engine import Game, Stat
from alone_against_fear.engine.creation import Points, create
from alone_against_fear.engine.game import Rolled
from alone_against_fear.engine.manual import Manual
from alone_against_fear.engine.protocol import (
    Book,
    Changed,
    Choose,
    Duplicate,
    ItemTaken,
    LeadRolled,
    Number,
    Step,
    StepStarted,
    Text,
    Topic,
)
from alone_against_fear.engine.state import Item, SkillLevel
from alone_against_fear.interface.scripted import ScriptedInterface

PISTOL = (5, 3, 4)
"""Random Weapon 5: a pistol with 2d6 bullets (3 and 4: 7)."""
ROPE = (1, 1)
"""Random Objects 11: a rope."""
BELL = (1, 3)
"""Useful Stuff 13: a small bell."""
FOOD = 4


@pytest.fixture(scope="module")
def content():
    return load_content()


def created(content, dice, answers):
    """Create a character with these dice and answers; every die and answer must be used."""
    game = Game(dice=ScriptedDice(dice), content=content)
    interface = ScriptedInterface(answers)
    create(game, interface)
    assert interface.remaining == 0, "answers left over"
    assert game.dice.remaining == 0, "dice left over"
    return game, interface


def asked(interface, topic):
    return [request for request in interface.asked if request.topic is topic]


def told(interface, kind):
    return [event for event in interface.told if isinstance(event, kind)]


def basics(*skills, points=(Points.STATS, 2)):
    """The answers before the rolls: a name, the 3 points, the Skills."""
    return ["Ann", *points, *(skills or ("skill.agile", "skill.tough"))]


# --- Scenario: the whole creation --------------------------------------------------------------


def test_a_character_is_created_from_the_rules(content):
    # given the player names Ann, puts 2 points on Life and 1 on Sanity, picks Agile and
    # Tough, rolls a pistol, takes the knife, rolls a rope and a small bell, and 4 Food
    game, interface = created(
        content,
        [*PISTOL, *ROPE, *BELL, FOOD],
        [*basics(), "weapon.knife"],
    )

    # then the character has it all
    character = game.character
    assert character.name == "Ann"
    assert (character.base_life, character.base_sanity) == (10, 9)
    # Tough raises the max and the current Life by 2 (E7)
    assert (character.life, character.sanity) == (12, 9)
    assert (game.max(Stat.LIFE), game.max(Stat.SANITY)) == (12, 9)
    assert character.skills == {"skill.agile": SkillLevel.BASIC, "skill.tough": SkillLevel.BASIC}
    assert character.items == [
        Item("weapon.pistol", "table.random_weapon.5", count=7),
        Item("weapon.knife"),
        Item("item.rope", "table.random_objects.11"),
        Item("item.small_bell", "table.useful_stuff.13"),
    ]
    assert (character.food, character.xp, character.clues) == (FOOD, 0, 0)


def test_what_creation_asks(content):
    _, interface = created(content, [*PISTOL, *ROPE, *BELL, FOOD], [*basics(), "weapon.knife"])

    assert asked(interface, Topic.NAME) == [Text(Topic.NAME)]
    assert asked(interface, Topic.POINTS) == [Choose(Topic.POINTS, tuple(Points))]
    assert asked(interface, Topic.LIFE_POINTS) == [Number(Topic.LIFE_POINTS, 0, 3)]
    assert asked(interface, Topic.WEAPON) == [
        Choose(Topic.WEAPON, ("weapon.knife", "weapon.stick"))
    ]


def test_what_creation_tells(content):
    _, interface = created(content, [*PISTOL, *ROPE, *BELL, FOOD], [*basics(), "weapon.knife"])

    rolled = told(interface, Rolled)
    assert [r.table_id for r in rolled] == [
        "table.random_weapon",
        "table.random_objects",
        "table.useful_stuff",
    ]
    assert [event.item.id for event in told(interface, ItemTaken)] == [
        "weapon.pistol",
        "weapon.knife",
        "item.rope",
        "item.small_bell",
    ]
    assert told(interface, Changed) == [Changed(Stat.FOOD, FOOD, FOOD)]


class InOrder(ScriptedInterface):
    """A scripted interface that also keeps what was asked and told in one list, in order."""

    def __init__(self, answers):
        super().__init__(answers)
        self.both = []

    def ask(self, request):
        self.both.append(request)
        return super().ask(request)

    def tell(self, event):
        self.both.append(event)
        super().tell(event)


def test_creation_tells_each_step_as_it_starts(content):
    # given a player who takes Bow, so a bow and d6+3 arrows come before the Random Weapon roll
    game = Game(dice=ScriptedDice([2, *PISTOL, *ROPE, *BELL, FOOD]), content=content)
    interface = InOrder([*basics("skill.bow", "skill.agile"), "weapon.knife"])

    # when the character is created
    create(game, interface)

    # then each step is told before what it asks or rolls: the name, the 3 points, the
    # Skills (and the gear they give), the weapons, then the objects and the Food
    both = interface.both
    steps = [event.step for event in both if isinstance(event, StepStarted)]
    assert steps == [Step.NAME, Step.POINTS, Step.SKILLS, Step.WEAPONS, Step.GEAR]

    def at(step):
        return both.index(StepStarted(step))

    def first(match):
        return next(i for i, x in enumerate(both) if match(x))

    assert at(Step.NAME) < first(lambda x: getattr(x, "topic", None) is Topic.NAME)
    assert at(Step.POINTS) < first(lambda x: getattr(x, "topic", None) is Topic.POINTS)
    assert at(Step.SKILLS) < first(lambda x: getattr(x, "topic", None) is Topic.SKILL)
    bow = first(lambda x: isinstance(x, ItemTaken) and x.item.id == "weapon.bow")
    assert at(Step.SKILLS) < bow < at(Step.WEAPONS)
    assert at(Step.WEAPONS) < first(
        lambda x: isinstance(x, Rolled) and x.table_id == "table.random_weapon"
    )
    knife = first(lambda x: getattr(x, "topic", None) is Topic.WEAPON)
    assert (
        knife
        < at(Step.GEAR)
        < first(lambda x: isinstance(x, Rolled) and x.table_id == "table.random_objects")
    )


# --- The 3 points ---------------------------------------------------------------------------


@pytest.mark.parametrize(("on_life", "life", "sanity"), [(0, 8, 11), (3, 11, 8), (1, 9, 10)])
def test_the_3_points_go_to_life_and_sanity(content, on_life, life, sanity):
    game, _ = created(
        content,
        [*PISTOL, *ROPE, *BELL, FOOD],
        [*basics(points=(Points.STATS, on_life)), "weapon.knife"],
    )
    assert (game.character.base_life, game.character.base_sanity) == (life, sanity)


def test_the_3_points_traded_for_a_third_skill(content):
    game, interface = created(
        content,
        [*PISTOL, *ROPE, *BELL, FOOD],
        [
            *basics("skill.agile", "skill.tough", "skill.bow", points=(Points.SKILL,)),
            "weapon.knife",
        ],
    )
    assert (game.character.base_life, game.character.base_sanity) == (8, 8)
    assert list(game.character.skills) == ["skill.agile", "skill.tough", "skill.bow"]
    assert asked(interface, Topic.LIFE_POINTS) == []


@pytest.mark.parametrize(
    ("points", "dice", "extra"),
    [
        (Points.WEAPON, (6, 1, 1), Item("weapon.rifle", "table.random_weapon.6", count=2)),
        (Points.OBJECT, (2, 2), Item("item.lighter", "table.random_objects.22")),
        (Points.USEFUL, (1, 2), Item("item.flower_bunch_or_present", "table.useful_stuff.12")),
    ],
)
def test_the_3_points_traded_for_an_extra_roll(content, points, dice, extra):
    # the extra roll comes right after the table's first roll
    order = {
        Points.WEAPON: [*PISTOL, *dice, *ROPE, *BELL],
        Points.OBJECT: [*PISTOL, *ROPE, *dice, *BELL],
        Points.USEFUL: [*PISTOL, *ROPE, *BELL, *dice],
    }[points]
    game, _ = created(content, [*order, FOOD], [*basics(points=(points,)), "weapon.knife"])

    assert extra in game.character.items
    assert len(game.character.items) == 5
    assert (game.character.base_life, game.character.base_sanity) == (8, 8)


# --- Skills ---------------------------------------------------------------------------------


def test_the_skills_offered_are_not_arcane_and_not_twice(content):
    _, interface = created(content, [*PISTOL, *ROPE, *BELL, FOOD], [*basics(), "weapon.knife"])

    first, second = asked(interface, Topic.SKILL)
    assert first.options == tuple(content.skills)
    assert second.options == tuple(s for s in content.skills if s != "skill.agile")


# --- Weapons --------------------------------------------------------------------------------


def test_random_weapon_1_is_the_players_choice_of_bat_or_hammer(content):
    game, interface = created(
        content, [1, *ROPE, *BELL, FOOD], [*basics(), "weapon.hammer", "weapon.stick"]
    )

    assert asked(interface, Topic.WEAPON)[0] == Choose(
        Topic.WEAPON, ("weapon.baseball_bat", "weapon.hammer")
    )
    assert game.character.items[:2] == [
        Item("weapon.hammer", "table.random_weapon.1"),
        Item("weapon.stick"),
    ]


def test_the_bow_comes_with_its_arrows(content):
    # Random Weapon 3: 1 grenade or a bow with 2d6+3 arrows (2 and 2: 7)
    game, _ = created(
        content, [3, 2, 2, *ROPE, *BELL, FOOD], [*basics(), "weapon.bow", "weapon.knife"]
    )
    assert game.character.items[0] == Item("weapon.bow", "table.random_weapon.3", count=7)


def test_the_grenade_is_one(content):
    game, _ = created(
        content, [3, *ROPE, *BELL, FOOD], [*basics(), "weapon.grenade", "weapon.knife"]
    )
    assert game.character.items[0] == Item("weapon.grenade", "table.random_weapon.3", count=1)


def test_a_samurai_sword_is_rolled_authentic_or_replica(content):
    # Random Objects 54: roll d6, on a 1 or 2 authentic, on a 3-6 a cheap replica
    game, interface = created(content, [*PISTOL, 5, 4, 3, *BELL, FOOD], [*basics(), "weapon.knife"])
    sword = Item("weapon.samurai_sword_cheap_replica", "table.random_objects.54")
    assert sword in game.character.items
    assert told(interface, LeadRolled) == [
        LeadRolled("table.random_objects.54", 3, "weapon.samurai_sword_cheap_replica")
    ]


# --- Duplicates -----------------------------------------------------------------------------


def test_an_item_already_given_is_rerolled(content):
    # given a backpack from Random Objects (26), then one from Useful Stuff (14)
    game, interface = created(
        content, [*PISTOL, 2, 6, 1, 4, *BELL, FOOD], [*basics(), "weapon.knife"]
    )
    # then the second is rerolled: a small bell instead
    items = [item.id for item in game.character.items]
    assert items.count("item.backpack") == 1
    assert "item.small_bell" in items
    assert told(interface, Duplicate) == [Duplicate("table.useful_stuff.14")]


def test_a_weapon_already_given_is_rerolled(content):
    # given a baseball bat from Random Weapon 1, then one from Random Objects 21
    game, interface = created(
        content,
        [1, 2, 1, *ROPE, *BELL, FOOD],
        [*basics(), "weapon.baseball_bat", "weapon.knife"],
    )
    assert told(interface, Duplicate) == [Duplicate("table.random_objects.21")]
    assert [item.id for item in game.character.items].count("weapon.baseball_bat") == 1


def test_a_variant_is_not_a_duplicate_of_the_other(content):
    # a hammer from Random Weapon 1, then a baseball bat from Random Objects 21: both kept
    game, interface = created(
        content, [1, 2, 1, *BELL, FOOD], [*basics(), "weapon.hammer", "weapon.knife"]
    )
    assert told(interface, Duplicate) == []
    assert {"weapon.hammer", "weapon.baseball_bat"} <= {i.id for i in game.character.items}


def test_a_choice_offers_only_what_is_not_given_yet(content):
    # given a chainsaw from Random Weapon 2, then Random Weapon 2 again (the extra roll)
    game, interface = created(
        content,
        [2, 2, *ROPE, *BELL, FOOD],
        [*basics(points=(Points.WEAPON,)), "weapon.chainsaw", "weapon.knife"],
    )
    # then the second gives the authentic sword without asking
    assert len(asked(interface, Topic.WEAPON)) == 2  # chainsaw or sword, then knife or stick
    assert Item("weapon.samurai_sword_authentic", "table.random_weapon.2") in (game.character.items)


def test_the_same_entry_twice_is_a_duplicate(content):
    # given d6 Food points (Random Objects 33), then again on the extra roll
    game, interface = created(
        content,
        [*PISTOL, 3, 3, 2, 3, 3, *ROPE, *BELL, FOOD],
        [*basics(points=(Points.OBJECT,)), "weapon.knife"],
    )
    assert told(interface, Duplicate) == [Duplicate("table.random_objects.33")]


# --- Entries that are not items ---------------------------------------------------------------


def test_food_points_add_to_the_food(content):
    # Random Objects 33: d6 Food points (2), then the d6 starting Food (4)
    game, interface = created(content, [*PISTOL, 3, 3, 2, *BELL, FOOD], [*basics(), "weapon.knife"])
    assert game.character.food == 2 + FOOD
    assert told(interface, Changed) == [Changed(Stat.FOOD, 2, 2), Changed(Stat.FOOD, FOOD, 6)]


def test_a_random_book_goes_through_book_mode(content):
    # Random Objects 45: roll on the Random Book table, not copied yet (2d6: 3 and 4)
    game, interface = created(
        content,
        [*PISTOL, 4, 5, 3, 4, *BELL, FOOD],
        [*basics(), "weapon.knife", "table.random_book", Manual.WRITE_NOTE, "A book", Book.DONE],
    )
    rolled = [r for r in told(interface, Rolled) if r.table_id == "table.random_book"]
    assert rolled == [Rolled("table.random_book", (7,), None)]
    assert [note.text for note in game.character.notes] == ["A book"]
    assert all(i.source != "table.random_objects.45" for i in game.character.items)


# --- Counts and uses ------------------------------------------------------------------------


def test_counts_are_rolled(content):
    # d6 garlic heads (Random Objects 15: 5), then d3 bottles of liquor (Useful Stuff 35: a 6
    # halved, 3)
    game, _ = created(content, [*PISTOL, 1, 5, 5, 3, 5, 6, FOOD], [*basics(), "weapon.knife"])
    assert Item("item.garlic_heads", "table.random_objects.15", count=5) in game.character.items
    assert Item("item.liquor", "table.useful_stuff.35", count=3) in game.character.items


def test_uses_are_rolled(content):
    # a First Aid Kit (Random Objects 13) with d6+2 uses (4: 6)
    game, _ = created(content, [*PISTOL, 1, 3, 4, *BELL, FOOD], [*basics(), "weapon.knife"])
    assert Item("item.first_aid_kit", "table.random_objects.13", uses=6) in game.character.items


# --- Skills that give gear at creation ----------------------------------------------------------


def test_bow_gives_a_bow_and_arrows_at_creation(content):
    # given Bow taken at creation: a bow and d6+3 arrows (2: 5)
    game, interface = created(
        content,
        [2, *PISTOL, *ROPE, *BELL, FOOD],
        [*basics("skill.bow", "skill.agile"), "weapon.knife"],
    )
    bow = Item("weapon.bow", "skill.bow", count=5)
    assert game.character.items[0] == bow
    assert ItemTaken(bow) in interface.told


def test_faith_gives_the_religious_symbol_at_creation(content):
    # design/rulings.md: the Religious symbol, not the cheap one
    game, _ = created(
        content,
        [*PISTOL, *ROPE, *BELL, FOOD],
        [*basics("skill.faith", "skill.agile"), "weapon.knife"],
    )
    assert game.character.items[0] == Item("item.religious_symbol", "skill.faith")
    assert len(game.character.items) == 5  # and the usual four


def test_gear_from_a_skill_counts_for_duplicates(content):
    # given Bow at creation, then Random Weapon 3 (a grenade or a bow): only the grenade is left
    game, interface = created(
        content,
        [2, 3, *ROPE, *BELL, FOOD],
        [*basics("skill.bow", "skill.agile"), "weapon.knife"],
    )
    assert Item("weapon.grenade", "table.random_weapon.3", count=1) in game.character.items
    assert len(asked(interface, Topic.WEAPON)) == 1  # only the knife or stick


def test_the_religious_symbol_from_faith_counts_for_duplicates(content):
    # given Faith, then Random Objects 12 (a Religious symbol): rerolled, a rope instead
    game, interface = created(
        content,
        [*PISTOL, 1, 2, *ROPE, *BELL, FOOD],
        [*basics("skill.faith", "skill.agile"), "weapon.knife"],
    )
    assert told(interface, Duplicate) == [Duplicate("table.random_objects.12")]
