"""The terminal interface (E4): a minimal way to play.

It shows the character, the map and each request with numbered options, reads the player's
choice and checks it before answering, and narrates what the engine tells it. It reads the
game state to show it and changes it only through its answers. End of input (Ctrl-D) or Ctrl-C
quits. `main` sets up a game, with the log written to a file.
"""

from __future__ import annotations

import argparse
import logging
from collections.abc import Callable, Sequence
from datetime import datetime
from pathlib import Path

from ..content import load_content
from ..dice import RandomDice
from ..engine import Arrival, Game, Position, Upkeep
from ..engine.loop import play
from ..engine.protocol import End, Ended, Event, Quit, Request, Topic
from ..engine.town import SHEET_COLUMNS, SHEET_ROWS

CELL = 5
"""Width of a box on the map: room for "[30]" or a box number in the thousands."""

ENDINGS = {
    End.DEAD: "You are dead. The game is over.",
    End.INSANE: "You have gone insane. The game is over.",
    End.QUIT: "You quit the game.",
}


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

    # --- The protocol --------------------------------------------------------------------

    def ask(self, request: Request) -> object:
        options = request.options
        match request.topic:
            case Topic.ACTION:
                self._output("")
                self._output(self._status())
                self._output("  ".join(f"{n}) {option}" for n, option in _numbered(options)))
                prompt = "What do you do? "
            case Topic.HOME | Topic.MOVE:
                self._output(self._map(options))
                what = "Home" if request.topic is Topic.HOME else "Move to"
                prompt = f"{what}: choose a box [1-{len(options)}] "
        return options[self._read_choice(prompt, len(options)) - 1]

    def tell(self, event: Event) -> None:
        match event:
            case Arrival(number=1):
                self._output("Home is box 1.")
            case Arrival(number=number, upkeep=upkeep):
                self._output(f"Box {number}.")
                if upkeep is Upkeep.ATE:
                    self._output(f"You eat 1 Food (Food {self.game.character.food}).")
                elif upkeep is Upkeep.STARVED:
                    self._output(f"No Food: you lose 1 Life (Life {self.game.character.life}).")
            case Ended(end=end):
                self._output(ENDINGS[end])

    # --- Reading ----------------------------------------------------------------------------

    def _read_choice(self, prompt: str, count: int) -> int:
        while True:
            try:
                line = self._input(prompt).strip()
            except (EOFError, KeyboardInterrupt):
                raise Quit from None
            if line.isdigit() and 1 <= int(line) <= count:
                return int(line)
            self._output(f"Choose one of 1 to {count}.")

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
