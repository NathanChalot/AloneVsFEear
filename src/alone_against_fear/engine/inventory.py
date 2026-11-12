"""The inventory's rules (E9, design/inventory.md): what an item takes, read from the content.

Pure functions over the content and the character; `Game` keeps the state and checks the
limits with them. An item takes its entry's `slots` carried (1, 0 for negligible weight; a
bundle once, whatever its count) and its `worn` slots worn; a weapon takes 1 slot and its
`hands` in hand. What the rules say beyond a number is here, keyed by ID: the axe in one hand
with Strong (Expert), one set of clothes at a time.
"""

from __future__ import annotations

from ..content import Content
from .state import Character, Item, Place, SkillLevel

MAX_CARRIED = 20
""""This is the absolute maximum you can carry in the game" (`1_1_main_rules.md`)."""
BACKPACK = "item.backpack"
CLOTHES = frozenset({"item.dark_clothes", "item.stylish_clothes", "item.sport_clothes"})
""""You may wear only one set of clothes at a time.\""""
ONE_HANDED_WHEN_STRONG = frozenset({"weapon.axe"})
"""Two-handed weapons that Strong (Expert) uses one-handed."""
STRONG = "skill.strong"


def is_weapon(content: Content, item: Item) -> bool:
    return item.id in content.weapons or item.id in content.variants


def slots(content: Content, item: Item, place: Place) -> int:
    """The item slots an item takes where it is: carried or worn; none in hand or in a box."""
    if place is Place.CARRIED:
        return 1 if is_weapon(content, item) else content.item_entry(item.id).slots
    if place is Place.WORN:
        return content.item_entry(item.id).worn or 0
    return 0


def wearable(content: Content, item: Item) -> bool:
    """Its text says it can be worn (design/rulings.md, Inventory)."""
    return item.id in content.items and content.item_entry(item.id).worn is not None


def hands_needed(content: Content, character: Character, item: Item) -> int:
    if not is_weapon(content, item):
        return 1
    if item.id in ONE_HANDED_WHEN_STRONG and character.skills.get(STRONG) is SkillLevel.EXPERT:
        return 1
    return content.weapon(item.id).hands


def held_items(character: Character) -> tuple[Item, ...]:
    """Every item the character has, wherever they hold it: in hand, carried, worn."""
    return (*character.hands, *character.items, *character.worn)


def unit(content: Content, item: Item) -> str | None:
    """What the item's count or uses count, when its name does not say."""
    return content.item_entry(item.id).unit if item.id in content.items else None
