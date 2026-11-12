"""E9: the inventory (design/inventory.md, rulings Inventory): two hands, a carry limit and a
Food limit, light items, worn items, ammo per type, items left in a box, losing the backpack.

The rules: `1_1_main_rules.md` (Food, Equipment), `11_encumbrance_summary.md`, `3_combat.md`
(Keep Track of Ammo). Every test goes through `Game`, the only writer.
"""

import pytest

from alone_against_fear.content import Effect, load_content
from alone_against_fear.dice import ScriptedDice
from alone_against_fear.effect_targets import Parameter
from alone_against_fear.engine import Game, GameError, Stat
from alone_against_fear.engine.state import Item, Mark, Place, Position, SkillLevel

HOME = Position(2, 2)
NEXT = Position(3, 2)

ROPE = Item("item.rope")
"""1 slot."""
RING = Item("item.silver_ring")
"""Negligible weight."""
BACKPACK = Item("item.backpack")
SMELTING = Item("item.smelting_equipment")
"""Counts as 2 carried items."""
JACKET = Item("item.leather_jacket")
"""Negligible weight if worn, 1 carried."""
ARMOR = Item("item.body_armor")
"""Wearing it counts as carrying 2 objects."""
DARK = Item("item.dark_clothes")
SPORT = Item("item.sport_clothes")
PISTOL = Item("weapon.pistol")
RIFLE = Item("weapon.rifle")
"""Two handed."""
AXE = Item("weapon.axe")
"""Two handed; one-handed with Strong (Expert)."""
KNIFE = Item("weapon.knife")


@pytest.fixture(scope="module")
def content():
    return load_content()


def new_game(content, faces=(), food=0, skills=()):
    game = Game(dice=ScriptedDice(list(faces)), content=content)
    game.create_character(life=10, sanity=9, food=food, skills=skills)
    game.choose_home(HOME)
    return game


@pytest.fixture
def game(content):
    return new_game(content)


def fill(game, slots):
    """Carry `slots` ropes."""
    for _ in range(slots):
        game.add_item(ROPE)


# --- The carry limit --------------------------------------------------------------------------


def test_a_character_carries_10_items(game):
    assert (game.carry_limit(), game.slots_used(), game.room()) == (10, 0, 10)
    fill(game, 10)
    assert game.room() == 0
    with pytest.raises(GameError, match="no room"):
        game.add_item(ROPE)


@pytest.mark.parametrize(("level", "limit"), [(SkillLevel.BASIC, 13), (SkillLevel.EXPERT, 15)])
def test_strong_carries_3_or_5_more(content, level, limit):
    game = new_game(content, skills=["skill.strong"])
    game.character.skills["skill.strong"] = level
    assert game.carry_limit() == limit


def test_a_backpack_carries_5_more_and_takes_no_slot(game):
    game.add_item(BACKPACK)
    assert (game.carry_limit(), game.slots_used()) == (15, 0)


def test_a_second_backpack_adds_nothing(game):
    # the backpack's effects are one group: the highest applies, they do not stack
    game.add_item(BACKPACK)
    game.add_item(BACKPACK)
    assert (game.carry_limit(), game.food_limit()) == (15, 15)


def test_20_items_is_the_absolute_maximum(content):
    # "A Strong (Expert) character with a backpack will be able to carry a maximum of
    # (10+5+5) = 20 items. This is the absolute maximum you can carry in the game."
    game = new_game(content, skills=["skill.strong"])
    game.character.skills["skill.strong"] = SkillLevel.EXPERT
    game.add_item(BACKPACK)
    assert game.carry_limit() == 20
    game.add_lasting(game.content.skill("skill.strong").effects[1])  # +3 more, from a text
    assert game.carry_limit() == 20


def test_light_items_never_count(game):
    fill(game, 10)
    for _ in range(5):
        game.add_item(RING)
    assert game.slots_used() == 10


def test_a_bundle_takes_its_slots_once(game):
    game.add_item(Item("item.cat_food", count=6))
    assert game.slots_used() == 1


def test_smelting_equipment_counts_as_2(game):
    game.add_item(SMELTING)
    assert game.slots_used() == 2


def test_ammo_is_not_an_item(game):
    fill(game, 10)
    game.gain_ammo("bullets", 12)
    assert game.character.ammo == {"bullets": 12}
    assert game.room() == 0


# --- Food ---------------------------------------------------------------------------------


def test_10_food_is_free_then_each_food_takes_a_slot(content):
    game = new_game(content, food=10)
    assert (game.food_limit(), game.slots_used()) == (10, 0)
    game.gain(Stat.FOOD, 3)
    assert game.slots_used() == 3


def test_a_backpack_carries_15_food(content):
    game = new_game(content, food=15)
    game.add_item(BACKPACK)
    assert game.slots_used() == 0


def test_strong_does_not_raise_the_food_limit(content):
    game = new_game(content, skills=["skill.strong"])
    assert game.food_limit() == 10


