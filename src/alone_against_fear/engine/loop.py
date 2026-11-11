"""The game loop (E4): a mission played turn by turn (design/game-flow.md, Mission).

A new campaign, or one whose character is gone, creates a character (E6). The first game asks
for Home. Then each turn: free actions, until the player moves to a
box (numbered, a box of time announced: the Food upkeep, lasting effects ending, E8) and
arrives, or quits. Arriving rolls Town Exploration in a new box
and a 1 in 6 chance of a Random Encounter in a visited one; what is reached goes through book
mode (E5a), whose actions follow the entry to other tables and events; the player applies what
the engine cannot read with manual actions (E5b). Home is box 1 and rolls nothing. The free
actions: move, Search while the box may be Searched, apply an effect (the manual actions about
the character), spend XP while it can buy a Skill, attach a sheet once one is full, quit. With
notes, the Search first asks the modifier they give.
The loop ends at death (Life 0), insanity (Sanity 0) or when the player quits; a drill (T1)
also ends it when its stop condition holds, checked after creation and before each turn.
"""

from __future__ import annotations

import logging
from collections.abc import Callable

from ..dice import Chance
from . import book_mode, creation, manual, moments
from .game import Arrival, Game
from .manual import Manual
from .protocol import (
    Action,
    Bought,
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
from .state import Moment, Position
from .town import boxes_of

FIRST_SHEET = Position(0, 0)
TOWN_EXPLORATION = "table.town_exploration"
RANDOM_ENCOUNTER = "table.random_encounter"
WANDERING = Chance(1)
"""The Random Encounter chance in a visited box. Safe Houses (Home included, see
design/rulings.md) and left-behind encounters change it with their tasks (E11, E15)."""

log = logging.getLogger(__name__)

Stop = Callable[[Game], bool]
"""A drill's natural end (T1): true once the drill is over."""


def play(game: Game, interface: Interface, stop: Stop | None = None) -> End:
    """Play until the game ends, and say why. A campaign under way goes on where it stands.
    A drill gives its `stop`; death and insanity end the game first."""
    try:
        end = _turns(game, interface, stop or _never)
    except Quit:
        end = End.QUIT
    log.info("game ends: %s", end)
    interface.tell(Ended(end))
    return end


def choose_home(game: Game, interface: Interface) -> None:
    """The first game asks for Home: any box of the first sheet, box 1."""
    home = ask(interface, Choose(Topic.HOME, tuple(boxes_of(FIRST_SHEET))))
    number = game.choose_home(home)
    interface.tell(Arrival(home, number, new=True))


def _never(game: Game) -> bool:
    return False


def _turns(game: Game, interface: Interface, stop: Stop) -> End:
    if game.campaign.character is None:
        creation.create(game, interface)
        if stop(game):
            return End.DRILL_OVER
    if game.campaign.home is None:
        choose_home(game, interface)
    while (end := game.ended()) is None:
        if stop(game):
            return End.DRILL_OVER
        action = ask(interface, Choose(Topic.ACTION, _actions(game)))
        match action:
            case Action.QUIT:
                return End.QUIT
            case Action.MOVE:
                to = ask(interface, Choose(Topic.MOVE, _reading_order(game.targets())))
                _arrive(game, interface, game.move(to))
            case Action.APPLY:
                manual.apply_effects(game, interface)
            case Action.SPEND_XP:
                _spend_xp(game, interface)
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
    spend = (Action.SPEND_XP,) if game.purchases() else ()
    sheet = (Action.SHEET,) if game.new_sheets() else ()
    return (Action.MOVE, *search, Action.APPLY, *spend, *sheet, Action.QUIT)


def _spend_xp(game: Game, interface: Interface) -> None:
    """Buy one Skill or raise one to Expert, or go back. XP may be spent at any moment
    (`1_1_main_rules.md`, Experience); between moves is enough until a rule needs more."""
    purchase = ask(interface, Choose(Topic.PURCHASE, (*game.purchases(), Manual.BACK)))
    if purchase is not Manual.BACK:
        game.buy(purchase)
        interface.tell(Bought(purchase))


def _arrive(game: Game, interface: Interface, arrival: Arrival) -> None:
    """Tell the arrival, announce the box of time it took (E8), then roll what the box calls
    for and resolve it, unless the Food upkeep killed the character."""
    interface.tell(arrival)
    moments.announce(game, interface, Moment.TIME_PASSES)
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
