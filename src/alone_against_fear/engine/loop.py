"""The game loop (E4): a mission played turn by turn (design/game-flow.md, Mission).

The first game asks for Home. Then each turn: free actions, until the player moves to a
box (numbered, Food upkeep) and arrives, or quits. Arriving rolls Town Exploration in a new box
and a 1 in 6 chance of a Random Encounter in a visited one; what is reached goes through book
mode (E5a), whose actions follow the entry to other tables and events; the player applies what
the engine cannot read with manual actions (E5b). Home is box 1 and rolls nothing. The free
actions: move, Search while the box may be Searched, apply an effect (the manual actions about
the character), attach a sheet once one is full, quit. With notes, the Search first asks the
modifier they give.
The loop ends at death (Life 0), insanity (Sanity 0) or when the player quits.
"""

from __future__ import annotations

import logging

from ..dice import Chance, DiceCode
from . import book_mode, manual
from .game import Arrival, Game
from .protocol import (
    Action,
    Choose,
    End,
    Ended,
    Interface,
    Number,
    Quit,
    SheetAttached,
    Topic,
    Wandering,
    ask,
)
from .state import Position
from .town import boxes_of

PLACEHOLDER_LIFE = 8
PLACEHOLDER_SANITY = 8
"""Until character creation (E6): the base Life and Sanity, d6 Food, no items."""

FIRST_SHEET = Position(0, 0)
TOWN_EXPLORATION = "table.town_exploration"
RANDOM_ENCOUNTER = "table.random_encounter"
WANDERING = Chance(1)
"""The Random Encounter chance in a visited box. Safe Houses (Home included, see
design/rulings.md) and left-behind encounters change it with their tasks (E11, E15)."""

log = logging.getLogger(__name__)


def play(game: Game, interface: Interface) -> End:
    """Play until the game ends, and say why. A campaign under way goes on where it stands."""
    try:
        end = _turns(game, interface)
    except Quit:
        end = End.QUIT
    log.info("game ends: %s", end)
    interface.tell(Ended(end))
    return end


def _turns(game: Game, interface: Interface) -> End:
    if game.campaign.character is None:
        food = DiceCode.parse("d6").roll(game.dice).total
        game.create_character(life=PLACEHOLDER_LIFE, sanity=PLACEHOLDER_SANITY, food=food)
    if game.campaign.home is None:
        home = ask(interface, Choose(Topic.HOME, tuple(boxes_of(FIRST_SHEET))))
        number = game.choose_home(home)
        interface.tell(Arrival(home, number, new=True))
    while (end := game.ended()) is None:
        action = ask(interface, Choose(Topic.ACTION, _actions(game)))
        match action:
            case Action.QUIT:
                return End.QUIT
            case Action.MOVE:
                to = ask(interface, Choose(Topic.MOVE, _reading_order(game.targets())))
                _arrive(game, interface, game.move(to))
            case Action.APPLY:
                manual.apply_effects(game, interface)
            case Action.SEARCH:
                modifier = ask(interface, Number(Topic.MODIFIER)) if game.character.notes else 0
                searched = game.search(modifier)
                interface.tell(searched)
                book_mode.follow(game, interface, searched.rolled)
            case Action.SHEET:
                sheet = ask(interface, Choose(Topic.SHEET, _reading_order(game.new_sheets())))
                game.add_sheet(sheet)
                interface.tell(SheetAttached(sheet))
    return end


def _actions(game: Game) -> tuple[Action, ...]:
    """The free actions: move first and quit last, so they keep their place."""
    search = (Action.SEARCH,) if game.may_search() else ()
    sheet = (Action.SHEET,) if game.new_sheets() else ()
    return (Action.MOVE, *search, Action.APPLY, *sheet, Action.QUIT)


def _arrive(game: Game, interface: Interface, arrival: Arrival) -> None:
    """Tell the arrival, then roll what the box calls for and resolve it, unless the Food
    upkeep killed the character."""
    interface.tell(arrival)
    if game.ended():
        return
    if arrival.new:
        book_mode.resolve(game, interface, TOWN_EXPLORATION)
        return
    wandering = WANDERING.roll(game.dice)
    interface.tell(Wandering(wandering.face, wandering.success))
    if wandering.success:
        book_mode.resolve(game, interface, RANDOM_ENCOUNTER)


def _reading_order(positions: set[Position]) -> tuple[Position, ...]:
    """Row by row, left to right, as the boxes are read on the map."""
    return tuple(sorted(positions, key=lambda p: (p.row, p.column)))