def test_food_stops_where_no_slot_is_left(content):
    # given 10 Food and 8 slots used: 2 Food more fit
    game = new_game(content, food=10)
    fill(game, 8)
    assert game.max(Stat.FOOD) == 12
    # when 5 Food are gained, then 2 are kept
    assert game.gain(Stat.FOOD, 5) == 12
    assert game.room() == 0


def test_food_over_the_limit_leaves_no_room_for_an_item(content):
    game = new_game(content, food=20)
    with pytest.raises(GameError, match="no room"):
        game.add_item(ROPE)


# --- Hands ------------------------------------------------------------------------------------


def test_hands_are_extra_slots(game):
    fill(game, 10)
    game.add_item(PISTOL, Place.HANDS)
    game.add_item(KNIFE, Place.HANDS)
    assert game.character.hands == [PISTOL, KNIFE]
    assert (game.free_hands(), game.room()) == (0, 0)


def test_a_third_object_does_not_fit_in_two_hands(game):
    game.add_item(PISTOL, Place.HANDS)
    game.add_item(KNIFE, Place.HANDS)
    with pytest.raises(GameError, match="hands"):
        game.add_item(ROPE, Place.HANDS)


def test_a_two_handed_weapon_needs_both_hands(game):
    game.add_item(KNIFE, Place.HANDS)
    with pytest.raises(GameError, match="hands"):
        game.add_item(RIFLE, Place.HANDS)
    game.move_item(KNIFE, Place.CARRIED)
    game.add_item(RIFLE, Place.HANDS)
    assert game.free_hands() == 0


def test_strong_expert_holds_the_axe_in_one_hand(content):
    # "If you are Strong (Expert), you may use it one-handed."
    game = new_game(content, skills=["skill.strong"])
    assert game.hands_needed(AXE) == 2
    game.character.skills["skill.strong"] = SkillLevel.EXPERT
    assert game.hands_needed(AXE) == 1


def test_holding_and_stowing(game):
    game.add_item(PISTOL)
    game.move_item(PISTOL, Place.HANDS)
    assert (game.character.hands, game.character.items) == ([PISTOL], [])
    game.move_item(PISTOL, Place.CARRIED)
    assert (game.character.hands, game.character.items) == ([], [PISTOL])


def test_stowing_needs_room(game):
    fill(game, 10)
    game.add_item(PISTOL, Place.HANDS)
    with pytest.raises(GameError, match="no room"):
        game.move_item(PISTOL, Place.CARRIED)


# --- Worn items ---------------------------------------------------------------------------


def test_a_worn_jacket_takes_no_slot(game):
    game.add_item(JACKET)
    assert game.slots_used() == 1
    game.move_item(JACKET, Place.WORN)
    assert (game.character.worn, game.slots_used()) == ([JACKET], 0)


def test_worn_body_armor_counts_as_2(game):
    game.add_item(ARMOR, Place.WORN)
    assert game.slots_used() == 2


def test_only_wearable_items_are_worn(game):
    game.add_item(ROPE)
    with pytest.raises(GameError, match="cannot be worn"):
        game.move_item(ROPE, Place.WORN)
    with pytest.raises(GameError, match="cannot be worn"):
        game.add_item(RING, Place.WORN)  # the ruling: jewellery is not worn


def test_one_set_of_clothes_at_a_time(game):
    game.add_item(DARK, Place.WORN)
    game.add_item(SPORT)
    with pytest.raises(GameError, match="one set of clothes"):
        game.move_item(SPORT, Place.WORN)


def test_taking_off_needs_room(game):
    game.add_item(JACKET, Place.WORN)
    fill(game, 10)
    with pytest.raises(GameError, match="no room"):
        game.move_item(JACKET, Place.CARRIED)


def test_where_an_item_may_go(game):
    game.add_item(JACKET)
    assert game.places_for(JACKET) == (Place.HANDS, Place.WORN, Place.BOX)


# --- Items left in a box ----------------------------------------------------------------------


def test_an_item_left_stays_in_the_box(game):
    game.add_item(ROPE)
    game.move_item(ROPE, Place.BOX)
    assert game.character.items == []
    assert game.box_items() == [ROPE]
    game.move_item(ROPE, Place.CARRIED)
    assert (game.character.items, game.box_items()) == ([ROPE], [])


def test_picking_up_needs_room(game):
    game.add_item(ROPE, Place.BOX)
    fill(game, 10)
    with pytest.raises(GameError, match="no room"):
        game.move_item(ROPE, Place.CARRIED, here=Place.BOX)


def leave_rope_next_door(content, faces):
    game = new_game(content, faces=faces)
    game.move(NEXT)
    game.add_item(ROPE, Place.BOX)
    game.move(HOME)
    game.move(NEXT)
    return game


@pytest.mark.parametrize(("face", "gone"), [(1, True), (3, True), (4, False), (6, False)])
def test_left_items_roll_on_return(content, face, gone):
    # rulings, Inventory: on 1-3 they are all gone
    game = leave_rope_next_door(content, [face])
    rolled = game.roll_left_items()
    assert (rolled.face, rolled.gone) == (face, gone)
    assert game.box_items() == ([] if gone else [ROPE])


