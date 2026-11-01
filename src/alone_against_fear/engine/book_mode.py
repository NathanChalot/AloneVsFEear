"""Resolving a box, and book mode (E5a): design/mvp-scope.md, Book mode.

Arriving rolls a table; the box is then resolved before anything else. Each entry reached
leads on as its text says, until it leads nowhere. A copied entry whose lead is written
(`leads.LEADS`) plays itself: it rolls on the table named, asks when the text gives a choice,
rolls the die the text rolls. What the engine cannot read is book mode: the entry of a table
not copied yet, or a numbered event, is pointed to in its source, and the player says where
its text leads (a table, an event, or nowhere else). Before that, the player applies the text
with manual actions (E5b): the menu comes back after each one, so the whole entry is applied
before the player leaves it. A character at 0 Life or Sanity is offered only the manual actions
and "nowhere else": the chain stops at the entry that kills, once its effects are applied.
Everything reached is told to the interface and recorded. As content is copied and written,
fewer entries come to book mode.
"""

from __future__ import annotations

from ..dice import DiceCode
from . import manual
from .game import Game, GameError, Rolled
from .leads import LEADS, Auto, Choice, DieRoll, Nowhere
from .manual import Manual
from .protocol import Book, Choose, EventPlayed, Interface, LeadRolled, Topic, ask

LEAD_DIE = DiceCode.parse("d6")


def resolve(game: Game, interface: Interface, id_: str) -> None:
    """Reach a table or event, then follow where each entry leads until it leads nowhere."""
    next_id: str | None = id_
    while next_id is not None:
        next_id = _lead(game, interface, _reach(game, interface, next_id))


def follow(game: Game, interface: Interface, rolled: Rolled) -> None:
    """Tell a table already rolled (a Search), then follow its entry as `resolve` does."""
    interface.tell(rolled)
    next_id = _lead(game, interface, rolled)
    if next_id is not None:
        resolve(game, interface, next_id)


def _reach(game: Game, interface: Interface, id_: str) -> Rolled | None:
    """Roll a table or play an event, and tell the interface. None for an event."""
    if id_.startswith("event."):
        game.play_event(id_)
        interface.tell(EventPlayed(id_))
        return None
    if id_.startswith("table."):
        rolled = game.roll_table(id_)
        interface.tell(rolled)
        return rolled
    raise GameError(f"cannot reach {id_}")


def _lead(game: Game, interface: Interface, rolled: Rolled | None) -> str | None:
    """Where the entry reached leads: a table or event ID, or None for nowhere."""
    if rolled is None or rolled.entry_id is None:  # an event, or a table not copied yet
        return _book(game, interface, (Book.TABLE, Book.EVENT))
    entry = game.content.entry(rolled.entry_id)
    match LEADS.get(entry.id):
        case Auto(ref=ref):
            return ref
        case Choice(refs=refs):
            return ask(interface, Choose(Topic.CHOICE, refs))
        case DieRoll() as die:
            face = LEAD_DIE.roll(game.dice).total
            ref = die.ref_for(face)
            interface.tell(LeadRolled(entry.id, face, ref))
            return ref
        case Nowhere():
            return None
        case None:  # copied, but not written: the player applies it and reads where it goes
            return _book(game, interface, entry.refs)


def _book(game: Game, interface: Interface, leads: tuple[str, ...]) -> str | None:
    """The player reads the text: applies it with manual actions, then says where it leads.
    `leads` are the entry's own tables, or `Book.TABLE` and `Book.EVENT` when only its source
    knows. At 0 Life or Sanity, it leads nowhere else."""
    while True:
        where = () if game.ended() else leads
        answer = ask(interface, Choose(Topic.BOOK, (*where, *manual.offered(game), Book.DONE)))
        match answer:
            case Manual():
                manual.apply(game, interface, answer)
            case Book.DONE:
                return None
            case Book.TABLE:
                return ask(interface, Choose(Topic.TABLE, tables(game)))
            case Book.EVENT:
                return ask(interface, Choose(Topic.EVENT, events(game)))
            case _:
                return answer


def tables(game: Game) -> tuple[str, ...]:
    """Every table, copied or not, by name."""
    content = game.content
    catalogued = [item for item in content.catalogue.values() if item.id.startswith("table.")]
    named = {table.id: table.name or table.id for table in content.tables.values()}
    named |= {table.id: table.name for table in catalogued}
    return tuple(sorted(named, key=lambda id_: named[id_].lower()))


def events(game: Game) -> tuple[str, ...]:
    """Every numbered event, in the book's order."""
    return tuple(event.id for event in game.content.events())
