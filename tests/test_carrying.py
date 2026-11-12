"""E9: carrying, played (design/inventory.md, Picking something up): the player takes what
a text gives, chooses what to drop when there is no room, holds, stows, wears and leaves
items as a free action, and loses items, ammo or the backpack by hand from a text.

Scenarios played by a scripted interface; the dice show the faces given.
"""

import pytest

from alone_against_fear.content import load_content
from alone_against_fear.dice import ScriptedDice
from alone_against_fear.engine import Game, Position, Stat, carrying
from alone_against_fear.engine.game import LeftItems
from alone_against_fear.engine.loop import play
from alone_against_fear.engine.manual import Manual
from alone_against_fear.engine.protocol import (
    Action,
    AmmoChanged,
    BackpackLost,
    Book,
    Changed,
    Choose,
    ItemAt,
    ItemLost,
    ItemMoved,
    ItemTaken,
    Number,
    Topic,
)
from alone_against_fear.engine.state import Item, Place
from alone_against_fear.interface.scripted import ScriptedInterface

HOME = Position(2, 2)
EAST = Position(3, 2)
STREET = (3, 3, 4)
"""A new box: Town Exploration 6 rolls the Street (not copied yet): book mode."""
ROPE = Item("item.rope")
RING = Item("item.silver_ring")
BACKPACK = Item("item.backpack")
PISTOL = Item("weapon.pistol")
RIFLE = Item("weapon.rifle")
JACKET = Item("item.leather_jacket")


@pytest.fixture(scope="module")
def content():
    return load_content()


def new_game(content, *faces, food=3, at_home=True):
    game = Game(dice=ScriptedDice(faces), content=content)
    game.create_character(life=8, sanity=8, food=food)
    if at_home:
        game.choose_home(HOME)
    return game


def fill(game, slots):
    for _ in range(slots):
        game.add_item(ROPE)


def asked(interface, topic):
    return [request for request in interface.asked if request.topic is topic]


def told(interface, kind):
    return [event for event in interface.told if isinstance(event, kind)]


# --- Taking an item -----------------------------------------------------------------------------


def test_an_item_that_fits_is_taken(content):
    game = new_game(content)
    interface = ScriptedInterface([])

    carrying.take(game, interface, ROPE)

    assert game.character.items == [ROPE]
    assert interface.told == [ItemTaken(ROPE, Place.CARRIED)]


def test_with_no_room_the_player_drops_an_item_to_take_the_new_one(content):
    # given 10 ropes carried, and a free hand
    game = new_game(content)
    fill(game, 10)
    interface = ScriptedInterface([ItemAt(ROPE, Place.CARRIED)])

    # when a pistol is found and the player drops a rope for it
    carrying.take(game, interface, PISTOL)

    # then the player was asked what to do: drop one, hold it, or leave it
    (room,) = asked(interface, Topic.ROOM)
    assert room == Choose(
        Topic.ROOM, (ItemAt(ROPE, Place.CARRIED), Place.HANDS, Place.BOX), about=PISTOL
    )
    # and the rope stays in the box, the pistol is carried
    assert game.box_items() == [ROPE]
    assert game.character.items == [*[ROPE] * 9, PISTOL]
    assert told(interface, ItemMoved) == [ItemMoved(ROPE, Place.CARRIED, Place.BOX)]


def test_with_no_room_the_player_holds_the_new_item(content):
    game = new_game(content)
    fill(game, 10)
    interface = ScriptedInterface([Place.HANDS])

    carrying.take(game, interface, PISTOL)

    assert game.character.hands == [PISTOL]
    assert told(interface, ItemTaken) == [ItemTaken(PISTOL, Place.HANDS)]


def test_with_no_room_the_player_leaves_the_new_item_in_the_box(content):
    game = new_game(content)
    fill(game, 10)
    interface = ScriptedInterface([Place.BOX])

    carrying.take(game, interface, PISTOL)

    assert game.box_items() == [PISTOL]
    assert told(interface, ItemTaken) == [ItemTaken(PISTOL, Place.BOX)]


def test_holding_is_not_offered_without_the_hands_for_it(content):
    game = new_game(content)
    fill(game, 10)
    game.add_item(PISTOL, Place.HANDS)
    interface = ScriptedInterface([Place.BOX])

    carrying.take(game, interface, RIFLE)

    assert Place.HANDS not in asked(interface, Topic.ROOM)[0].options