def test_left_items_roll_again_on_every_return(content):
    game = leave_rope_next_door(content, [5, 2])
    assert not game.roll_left_items().gone
    game.move(HOME)
    game.move(NEXT)
    assert game.roll_left_items().gone


def test_a_box_with_nothing_left_rolls_nothing(game):
    game.move(NEXT)
    assert game.roll_left_items() is None


def test_a_safe_house_keeps_its_stash(content):
    game = new_game(content)
    game.move(NEXT)
    game.add_mark(NEXT, Mark.SAFE_HOUSE)
    game.add_item(ROPE, Place.BOX)
    game.move(HOME)
    game.move(NEXT)
    assert game.roll_left_items() is None
    assert game.box_items() == [ROPE]


def test_home_keeps_its_stash(game):
    # Home is a Safe House (rulings, Safe Houses); the rest of it comes with E15
    game.add_item(ROPE, Place.BOX)
    game.move(NEXT)
    game.move(HOME)
    assert game.roll_left_items() is None


def test_a_new_character_loses_every_item_left(game):
    game.add_item(ROPE, Place.BOX)
    game.create_character(life=8, sanity=8, food=2)
    assert game.box_items() == []


# --- Losing the backpack ----------------------------------------------------------------------


def test_losing_the_backpack_loses_every_carried_item(content):
    # given a character with a backpack, items carried (one light), held, worn, ammo, 14 Food
    game = new_game(content, food=14)
    game.add_item(BACKPACK)
    fill(game, 3)
    game.add_item(RING)
    game.add_item(PISTOL, Place.HANDS)
    game.add_item(JACKET, Place.WORN)
    game.gain_ammo("bullets", 6)
    # when the backpack is lost
    lost = game.lose_backpack()
    # then the carried items are gone, light ones too; hands, worn and ammo are kept
    assert lost == (BACKPACK, ROPE, ROPE, ROPE, RING)
    assert game.character.items == []
    assert (game.character.hands, game.character.worn) == ([PISTOL], [JACKET])
    assert game.character.ammo == {"bullets": 6}
    # and the 4 Food over the new limit take 4 slots
    assert (game.food_limit(), game.character.food, game.slots_used()) == (10, 14, 4)


def test_food_that_no_longer_fits_is_lost(content):
    # given 15 Food, a backpack, worn body armor (2 slots) and 8 slots fewer from a text
    game = new_game(content, food=15)
    game.add_item(BACKPACK)
    game.add_item(ARMOR, Place.WORN)
    game.add_lasting(Effect(basic=-8, parameter=Parameter.CARRY_LIMIT))
    # when the backpack is lost: 10 Food free, and no slot left after the armor
    game.lose_backpack()
    # then the 5 Food over are lost
    assert (game.carry_limit(), game.character.food) == (2, 10)


def test_no_backpack_no_loss(game):
    with pytest.raises(GameError, match="no backpack"):
        game.lose_backpack()


# --- Ammo ---------------------------------------------------------------------------------


def test_ammo_is_kept_per_type(game):
    game.gain_ammo("bullets", 6)
    game.gain_ammo("shells", 3)
    game.gain_ammo("bullets", 2)
    game.lose_ammo("bullets", 5)
    assert game.character.ammo == {"bullets": 3, "shells": 3}


def test_spent_ammo_leaves_no_count(game):
    game.gain_ammo("arrows", 2)
    game.lose_ammo("arrows", 2)
    assert game.character.ammo == {}


def test_ammo_cannot_go_below_zero(game):
    game.gain_ammo("bolts", 1)
    with pytest.raises(GameError, match="only 1 bolts"):
        game.lose_ammo("bolts", 2)


def test_an_unknown_ammo_type_is_refused(game):
    with pytest.raises(GameError, match="no such ammo"):
        game.gain_ammo("pebbles", 1)


def test_dropping_a_weapon_keeps_its_ammo(game):
    game.add_item(PISTOL)
    game.gain_ammo("bullets", 6)
    game.move_item(PISTOL, Place.BOX)
    assert game.character.ammo == {"bullets": 6}


# --- Items and their effects ------------------------------------------------------------------


@pytest.mark.parametrize("place", [Place.CARRIED, Place.HANDS])
def test_the_backpacks_effects_hold_while_the_character_has_it(game, place):
    game.add_item(BACKPACK, place)
    assert game.carry_limit() == 15
    game.remove_item(BACKPACK)
    assert game.carry_limit() == 10


def test_a_backpack_left_in_a_box_gives_nothing(game):
    game.add_item(BACKPACK, Place.BOX)
    assert game.carry_limit() == 10


def test_removing_an_item_it_does_not_have_is_refused(game):
    with pytest.raises(GameError, match="no "):
        game.remove_item(ROPE)
