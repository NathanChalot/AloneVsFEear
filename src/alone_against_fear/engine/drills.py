"""Drills (T1): short scoped runs the player tries in a break, 5 to 15 minutes each.

A drill sets up a start through the engine, as a test does (a pregenerated character, a
situation), then the game loop runs as usual until the drill's natural end, told as
`End.DRILL_OVER`; death, insanity and quitting end it too. No rule changes. Each task from T1
on adds its drill (WorkingWithClaude.md, Playtesting).
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass

from ..content import Effect
from . import creation, loop
from .game import Game
from .protocol import Choose, Interface, Topic, ask
from .state import End, Stat

WALK_BOXES = 10
"""The walk drill: boxes walked from Home."""
LASTING_BOXES = 6
"""The lasting drill: boxes walked from Home, two meals with Eating Disorder."""
EATING_DISORDER = "mental_scar.eating_disorder"
LASTING_EFFECT = Effect(basic=-1)
"""The lasting drill's effect: -1 to every roll, for the next 3 boxes."""
LASTING_EFFECT_BOXES = 3

log = logging.getLogger(__name__)

Setup = Callable[[Game, Interface], loop.Stop]
"""Sets the drill's start up and gives its stop condition."""


@dataclass(frozen=True)
class Drill:
    about: str
    """One line shown when the drill starts: what to try, and when it ends."""
    setup: Setup


def run(name: str, game: Game, interface: Interface) -> End:
    """Set the drill up on a new campaign, then play until its natural end."""
    drill = DRILLS[name]
    log.info("drill %s", name)
    stop = drill.setup(game, interface)
    return loop.play(game, interface, stop)


def _creation(game: Game, interface: Interface) -> loop.Stop:
    return lambda game: game.campaign.character is not None


def _walk(game: Game, interface: Interface) -> loop.Stop:
    _pregenerated(game, interface)
    return _after_boxes(WALK_BOXES)


def _lasting(game: Game, interface: Interface) -> loop.Stop:
    """Eating Disorder (a meal every 3 boxes) and a lasting effect set at Home, so its end
    shows the box it ends in."""
    _pregenerated(game, interface)
    game.gain_mental_scar(EATING_DISORDER)
    loop.choose_home(game, interface)
    game.add_lasting(LASTING_EFFECT, LASTING_EFFECT_BOXES)
    return _after_boxes(LASTING_BOXES)


def _xp(game: Game, interface: Interface) -> loop.Stop:
    """XP enough to raise the dearest Skill held to Expert and buy the dearest new one; the
    drill ends when nothing more can be bought."""
    _pregenerated(game, interface)
    skills = game.content.skills
    held = game.character.skills
    expert = max(skills[id_].xp for id_ in held if skills[id_].expert is not None)
    new = max(skill.xp for skill in skills.values() if skill.id not in held)
    game.gain(Stat.XP, expert + new)
    return lambda game: not game.purchases()


def _pregenerated(game: Game, interface: Interface) -> None:
    options = tuple(game.content.pregenerated)
    creation.pregenerated(game, ask(interface, Choose(Topic.PREGENERATED, options)))


def _after_boxes(boxes: int) -> loop.Stop:
    """Over once the character has walked `boxes` boxes from Home (box 1)."""
    return lambda game: game.campaign.box_counter >= 1 + boxes


DRILLS = {
    "creation": Drill("Create a character; the drill ends with the sheet done.", _creation),
    "walk": Drill(
        f"A pregenerated character at Home walks {WALK_BOXES} boxes: exploration and book mode.",
        _walk,
    ),
    "lasting": Drill(
        "A pregenerated character with Eating Disorder (a meal every 3 boxes) and -1 to "
        f"every roll for the next {LASTING_EFFECT_BOXES} boxes walks {LASTING_BOXES} boxes; "
        "add and remove lasting effects of your own.",
        _lasting,
    ),
    "xp": Drill(
        "A pregenerated character with XP to spend: buy a Skill, raise one to Expert. The "
        "drill ends when nothing more can be bought.",
        _xp,
    ),
}
