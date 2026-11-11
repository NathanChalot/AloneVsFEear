"""Moments and reactions (E8, design/effects.md, Moments).

A moment is a point in play that the engine announces. Announcing it runs the reactions
waiting for it, then counts down the lasting effects that count it, telling the interface
each one that ends. A reaction may tell and, later, ask the player (spend Luck, a script's
choice), so a moment is announced where the engine holds the interface, as book mode is.

The reactions here are the rules' own, always in play: the Food upkeep on each box of time.
Reactions held by an item, a box or a creature, written as scripts, come with E10; the order
of several reactions on one moment (helpful first, design/rulings.md, Effects) with E12.
"""

from __future__ import annotations

import logging
from collections.abc import Callable

from .game import Game
from .protocol import EffectEnded, FoodUpkeep, Interface
from .state import Moment

type Reaction = Callable[[Game, Interface], None]

log = logging.getLogger(__name__)


def food_upkeep(game: Game, interface: Interface) -> None:
    """1 Food once the Food interval has passed since the last meal, or 1 Life without Food
    (`1_1_main_rules.md`, Food; design/rulings.md, Map)."""
    result = game.food_upkeep()
    if result is not None:
        interface.tell(FoodUpkeep(result))


RULES: dict[Moment, tuple[Reaction, ...]] = {Moment.TIME_PASSES: (food_upkeep,)}
"""The reactions of the rules themselves, by the moment they wait for."""


def announce(game: Game, interface: Interface, moment: Moment) -> None:
    """A moment happens: its reactions run, then the lasting effects counting it go down and
    the ones that end are told."""
    log.info("moment: %s", moment)
    for reaction in RULES.get(moment, ()):
        reaction(game, interface)
    for ended in game.count_down(moment):
        interface.tell(EffectEnded(ended))
