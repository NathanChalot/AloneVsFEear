"""The engine API (E2): the only way the game state is changed.

Every change is written to the log (logger `alone_against_fear`); the interface decides where
the log goes. The rules about these changes (limits, what a loss below zero means) come with
the tasks that need them.
"""

from __future__ import annotations

import logging
from collections.abc import Iterable
from dataclasses import dataclass

from ..content import CatalogueEvent, CatalogueTable, Content
from ..dice import Dice, DiceCode
from .state import (
    Box,
    Campaign,
    Character,
    End,
    Happened,
    History,
    Level,
    Mark,
    Mission,
    MoveKind,
    Note,
    Position,
    Stat,
    Upkeep,
)
from .town import boxes_of, neighbours, sheet_neighbours, sheet_of

FOOD_INTERVAL = 5
"""One Food every this many box numbers (Skills that change it come with E9)."""

PLACE_TABLES = frozenset(
    {
        "table.street",
        "table.cemetery",
        "table.house",
        "table.clinic",
        "table.place_of_worship",
        "table.military_installation_or_lab",
        "table.farm",
        "table.haunted_house",
        "table.store",
        "table.sewers",
        "table.railways",
        "table.school",
        "table.woods_or_park",
    }
)
"""The tables that make a box a place: rolled in a box, the box remembers them."""

SEARCH_TABLE = "table.search"
D6 = DiceCode.parse("d6")

log = logging.getLogger(__name__)


class GameError(Exception):
    """A change the game state does not allow."""


@dataclass(frozen=True)
class Arrival:
    """What entering a box did: its new number, whether it was its first visit, and what the
    Food upkeep did, if it was due."""

    position: Position
    number: int
    upkeep: Upkeep | None = None
    new: bool = False


@dataclass(frozen=True)
class Rolled:
    """A table was rolled: the result on each level (a nested table adds one) and the entry
    reached, or None for a table not copied yet (its source holds the entry)."""

    table_id: str
    results: tuple[int, ...]
    entry_id: str | None


@dataclass(frozen=True)
class RolledVsL:
    """A roll vs L: the die, the modifier, the total and whether it made the L. A natural 1
    always fails and a natural 6 always succeeds."""

    level: int
    modifier: int
    face: int
    total: int
    success: bool


