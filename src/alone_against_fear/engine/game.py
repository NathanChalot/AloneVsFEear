"""The engine API (E2): the only way the game state is changed.

Every change is written to the log (logger `alone_against_fear`); the interface decides where
the log goes. The rules about these changes (limits, what a loss below zero means) come with
the tasks that need them.
"""

from __future__ import annotations

import logging
from collections.abc import Iterable

from ..content import Content
from ..dice import Dice
from .state import Box, Campaign, Character, Happened, History, Level, Mission, Position, Stat

log = logging.getLogger(__name__)


class GameError(Exception):
    """A change the game state does not allow."""


class Game:
    def __init__(self, dice: Dice, content: Content, campaign: Campaign | None = None) -> None:
        self.dice = dice
        self.content = content
        self.campaign = campaign if campaign is not None else Campaign()

    # --- Queries ---------------------------------------------------------------

    @property
    def character(self) -> Character:
        if self.campaign.character is None:
            raise GameError("there is no character yet")
        return self.campaign.character

    @property
    def mission(self) -> Mission:
        if self.character.mission is None:
            raise GameError("the character is not on a mission")
        return self.character.mission

    def history(self, level: Level) -> History:
        match level:
            case Level.CAMPAIGN:
                return self.campaign.history
            case Level.CHARACTER:
                return self.character.history
            case Level.MISSION:
                return self.mission.history

    # --- The character -----------------------------------------------------------

    def create_character(
        self,
        life: int,
        sanity: int,
        food: int,
        items: Iterable[str] = (),
    ) -> Character:
        """A new character, who continues the campaign; the last one is forgotten."""
        self.campaign.character = Character(life=life, sanity=sanity, food=food, items=[*items])
        log.info("new character: Life %d, Sanity %d, Food %d", life, sanity, food)
        return self.campaign.character

    def gain(self, stat: Stat, amount: int) -> int:
        """Add to one of the character's numbers; returns the new value."""
        _check_amount(stat, amount)
        return self._set(stat, getattr(self.character, stat) + amount, f"gains {amount}")

    def lose(self, stat: Stat, amount: int) -> int:
        """Take from one of the character's numbers; returns the new value. Not clamped:
        what a loss below zero means is a rule, decided by the task that needs it."""
        _check_amount(stat, amount)
        return self._set(stat, getattr(self.character, stat) - amount, f"loses {amount}")

    def _set(self, stat: Stat, value: int, change: str) -> int:
        setattr(self.character, stat, value)
        log.info("character %s %s, now %d", change, stat, value)
        return value

    def add_item(self, name: str) -> None:
        self.character.items.append(name)
        log.info("character takes %s", name)

    def remove_item(self, name: str) -> None:
        if name not in self.character.items:
            raise GameError(f"the character has no {name}")
        self.character.items.remove(name)
        log.info("character drops %s", name)

    # --- Missions --------------------------------------------------------------------

    def start_mission(self, mission_id: str) -> Mission:
        """A new mission; the last one is forgotten."""
        if not mission_id.startswith("mission.") or mission_id not in self.content:
            raise GameError(f"no such mission: {mission_id}")
        self.character.mission = Mission(id=mission_id)
        log.info("mission starts: %s", mission_id)
        return self.character.mission

    # --- The map and the clock ----------------------------------------------------------

    def number_box(self, position: Position) -> int:
        """Advance the clock and write the new box number in the box at `position`.
        Moves (neighbours, sheets, what arriving does) come in E3."""
        self.campaign.box_counter += 1
        number = self.campaign.box_counter
        box = self.campaign.map.boxes.setdefault(position, Box(position))
        box.numbers.append(number)
        log.info("box %d at %s", number, tuple(position))
        return number

    # --- History -------------------------------------------------------------------------

    def record(self, level: Level, happened: Happened, id_: str) -> None:
        history = self.history(level)
        history.counts[happened][id_] += 1
        log.info("%s: %s %s", level, happened, id_)

    def add_keyword(self, level: Level, keyword: str) -> None:
        self.history(level).keywords.add(keyword)
        log.info("%s keyword: %s", level, keyword)


def _check_amount(stat: Stat, amount: int) -> None:
    if amount < 0:
        raise GameError(f"a negative amount of {stat}: {amount}")
