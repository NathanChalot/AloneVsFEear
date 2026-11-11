"""Feedback written while playing (T1): a line starting with # at any prompt of the terminal.

Each note is appended to a Markdown file (`feedback/feedback.md` by default, kept in the
repository) with what is needed to find the moment again: the date, the drill, the dice seed,
the box number, the character, the question on screen and the run's log file. It is also
logged. Notes are triaged at the next consistency review or playtest (WorkingWithClaude.md,
Playtesting).
"""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

from ..engine import Game

PREFIX = "#"
"""A line starting with this is a feedback note, not an answer."""
HEADER = (
    "# Feedback\n\n"
    "Notes written while playing (`#` at any prompt), newest last. Each is triaged at the next "
    "consistency review or playtest ([Working with Claude](../WorkingWithClaude.md#playtesting)).\n"
)

log = logging.getLogger(__name__)


class FeedbackLog:
    """Where the notes of one run go, and what identifies the run."""

    def __init__(
        self, path: Path | str, seed: int | None, drill: str | None, log_file: Path | str
    ) -> None:
        self.path = Path(path)
        self.seed = seed
        self.drill = drill
        self.log_file = log_file

    def write(self, game: Game, prompt: str, text: str) -> None:
        """Append a note, written while `prompt` was asked."""
        box = game.campaign.box_counter
        character = game.campaign.character
        heading = [f"{datetime.now():%Y-%m-%d %H:%M}"]
        if self.drill is not None:
            heading.append(f"drill {self.drill}")
        heading += [f"seed {self.seed}", f"box {box}"]
        entry = (
            f"\n## {' · '.join(heading)}\n\n"
            f"- Character: {character.name or 'unnamed' if character else 'none yet'}\n"
            f"- Asked: {prompt.strip()}\n"
            f"- Log: {self.log_file}\n\n"
            f"{text}\n"
        )
        self.path.parent.mkdir(parents=True, exist_ok=True)
        new = not self.path.exists()
        with self.path.open("a", encoding="utf-8") as file:
            if new:
                file.write(HEADER)
            file.write(entry)
        log.info("feedback at box %d: %s", box, text)
