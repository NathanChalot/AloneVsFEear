"""Carrying, played (E9, design/inventory.md, Picking something up): the engine asks, the
player answers.

What a text or a roll gives is taken through `take` and `gain_food`: it fits, or the player
leaves an item here to make room, holds the new item in a free hand, or leaves it. The manual
actions about items (take what a text gives, lose an item or ammo, lose the backpack) and the
roll for items left in a box on coming back are here too; `Game` keeps every limit.
"""

from __future__ import annotations

from ..content import AMMO_TYPES
from . import inventory
from .game import Game
from .protocol import (
    AmmoChanged,
    BackpackLost,
    Changed,
    Choose,
    Interface,
    ItemAt,
    ItemLost,
    ItemMoved,
    ItemTaken,
    Topic,
    ask,
)
from .state import Item, Place, Stat

UNARMED = "weapon.unarmed_attack"
"""In the weapon summary, but never held."""


def take(game: Game, interface: Interface, item: Item) -> Place:
    """Take a new item: carried if it fits; otherwise the player leaves something here and
    tries again, holds it, or leaves it here. Returns where it went. With no box yet (at
    creation), leaving it loses it."""
    while game.room() < inventory.slots(game.content, item, Place.CARRIED):
        options = (*_freeing(game), *_hands_for(game, item), Place.BOX)
        answer = ask(interface, Choose(Topic.ROOM, options, about=item))
        if isinstance(answer, ItemAt):
            leave(game, interface, answer)
            continue
        if answer is Place.BOX and game.campaign.position is None:
            interface.tell(ItemLost(item))
            return Place.BOX
        game.add_item(item, answer)
        interface.tell(ItemTaken(item, answer))
        return answer
    game.add_item(item)
    interface.tell(ItemTaken(item))
    return Place.CARRIED


def gain_food(game: Game, interface: Interface, amount: int) -> int:
    """Gain Food: it fits under the Food limit, then in the item slots left; for the rest the
    player leaves items here to make room, or leaves the Food. Returns how much was gained."""
    character = game.character
    while character.food + amount > game.max(Stat.FOOD) and (freeing := _freeing(game)):
        answer = ask(interface, Choose(Topic.ROOM, (*freeing, Place.BOX), about=Stat.FOOD))
        if answer is Place.BOX:
            break
        leave(game, interface, answer)
    before = character.food
    value = game.gain(Stat.FOOD, amount)
    interface.tell(Changed(Stat.FOOD, value - before, value))
    return value - before


def leave(game: Game, interface: Interface, at: ItemAt) -> None:
    """Leave an item in the box the character stands in, or lose it with no box yet."""
    if game.campaign.position is None:
        game.remove_item(at.item, here=at.place)
        interface.tell(ItemLost(at.item))
        return
    move(game, interface, at, Place.BOX)


def move(game: Game, interface: Interface, at: ItemAt, to: Place) -> None:
    game.move_item(at.item, to, here=at.place)
    interface.tell(ItemMoved(at.item, at.place, to))


def items_at(game: Game) -> tuple[ItemAt, ...]:
    """Every item the character has, then those left here: hands, carried, worn, box. Two
    equal items in one place are one option (ten ropes carried: leave a rope)."""
    c = game.character
    held = (
        *(ItemAt(i, Place.HANDS) for i in c.hands),
        *(ItemAt(i, Place.CARRIED) for i in c.items),
        *(ItemAt(i, Place.WORN) for i in c.worn),
    )
    here = () if game.campaign.position is None else game.box_items()
    return tuple(dict.fromkeys((*held, *(ItemAt(i, Place.BOX) for i in here))))


def _freeing(game: Game) -> tuple[ItemAt, ...]:
    """The items whose leaving makes room: carried or worn, taking a slot."""
    return tuple(
        at
        for at in items_at(game)
        if at.place in (Place.CARRIED, Place.WORN)
        and inventory.slots(game.content, at.item, at.place) > 0
    )


def _hands_for(game: Game, item: Item) -> tuple[Place, ...]:
    return (Place.HANDS,) if game.hands_needed(item) <= game.free_hands() else ()


# --- For the manual actions about items (`manual.py`) -----------------------------------


def takeable(game: Game) -> tuple[str, ...]:
    """What a text may give: every item, every weapon that can be held (not a heading that
    names two, not an unarmed attack), every ammo type."""
    content = game.content
    weapons = (w.id for w in [*content.weapons.values(), *content.variants.values()])
    holdable = sorted(w for w in weapons if not content.weapon(w).variants and w != UNARMED)
    return (*sorted(content.items), *holdable, *AMMO_TYPES)


def losable(game: Game) -> tuple[ItemAt | str, ...]:
    """What a text may take: an item the character has, or ammo of a type they have."""
    held = tuple(at for at in items_at(game) if at.place is not Place.BOX)
    return (*held, *(ammo for ammo in AMMO_TYPES if game.character.ammo.get(ammo)))


def has_backpack(game: Game) -> bool:
    return any(item.id == inventory.BACKPACK for item in game.character.items)


def lose_backpack(game: Game, interface: Interface) -> None:
    before = game.character.food
    interface.tell(BackpackLost(game.lose_backpack()))
    if (value := game.character.food) != before:
        interface.tell(Changed(Stat.FOOD, value - before, value))


def gain_ammo(game: Game, interface: Interface, ammo: str, amount: int) -> None:
    interface.tell(AmmoChanged(ammo, amount, game.gain_ammo(ammo, amount)))


def come_back(game: Game, interface: Interface) -> None:
    """Back in a box where items were left: they may be gone (design/rulings.md, Inventory)."""
    if (rolled := game.roll_left_items()) is not None:
        interface.tell(rolled)
