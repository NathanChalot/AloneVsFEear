"""Manual actions (E5b): how the player applies a text the engine cannot read.

Book mode shows an entry the engine cannot play; the player applies what it does with these
actions. Each is an engine operation opened to the player, so it goes through the rules: only
what the rules allow is offered, and the engine keeps every number (design/mvp-scope.md, Book
mode). Offered in the resolve step, after an entry the engine cannot read; the ones about the
character also as the free action "apply an effect" (a lasting effect noted earlier, on a turn
with no entry). Marking a Safe House is about the town: only with the entry that gives it.
A modifier for a number of boxes is a lasting effect the engine tracks and ends on time
(E8): on every roll or on one roll type, for the next N boxes or until removed. Notes are the
player's reminders of what the engine cannot track yet (a restriction, "until you reach a Safe
House"). Items (E9): take what a text gives (an item with its count or uses, a weapon with
its ammo, ammo), lose an item or ammo, lose the backpack; fighting a creature with E12.
"""

from __future__ import annotations

from enum import StrEnum

from ..content import AMMO_TYPES, Effect
from ..effect_targets import RollType, Tag, with_implied
from . import carrying
from .game import Game
from .inventory import is_weapon
from .protocol import (
    AmmoChanged,
    Changed,
    Choose,
    Interface,
    ItemAt,
    ItemLost,
    LastingAdded,
    LastingRemoved,
    Marked,
    NoteRemoved,
    NoteWritten,
    Number,
    Text,
    Topic,
    ask,
)
from .state import Item, Mark, Stat


class Target(StrEnum):
    ALL_ROLLS = "all_rolls"
    """A lasting effect on every roll: no roll type (design/rulings.md, Effects)."""


ALL_ROLLS = Target.ALL_ROLLS


class Manual(StrEnum):
    GAIN = "gain"
    """Gain Life, Sanity, Food, XP or Clues; Life and Sanity stop at their max."""
    LOSE = "lose"
    """Lose one of them, down to 0: only what the character has can be lost."""
    TAKE_ITEM = "take_item"
    """Take an item, a weapon or ammo a text gives, through the room rules (E9)."""
    LOSE_ITEM = "lose_item"
    """Lose an item or ammo the character has (E9)."""
    LOSE_BACKPACK = "lose_backpack"
    """The backpack is stolen or destroyed, with every carried item (E9)."""
    ROLL = "roll"
    """A roll vs L: its type, the L and the modifier typed from the text; the effects held
    add theirs (E7)."""
    ADD_LASTING = "add_lasting"
    """Add a lasting effect: a modifier on every roll or one roll type, for the next N boxes
    or until removed; the engine applies it and ends it (E8)."""
    REMOVE_LASTING = "remove_lasting"
    """Remove a lasting effect, picked among the character's."""
    WRITE_NOTE = "write_note"
    """Write a note: a lasting effect or a modifier to remember."""
    REMOVE_NOTE = "remove_note"
    """Remove a note, picked among the character's notes."""
    SAFE_HOUSE = "safe_house"
    """Mark the box the character stands in as a Safe House."""
    BACK = "back"
    """Leave the "apply an effect" menu."""


def offered(game: Game) -> tuple[Manual, ...]:
    """The manual actions of an entry the rules allow now, always in the same order."""
    actions = list(_about_the_character(game))
    position = game.campaign.position
    if position is not None and Mark.SAFE_HOUSE not in game.campaign.map.boxes[position].marks:
        actions.append(Manual.SAFE_HOUSE)
    return tuple(actions)


def apply_effects(game: Game, interface: Interface) -> None:
    """The free action "apply an effect": the manual actions about the character, again and
    again until the player goes back."""
    while True:
        options = (*_about_the_character(game), Manual.BACK)
        action = ask(interface, Choose(Topic.APPLY, options))
        if action is Manual.BACK:
            return
        apply(game, interface, action)


def _about_the_character(game: Game) -> tuple[Manual, ...]:
    actions = [Manual.GAIN]
    if _losable(game):
        actions.append(Manual.LOSE)
    actions.append(Manual.TAKE_ITEM)
    if carrying.losable(game):
        actions.append(Manual.LOSE_ITEM)
    if carrying.has_backpack(game):
        actions.append(Manual.LOSE_BACKPACK)
    actions += [Manual.ROLL, Manual.ADD_LASTING]
    if game.character.lasting:
        actions.append(Manual.REMOVE_LASTING)
    actions.append(Manual.WRITE_NOTE)
    if game.character.notes:
        actions.append(Manual.REMOVE_NOTE)
    return tuple(actions)


