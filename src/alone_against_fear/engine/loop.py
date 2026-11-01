"""The game loop (E4): a mission played turn by turn (design/game-flow.md, Mission).

The first game asks for Home. Then each turn: choose an action, move to a box (numbered, Food
upkeep), arrive. Arriving does nothing more yet: the Town Exploration roll, the Search and the
free actions come with book mode (E5) and later tasks. The loop ends at death (Life 0),
insanity (Sanity 0) or when the player quits.
"""

from __future__ import annotations

import logging

from ..dice import DiceCode
from .game import Arrival, Game, GameError
from .protocol import Action, Choose, End, Ended, Interface, Quit, Request, Topic
from .state import Position
from .town import boxes_of

PLACEHOLDER_LIFE = 8
PLACEHOLDER_SANITY = 8
"""Until character creation (E6): the base Life and Sanity, d6 Food, no items."""

FIRST_SHEET = Position(0, 0)

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
        interface.tell(Arrival(home, number))
    while (end := _ended(game)) is None:
        action = ask(interface, Choose(Topic.ACTION, (Action.MOVE, Action.QUIT)))
        if action is Action.QUIT:
            return End.QUIT
        to = ask(interface, Choose(Topic.MOVE, _reading_order(game.targets())))
        interface.tell(game.move(to))
    return end


def ask(interface: Interface, request: Request) -> object:
    """Ask the interface, refuse an answer that is not an option, and log it."""
    answer = interface.ask(request)
    if answer not in request.options:
        raise GameError(f"{answer!r} is not one of the options for {request.topic}")
    log.info("answer %s: %s", request.topic, _shown(answer))
    return request.options[request.options.index(answer)]  # the option itself, not a copy


def _ended(game: Game) -> End | None:
    """Death is checked first: a character at 0 Life and 0 Sanity is dead."""
    if game.character.life <= 0:
        return End.DEAD
    if game.character.sanity <= 0:
        return End.INSANE
    return None


def _reading_order(positions: set[Position]) -> tuple[Position, ...]:
    """Row by row, left to right, as the boxes are read on the map."""
    return tuple(sorted(positions, key=lambda p: (p.row, p.column)))


def _shown(answer: object) -> str:
    if isinstance(answer, Position):
        return str(tuple(answer))
    return str(answer)
