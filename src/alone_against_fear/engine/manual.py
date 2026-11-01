"""Manual actions (E5b): how the player applies a text the engine cannot read.

Book mode shows an entry the engine cannot play; the player applies what it does with these
actions. Each is an engine operation opened to the player, so it goes through the rules: only
what the rules allow is offered, and the engine keeps every number (design/mvp-scope.md, Book
mode). Offered in the resolve step, after an entry the engine cannot read; the ones about the
character also as the free action "apply an effect" (a lasting effect noted earlier, on a turn
with no entry). Marking a Safe House is about the town: only with the entry that gives it.
Notes are the player's reminders of what the engine cannot track yet. Items (take, drop) come
once R3 gives them IDs; fighting a creature with E12.
"""

from __future__ import annotations

from enum import StrEnum

from .game import Game
from .protocol import (
    Changed,
    Choose,
    Interface,
    Marked,
    NoteRemoved,
    NoteWritten,
    Number,
    Text,
    Topic,
    ask,
)
from .state import Mark, Stat


class Manual(StrEnum):
    GAIN = "gain"
    """Gain Life, Sanity, Food, XP or Clues. No max until E6."""
    LOSE = "lose"
    """Lose one of them, down to 0: only what the character has can be lost."""
    ROLL = "roll"
    """A roll vs L, the L and modifier typed from the text."""
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
    actions += [Manual.ROLL, Manual.WRITE_NOTE]
    if game.character.notes:
        actions.append(Manual.REMOVE_NOTE)
    return tuple(actions)


def apply(game: Game, interface: Interface, action: Manual) -> None:
    """Ask what the action needs, apply it through the engine, and tell what happened."""
    match action:
        case Manual.GAIN:
            stat = ask(interface, Choose(Topic.STAT, tuple(Stat)))
            amount = ask(interface, Number(Topic.AMOUNT, minimum=1))
            interface.tell(Changed(stat, amount, game.gain(stat, amount)))
        case Manual.LOSE:
            stat = ask(interface, Choose(Topic.STAT, _losable(game)))
            amount = min(ask(interface, Number(Topic.AMOUNT, minimum=1)), _value(game, stat))
            interface.tell(Changed(stat, -amount, game.lose(stat, amount)))
        case Manual.ROLL:
            level = ask(interface, Number(Topic.LEVEL, minimum=1))
            modifier = ask(interface, Number(Topic.MODIFIER))
            interface.tell(game.roll_vs(level, modifier))
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


def _losable(game: Game) -> tuple[Stat, ...]:
    return tuple(stat for stat in Stat if _value(game, stat) > 0)


def _value(game: Game, stat: Stat) -> int:
    return getattr(game.character, stat)
