"""The terminal interface (E4): a minimal way to play.

It shows the character, the map and each request with numbered options, reads the player's
choice and checks it before answering, and narrates what the engine tells it. It reads the
game state to show it and changes it only through its answers. End of input (Ctrl-D) or Ctrl-C
quits. `main` sets up a game, with the log written to a file.

Resolving a box (E5a): the entry reached is shown with the notes it points to; a table not
copied yet points to its source and the number rolled, and asks where its text leads (`t` a
table, `e` a numbered event, `d` nowhere else). A table's own rules are shown the first time it
is rolled in this game, and again on request (`r`). Free actions have letters, so `m` always
moves and `q` always quits; tables to choose from are numbered.
"""

from __future__ import annotations

import argparse
import logging
from collections.abc import Callable, Sequence
from datetime import datetime
from pathlib import Path

from ..content import CatalogueEvent, CatalogueTable, Table, load_content
from ..dice import RandomDice
from ..engine import Arrival, Game, Position, Upkeep
from ..engine.game import Rolled
from ..engine.loop import play
from ..engine.protocol import (
    Action,
    Book,
    End,
    Ended,
    Event,
    EventPlayed,
    LeadRolled,
    Quit,
    Request,
    SheetAttached,
    Topic,
    Wandering,
)
from ..engine.town import SHEET_COLUMNS, SHEET_ROWS, sheet_neighbours

CELL = 5
"""Width of a box on the map: room for "[30]" or a box number in the thousands."""

ENDINGS = {
    End.DEAD: "You are dead. The game is over.",
    End.INSANE: "You have gone insane. The game is over.",
    End.QUIT: "You quit the game.",
}

KEYS = {
    Action.MOVE: ("m", "move"),
    Action.SHEET: ("s", "attach a new sheet"),
    Action.QUIT: ("q", "quit"),
    Book.TABLE: ("t", "a table"),
    Book.EVENT: ("e", "a numbered event"),
    Book.DONE: ("d", "nowhere else"),
}
"""Options with a letter of their own; tables and events to choose from are numbered."""
RULES_KEY = "r"

SIDES = {(0, -1): "above", (-1, 0): "left of", (1, 0): "right of", (0, 1): "below"}