def test_dropping_a_light_item_makes_no_room_so_it_is_not_offered(content):
    game = new_game(content)
    fill(game, 10)
    game.add_item(RING)
    interface = ScriptedInterface([Place.BOX])

    carrying.take(game, interface, ROPE)

    assert ItemAt(RING, Place.CARRIED) not in asked(interface, Topic.ROOM)[0].options


# --- Food ----------------------------------------------------------------------------------


def test_food_that_fits_is_gained(content):
    game = new_game(content, food=3)
    interface = ScriptedInterface([])

    assert carrying.gain_food(game, interface, 4) == 4
    assert interface.told == [Changed(Stat.FOOD, 4, 7)]


def test_food_over_the_room_asks_what_to_drop_or_leaves_the_rest(content):
    # given 10 Food and 10 ropes: no room
    game = new_game(content, food=10)
    fill(game, 10)
    interface = ScriptedInterface([ItemAt(ROPE, Place.CARRIED), Place.BOX])

    # when 3 Food are found: the player drops a rope, then leaves the rest
    gained = carrying.gain_food(game, interface, 3)

    # then 1 Food is gained, in the slot of the rope
    assert (gained, game.character.food, game.room()) == (1, 11, 0)
    first, second = asked(interface, Topic.ROOM)
    assert first.about == Stat.FOOD and first.options[-1] is Place.BOX
    assert Place.HANDS not in first.options
    assert told(interface, Changed) == [Changed(Stat.FOOD, 1, 11)]


# --- The inventory, a free action -----------------------------------------------------------------


def test_the_inventory_is_a_free_action_once_there_is_something(content):
    game = new_game(content)
    interface = ScriptedInterface([Action.QUIT])
    play(game, interface)
    assert Action.INVENTORY not in asked(interface, Topic.ACTION)[0].options

    game.add_item(ROPE)
    interface = ScriptedInterface([Action.QUIT])
    play(game, interface)
    assert Action.INVENTORY in asked(interface, Topic.ACTION)[0].options


def test_the_player_holds_wears_and_leaves_items(content):
    # given a pistol and a jacket carried
    game = new_game(content)
    game.add_item(PISTOL)
    game.add_item(JACKET)
    interface = ScriptedInterface(
        [
            Action.INVENTORY,
            ItemAt(PISTOL, Place.CARRIED),
            Place.HANDS,
            ItemAt(JACKET, Place.CARRIED),
            Place.WORN,
            ItemAt(PISTOL, Place.HANDS),
            Place.BOX,
            Manual.BACK,
            Action.QUIT,
        ]
    )

    play(game, interface)

    assert (game.character.hands, game.character.worn, game.box_items()) == ([], [JACKET], [PISTOL])
    assert told(interface, ItemMoved) == [
        ItemMoved(PISTOL, Place.CARRIED, Place.HANDS),
        ItemMoved(JACKET, Place.CARRIED, Place.WORN),
        ItemMoved(PISTOL, Place.HANDS, Place.BOX),
    ]
    first = asked(interface, Topic.INVENTORY)[0]
    assert first.options == (
        ItemAt(PISTOL, Place.CARRIED),
        ItemAt(JACKET, Place.CARRIED),
        Manual.BACK,
    )
    assert asked(interface, Topic.PLACE)[1] == Choose(
        Topic.PLACE,
        (Place.HANDS, Place.WORN, Place.BOX, Manual.BACK),
        about=ItemAt(JACKET, Place.CARRIED),
    )


def test_the_player_picks_up_what_was_left_here(content):
    game = new_game(content)
    game.add_item(ROPE, Place.BOX)
    interface = ScriptedInterface(
        [Action.INVENTORY, ItemAt(ROPE, Place.BOX), Place.CARRIED, Manual.BACK, Action.QUIT]
    )

    play(game, interface)

    assert (game.character.items, game.box_items()) == ([ROPE], [])


# --- Left items, on coming back ------------------------------------------------------------