@dataclass(frozen=True)
class Searched:
    """A Search roll: the die, the modifier and the Search table rolled with their result."""

    face: int
    modifier: int
    rolled: Rolled


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

    def ended(self) -> End | None:
        """Why the game is over, or None: dead at 0 Life (checked first, design/rulings.md),
        insane at 0 Sanity."""
        if self.character.life <= 0:
            return End.DEAD
        if self.character.sanity <= 0:
            return End.INSANE
        return None

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

    # --- Rolls -----------------------------------------------------------------------------

    def roll_vs(self, level: int, modifier: int = 0) -> RolledVsL:
        """Roll d6 + modifier vs L: made on L or more; a natural 1 always fails and a natural 6
        always succeeds (design/rulings.md, Combat). The modifier is the text's until the
        Skills and items give theirs (E7)."""
        face = D6.roll(self.dice).total
        total = face + modifier
        success = face != 1 and (face == 6 or total >= level)
        rolled = RolledVsL(level, modifier, face, total, success)
        log.info(
            "roll vs L%d at %+d: %d, total %d, %s",
            level,
            modifier,
            face,
            total,
            "success" if success else "failure",
        )
        return rolled

    def add_item(self, name: str) -> None:
        self.character.items.append(name)
        log.info("character takes %s", name)

    def remove_item(self, name: str) -> None:
        if name not in self.character.items:
            raise GameError(f"the character has no {name}")
        self.character.items.remove(name)
        log.info("character drops %s", name)

    def add_note(self, text: str) -> Note:
        """A note the player keeps, written at the current box number; the engine never
        reads it."""
        note = Note(text, self.campaign.box_counter)
        self.character.notes.append(note)
        log.info("character note at box %d: %s", note.box, note.text)
        return note

    def remove_note(self, note: Note) -> None:
        if note not in self.character.notes:
            raise GameError(f"the character has no note {note}")
        self.character.notes.remove(note)
        log.info("character note removed: %s", note.text)

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
        Low level: `move` and `choose_home` are the ways a character enters a box."""
        self.campaign.box_counter += 1
        number = self.campaign.box_counter
        box = self.campaign.map.boxes.setdefault(position, Box(position))
        box.numbers.append(number)
        log.info("box %d at %s", number, tuple(position))
        return number

    def choose_home(self, position: Position) -> int:
        """The player picks Home, any box of the first sheet. It is box 1 (the clock starts
        here), with no content roll and no Food upkeep."""
        if self.campaign.home is not None:
            raise GameError("Home is already chosen")
        if sheet_of(position) != (0, 0):
            raise GameError(f"Home must be on the first sheet, not {tuple(position)}")
        self.campaign.map.sheets.add(sheet_of(position))
        self.campaign.home = self.campaign.position = position
        return self.number_box(position)

    def targets(self, kind: MoveKind = MoveKind.NORMAL) -> set[Position]:
        """The boxes a move of this kind may go to. The player chooses among them."""
        here = self._position()
        around = neighbours(here, self.campaign.map.sheets)
        if kind is MoveKind.ESCAPE:
            # back to a box already visited; any neighbour when none is (first box)
            visited = {box for box in around if box in self.campaign.map.boxes}
            return visited or around
        return around

    def move(self, to: Position, kind: MoveKind = MoveKind.NORMAL) -> Arrival:
        """Move to a box: time passes, the box gets the next number, and the Food upkeep runs
        if the number is due. What arriving does in the box comes with the game loop (E4)."""
        if to not in self.targets(kind):
            raise GameError(f"cannot move from {tuple(self._position())} to {tuple(to)}")
        new = to not in self.campaign.map.boxes
        self.campaign.position = to
        number = self.number_box(to)
        return Arrival(to, number, self._upkeep(number), new=new)

    def _position(self) -> Position:
        if self.campaign.position is None:
            raise GameError("Home is not chosen yet")
        return self.campaign.position

    def _upkeep(self, number: int) -> Upkeep | None:
        """1 Food every 5 box numbers, or 1 Life without Food. Not clamped to the Life: dying
        comes with E13."""
        if number % FOOD_INTERVAL:
            return None
        if self.character.food > 0:
            self.lose(Stat.FOOD, 1)
            return Upkeep.ATE
        self.lose(Stat.LIFE, 1)
        return Upkeep.STARVED

    def is_full(self, sheet: Position) -> bool:
        """All 30 boxes of the sheet have been visited."""
        return all(box in self.campaign.map.boxes for box in boxes_of(sheet))

    def new_sheets(self) -> set[Position]:
        """Where a new sheet may be attached: against a side of a full sheet."""
        sheets = self.campaign.map.sheets
        full = {sheet for sheet in sheets if self.is_full(sheet)}
        return {new for sheet in full for new in sheet_neighbours(sheet)} - sheets

    def add_sheet(self, sheet: Position) -> None:
        """Attach a new sheet against the side of a full sheet. Starting one after a mission
        before the current is full is not designed yet (step 2)."""
        sheets = self.campaign.map.sheets
        if sheet in sheets:
            raise GameError(f"sheet {tuple(sheet)} is already attached")
        touching = sheet_neighbours(sheet) & sheets
        if not touching:
            raise GameError(f"sheet {tuple(sheet)} touches no sheet by a side")
        if not any(self.is_full(other) for other in touching):
            raise GameError(f"the sheets next to {tuple(sheet)} are not full")
        sheets.add(sheet)
        log.info("sheet attached at %s", tuple(sheet))

    # --- What a box remembers ---------------------------------------------------------

    def _box(self, position: Position) -> Box:
        if position not in self.campaign.map.boxes:
            raise GameError(f"box {tuple(position)} has not been visited")
        return self.campaign.map.boxes[position]

    def add_place(self, position: Position, place_id: str) -> None:
        self._box(position).places.append(place_id)
        log.info("box %s holds %s", tuple(position), place_id)

    def mark_searched(self, position: Position) -> None:
        self._box(position).searched = True
        log.info("box %s searched", tuple(position))

    def add_mark(self, position: Position, mark: str) -> None:
        self._box(position).marks.add(mark)
        log.info("box %s marked %s", tuple(position), mark)

    def remove_mark(self, position: Position, mark: str) -> None:
        self._box(position).marks.discard(mark)
        log.info("box %s loses mark %s", tuple(position), mark)

    def may_search(self) -> bool:
        """The box the character stands in may be Searched: only once, and never a Safe
        House (`5_how_the_game_works.md`). Libraries and ignored encounters come with E11."""
        box = self._box(self._position())
        return not box.searched and Mark.SAFE_HOUSE not in box.marks

    def search(self, modifier: int = 0) -> Searched:
        """Search the box: d6 + modifier on the Search table, a natural 1 stays 1, the result
        kept on the table. The box is Searched and the entry recorded."""
        if not self.may_search():
            raise GameError(f"box {tuple(self._position())} cannot be Searched")
        table = self.content.table(SEARCH_TABLE)
        face = D6.roll(self.dice).total
        results = DiceCode.parse(table.dice).results()
        result = face if face == 1 else max(results[0], min(results[-1], face + modifier))
        entry = table.entry_for(result)
        self.mark_searched(self._position())
        self._record_everywhere(Happened.PLAYED, entry.id)
        log.info("search at %+d: %d, result %d: %s", modifier, face, result, entry.id)
        return Searched(face, modifier, Rolled(SEARCH_TABLE, (result,), entry.id))

    # --- Tables and events ------------------------------------------------------------

    def roll_table(self, table_id: str) -> Rolled:
        """Roll a table, and the table nested in the entry reached if there is one. The entry
        is recorded as played; a place table makes the character's box that place. A table not
        copied yet is rolled all the same, with no entry: its source holds the text."""
        table = self.content.tables.get(table_id)
        if table is None:
            catalogued = self.content.catalogue.get(table_id)
            if not isinstance(catalogued, CatalogueTable):
                raise GameError(f"no such table: {table_id}")
            result = DiceCode.parse(catalogued.dice).roll(self.dice).total
            rolled = Rolled(table_id, (result,), None)
        else:
            results = []
            while True:
                results.append(DiceCode.parse(table.dice).roll(self.dice).total)
                entry = table.entry_for(results[-1])
                if entry.table is None:
                    break
                table = entry.table
            rolled = Rolled(table_id, tuple(results), entry.id)
            self._record_everywhere(Happened.PLAYED, entry.id)
        log.info("%s rolled %s: %s", table_id, rolled.results, rolled.entry_id or "not copied")
        if table_id in PLACE_TABLES and self.campaign.position is not None:
            box = self._box(self.campaign.position)
            if table_id not in box.places:
                self.add_place(box.position, table_id)
        return rolled

    def play_event(self, event_id: str) -> None:
        """A numbered event is played: recorded as played. Its text is in its source until it
        is copied (R6)."""
        if not isinstance(self.content.catalogue.get(event_id), CatalogueEvent):
            raise GameError(f"no such event: {event_id}")
        self._record_everywhere(Happened.PLAYED, event_id)

    def _record_everywhere(self, happened: Happened, id_: str) -> None:
        """Record at every level there is: the campaign, the character, the mission. Limits
        read whichever level their text names."""
        levels = [Level.CAMPAIGN]
        if self.campaign.character is not None:
            levels.append(Level.CHARACTER)
            if self.campaign.character.mission is not None:
                levels.append(Level.MISSION)
        for level in levels:
            self.record(level, happened, id_)

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