class TerminalInterface:
    def __init__(
        self,
        game: Game,
        input_fn: Callable[[str], str] = input,
        output_fn: Callable[[str], None] = print,
    ) -> None:
        self.game = game
        self._input = input_fn
        self._output = output_fn
        self._seen: set[str] = set()
        """Tables whose own rules were shown in this game."""
        self._rules: Table | None = None
        """The last table with rules rolled in this box, to show them on request."""

    # --- The protocol --------------------------------------------------------------------

    def ask(self, request: Request) -> object:
        options = request.options
        match request.topic:
            case Topic.ACTION:
                self._output("")
                self._output(self._status())
                return self._menu(options, "What do you do? ")
            case Topic.CHOICE:
                return self._menu(options, "Your choice: ")
            case Topic.BOOK:
                return self._menu(options, "Where does the text lead? ")
            case Topic.HOME | Topic.MOVE:
                self._output(self._map(options))
                what = "Home" if request.topic is Topic.HOME else "Move to"
                return self._read(_by_number(options), f"{what}: choose a box [1-{len(options)}] ")
            case Topic.TABLE:
                for n, option in _numbered(options):
                    self._output(f"{n:>3}) {self._name(option)}")
                return self._read(_by_number(options), f"Which table? [1-{len(options)}] ")
            case Topic.EVENT:
                events = {str(self._event(option).number): option for option in options}
                return self._read(events, "Which event? Its number: ")
            case Topic.SHEET:
                for n, option in _numbered(options):
                    self._output(f"{n}) {self._side(option)}")
                return self._read(_by_number(options), f"Where? [1-{len(options)}] ")

    def tell(self, event: Event) -> None:
        match event:
            case Arrival(number=1):
                self._rules = None
                self._output("Home is box 1.")
            case Arrival(number=number, upkeep=upkeep):
                self._rules = None
                self._output(f"Box {number}.")
                if upkeep is Upkeep.ATE:
                    self._output(f"You eat 1 Food (Food {self.game.character.food}).")
                elif upkeep is Upkeep.STARVED:
                    self._output(f"No Food: you lose 1 Life (Life {self.game.character.life}).")
            case Rolled():
                self._show_rolled(event)
            case LeadRolled(face=face, ref=ref):
                self._output(f"  Rolled {face}: {self._name(ref)}")
            case Wandering(face=face, encounter=True):
                self._output(f"A Random Encounter! (1 in 6: rolled {face})")
            case Wandering(face=face):
                self._output(f"No encounter. (1 in 6: rolled {face})")
            case EventPlayed(event_id=event_id):
                played = self._event(event_id)
                self._output(f"Event #{played.number}, {played.name}: read it in {played.source}")
            case SheetAttached():
                self._output("A new sheet is attached.")
            case Ended(end=end):
                self._output(ENDINGS[end])

    # --- Reading ----------------------------------------------------------------------------

    def _read(self, keys: dict[str, object], prompt: str, rules: bool = False) -> object:
        """Ask until the player types one of the keys; `r` shows the last table's rules."""
        while True:
            try:
                line = self._input(prompt).strip().lower()
            except (EOFError, KeyboardInterrupt):
                raise Quit from None
            if line in keys:
                return keys[line]
            if rules and line == RULES_KEY and self._rules is not None:
                self._show_rules(self._rules)
                continue
            self._output(f"Choose one of {', '.join(keys) if len(keys) < 10 else _span(keys)}.")

    def _menu(self, options: Sequence[object], prompt: str) -> object:
        """One line of options: numbered tables and events, then lettered actions; `r` for
        the rules of the last table rolled in this box."""
        keys: dict[str, object] = {}
        numbered = (option for option in options if option not in KEYS)
        for n, option in enumerate(numbered, start=1):
            keys[str(n)] = option
        for option in options:
            if option in KEYS:
                keys[KEYS[option][0]] = option
        shown = [f"{key}) {self._label(option)}" for key, option in keys.items()]
        if self._rules is not None:
            shown.append(f"{RULES_KEY}) rules of the {self._rules.name}")
        self._output("  ".join(shown))
        return self._read(keys, prompt, rules=True)

    def _label(self, option: object) -> str:
        if option in KEYS:
            return KEYS[option][1]
        return self._name(str(option))

    # --- Book mode --------------------------------------------------------------------------

    def _show_rolled(self, rolled: Rolled) -> None:
        content = self.game.content
        results = ", then ".join(str(result) for result in rolled.results)
        if rolled.entry_id is None:
            source = content.catalogue[rolled.table_id]
            self._output(f"{source.name}: {results}")
            self._output(f"  Not copied yet: read entry {results} in {source.source}")
            return
        table = content.table(rolled.table_id)
        self._output(f"{table.name}: {results}")
        if table.text:
            self._rules = table
            if table.id not in self._seen:
                self._show_rules(table)
        entry = content.entry(rolled.entry_id)
        if entry.name:
            self._output(f"  {entry.name}")
        if entry.text:
            self._output(_indented(entry.text))
        for note in entry.notes:
            self._output(_indented(table.notes[note], "  Note: "))

    def _show_rules(self, table: Table) -> None:
        self._seen.add(table.id)
        self._output(_indented(table.text or "", "  Rules: "))

    def _name(self, id_: str) -> str:
        content = self.game.content
        if id_ in content.tables:
            return content.tables[id_].name or id_
        match content.catalogue.get(id_):
            case CatalogueTable(name=name):
                return name
            case CatalogueEvent(number=number, name=name):
                return f"event #{number}, {name}"
        return id_

    def _event(self, event_id: str) -> CatalogueEvent:
        event = self.game.content.catalogue[event_id]
        assert isinstance(event, CatalogueEvent)
        return event

    def _side(self, sheet: Position) -> str:
        """Where a new sheet goes, against a sheet already attached."""
        attached = self.game.campaign.map.sheets
        for other in sorted(sheet_neighbours(sheet) & attached):
            side = SIDES[(sheet.column - other.column, sheet.row - other.row)]
            return side if len(attached) == 1 else f"{side} sheet {tuple(other)}"
        return str(tuple(sheet))

    # --- Showing ----------------------------------------------------------------------------

    def _status(self) -> str:
        c = self.game.character
        return (
            f"Box {self.game.campaign.box_counter} · Life {c.life} · Sanity {c.sanity} · "
            f"Food {c.food} · XP {c.xp} · Clues {c.clues}"
        )

    def _map(self, options: Sequence[object] = ()) -> str:
        """The attached sheets (the first one before Home is chosen), one cell per box: an
        option's number, @ where the character stands, H for Home, the last number written in
        a visited box, a dot otherwise."""
        campaign = self.game.campaign
        sheets = campaign.map.sheets or {Position(0, 0)}
        columns = range(
            min(s.column for s in sheets) * SHEET_COLUMNS,
            (max(s.column for s in sheets) + 1) * SHEET_COLUMNS,
        )
        rows = range(
            min(s.row for s in sheets) * SHEET_ROWS, (max(s.row for s in sheets) + 1) * SHEET_ROWS
        )
        labels = {option: f"[{n}]" for n, option in _numbered(options)}
        lines = []
        for row in rows:
            cells = []
            for column in columns:
                box = Position(column, row)
                if box in labels:
                    cell = labels[box]
                elif box == campaign.position:
                    cell = "@"
                elif box == campaign.home:
                    cell = "H"
                elif box in campaign.map.boxes:
                    cell = str(campaign.map.boxes[box].numbers[-1])
                else:
                    cell = "."
                cells.append(cell.rjust(CELL))
            lines.append("".join(cells))
        return "\n".join(lines)


def _numbered(options: Sequence[object]):
    return enumerate(options, start=1)


def _by_number(options: Sequence[object]) -> dict[str, object]:
    return {str(n): option for n, option in _numbered(options)}


def _span(keys: dict[str, object]) -> str:
    return f"{next(iter(keys))} to {list(keys)[-1]}"


def _indented(text: str, first: str = "  ") -> str:
    lines = text.strip().splitlines()
    return "\n".join([first + lines[0], *("  " + line for line in lines[1:])])


# --- Starting a game ------------------------------------------------------------------------


def main(
    argv: Sequence[str] | None = None,
    *,
    input_fn: Callable[[str], str] = input,
    output_fn: Callable[[str], None] = print,
) -> int:
    parser = argparse.ArgumentParser(description="Play Alone Against Fear in the terminal.")
    parser.add_argument("--seed", type=int, help="dice seed (default: picked and logged)")
    parser.add_argument("--log-dir", default="logs", help="where the log file goes")
    args = parser.parse_args(argv)

    log_dir = Path(args.log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"{datetime.now():%Y%m%d-%H%M%S}.log"
    handler = logging.FileHandler(log_file, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    logger = logging.getLogger("alone_against_fear")
    level = logger.level
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    try:
        output_fn(f"Log: {log_file}")
        game = Game(dice=RandomDice(args.seed), content=load_content())
        play(game, TerminalInterface(game, input_fn, output_fn))
    finally:
        logger.removeHandler(handler)
        logger.setLevel(level)
        handler.close()
    return 0