def test_items_left_in_a_box_may_be_gone_on_return(content):
    # given a rope left in the Street box (book mode), then back Home and to the Street again
    # the dice: the Street, Home's 1 in 6 (2: no encounter), the rope (1), the Street's 1 in 6
    game = new_game(content, *STREET, 2, 1, 2)
    interface = ScriptedInterface(
        [
            Action.MOVE,
            EAST,
            Book.DONE,
            Action.INVENTORY,
            ItemAt(ROPE, Place.CARRIED),
            Place.BOX,
            Manual.BACK,
            Action.MOVE,
            HOME,
            Action.MOVE,
            EAST,
            Action.QUIT,
        ]
    )
    game.add_item(ROPE)

    play(game, interface)

    # then on return the d6 shows 1: the rope is gone
    assert told(interface, LeftItems) == [LeftItems(1, gone=True)]
    assert game.box_items() == []


# --- Manual actions: take, lose, the backpack ---------------------------------------------------


def on_the_street(*answers):
    return [Action.MOVE, EAST, *answers, Book.DONE, Action.QUIT]


def test_the_player_takes_an_item_a_text_gives_with_its_count(content):
    game = new_game(content, *STREET)
    interface = ScriptedInterface(on_the_street(Manual.TAKE_ITEM, "item.garlic_heads", 4))

    play(game, interface)

    garlic = Item("item.garlic_heads", count=4)
    assert game.character.items == [garlic]
    assert asked(interface, Topic.COUNT) == [Number(Topic.COUNT, minimum=1)]
    item_question = asked(interface, Topic.ITEM)[0]
    assert {"item.rope", "weapon.pistol", "bullets", Manual.BACK} <= set(item_question.options)
    assert "weapon.baseball_bat_or_hammer" not in item_question.options
    assert "weapon.unarmed_attack" not in item_question.options


def test_an_item_with_uses_asks_them(content):
    game = new_game(content, *STREET)
    interface = ScriptedInterface(on_the_street(Manual.TAKE_ITEM, "item.first_aid_kit", 5))

    play(game, interface)

    assert game.character.items == [Item("item.first_aid_kit", uses=5)]
    assert asked(interface, Topic.USES) == [Number(Topic.USES, minimum=1)]


def test_a_weapon_with_ammo_asks_how_many_come_with_it(content):
    game = new_game(content, *STREET)
    interface = ScriptedInterface(on_the_street(Manual.TAKE_ITEM, "weapon.pistol", 7))

    play(game, interface)

    assert game.character.items == [PISTOL]
    assert game.character.ammo == {"bullets": 7}
    assert asked(interface, Topic.AMMO) == [Number(Topic.AMMO, minimum=0)]
    assert told(interface, AmmoChanged) == [AmmoChanged("bullets", 7, 7)]


def test_the_player_takes_ammo(content):
    game = new_game(content, *STREET)
    interface = ScriptedInterface(on_the_street(Manual.TAKE_ITEM, "shells", 3))

    play(game, interface)

    assert game.character.ammo == {"shells": 3}


def test_the_player_loses_an_item_or_ammo(content):
    game = new_game(content, *STREET)
    game.add_item(ROPE)
    game.gain_ammo("bullets", 5)
    interface = ScriptedInterface(
        on_the_street(Manual.LOSE_ITEM, ItemAt(ROPE, Place.CARRIED), Manual.LOSE_ITEM, "bullets", 2)
    )

    play(game, interface)

    assert game.character.items == []
    assert game.character.ammo == {"bullets": 3}
    assert told(interface, ItemLost) == [ItemLost(ROPE)]
    first = asked(interface, Topic.ITEM)[0]
    assert first.options == (ItemAt(ROPE, Place.CARRIED), "bullets", Manual.BACK)
    assert asked(interface, Topic.AMOUNT)[-1] == Number(Topic.AMOUNT, minimum=1, maximum=5)


def test_losing_the_backpack_is_offered_only_with_one(content):
    game = new_game(content, *STREET)
    interface = ScriptedInterface(on_the_street())
    play(game, interface)
    assert Manual.LOSE_BACKPACK not in asked(interface, Topic.BOOK)[0].options

    game = new_game(content, *STREET)
    game.add_item(BACKPACK)
    game.add_item(ROPE)
    interface = ScriptedInterface(on_the_street(Manual.LOSE_BACKPACK))
    play(game, interface)
    assert told(interface, BackpackLost) == [BackpackLost((BACKPACK, ROPE))]
    assert game.character.items == []