def apply(game: Game, interface: Interface, action: Manual) -> None:
    """Ask what the action needs, apply it through the engine, and tell what happened."""
    match action:
        case Manual.GAIN:
            stat = ask(interface, Choose(Topic.STAT, tuple(Stat)))
            amount = ask(interface, Number(Topic.AMOUNT, minimum=1))
            if stat is Stat.FOOD:
                carrying.gain_food(game, interface, amount)
                return
            before = _value(game, stat)
            value = game.gain(stat, amount)
            interface.tell(Changed(stat, value - before, value))
        case Manual.LOSE:
            stat = ask(interface, Choose(Topic.STAT, _losable(game)))
            amount = min(ask(interface, Number(Topic.AMOUNT, minimum=1)), _value(game, stat))
            interface.tell(Changed(stat, -amount, game.lose(stat, amount)))
        case Manual.TAKE_ITEM:
            _take_item(game, interface)
        case Manual.LOSE_ITEM:
            _lose_item(game, interface)
        case Manual.LOSE_BACKPACK:
            carrying.lose_backpack(game, interface)
        case Manual.ROLL:
            roll = ask(interface, Choose(Topic.ROLL, ROLLS))
            level = ask(interface, Number(Topic.LEVEL, minimum=1))
            tags = _tags(game, interface, roll)
            modifier = ask(interface, Number(Topic.MODIFIER))
            interface.tell(game.roll_vs(level, roll, tags, modifier))
        case Manual.ADD_LASTING:
            target = ask(interface, Choose(Topic.TARGET, (ALL_ROLLS, *RollType)))
            amount = ask(interface, Number(Topic.MODIFIER))
            if amount == 0:
                return
            boxes = ask(interface, Number(Topic.BOXES, minimum=0))
            roll = None if target is ALL_ROLLS else target
            lasting = game.add_lasting(Effect(basic=amount, roll=roll), boxes or None)
            interface.tell(LastingAdded(lasting))
        case Manual.REMOVE_LASTING:
            lasting = ask(interface, Choose(Topic.LASTING, tuple(game.character.lasting)))
            game.remove_lasting(lasting)
            interface.tell(LastingRemoved(lasting))
        case Manual.WRITE_NOTE:
            interface.tell(NoteWritten(game.add_note(ask(interface, Text(Topic.NOTE)))))
        case Manual.REMOVE_NOTE:
            note = ask(interface, Choose(Topic.NOTES, tuple(game.character.notes)))
            game.remove_note(note)
            interface.tell(NoteRemoved(note))
        case Manual.SAFE_HOUSE:
            position = game.campaign.position
            game.add_mark(position, Mark.SAFE_HOUSE)
            interface.tell(Marked(position, Mark.SAFE_HOUSE))


def _take_item(game: Game, interface: Interface) -> None:
    """The item, weapon or ammo a text gives, with what the player reads in the text: its
    count, its uses, the ammo that comes with a weapon."""
    given = ask(interface, Choose(Topic.ITEM, (*carrying.takeable(game), Manual.BACK)))
    content = game.content
    if given is Manual.BACK:
        return
    if given in AMMO_TYPES:
        amount = ask(interface, Number(Topic.AMOUNT, minimum=1))
        carrying.gain_ammo(game, interface, given, amount)
        return
    count = uses = None
    if given in content.items:
        entries = [content.entry(e) for e in content.items[given]]
        if any(entry.count is not None for entry in entries):
            count = ask(interface, Number(Topic.COUNT, minimum=1))
        if any(entry.uses is not None for entry in entries):
            uses = ask(interface, Number(Topic.USES, minimum=1))
    carrying.take(game, interface, Item(given, count=count, uses=uses))
    if is_weapon(content, Item(given)) and (ammo := content.weapon(given).ammo):
        if amount := ask(interface, Number(Topic.AMMO, minimum=0)):
            carrying.gain_ammo(game, interface, ammo, amount)


def _lose_item(game: Game, interface: Interface) -> None:
    """An item or ammo a text takes: used up, broken, stolen."""
    lost = ask(interface, Choose(Topic.ITEM, (*carrying.losable(game), Manual.BACK)))
    if lost is Manual.BACK:
        return
    if isinstance(lost, ItemAt):
        game.remove_item(lost.item, here=lost.place)
        interface.tell(ItemLost(lost.item))
        return
    held = game.character.ammo[lost]
    amount = ask(interface, Number(Topic.AMOUNT, minimum=1, maximum=held))
    interface.tell(AmmoChanged(lost, -amount, game.lose_ammo(lost, amount)))


ROLLS = tuple(roll for roll in RollType if roll is not RollType.SEARCH)
"""The rolls vs L; the Search is a free action of its own."""


def _tags(game: Game, interface: Interface, roll: RollType) -> frozenset[Tag]:
    """What a roll made by hand is about, asked only where an effect held depends on it: one
    yes or no per effect, in the character's order, skipped when the tags already given match
    it (a bow Attack is a ranged one: Good Shot is not asked about after Bow)."""
    tags: frozenset[Tag] = frozenset()
    for held in game.depending_on_tags(roll):
        if held.effect.tags & with_implied(tags):
            continue
        if ask(interface, Choose(Topic.TAG, (True, False), about=held)):
            tags |= held.effect.tags
    return tags


def _losable(game: Game) -> tuple[Stat, ...]:
    return tuple(stat for stat in Stat if _value(game, stat) > 0)


def _value(game: Game, stat: Stat) -> int:
    return getattr(game.character, stat)
