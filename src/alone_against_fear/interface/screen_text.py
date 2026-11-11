"""The terminal's own wording (T2): headings, explanations and prompts, kept in YAML.

Each file of `screens/` holds one screen's text; a key is the file name, then the nested keys,
joined by dots: `creation.points.heading`. A text may name fields to fill in, as Python's
`str.format` does: `"Skill {n} of {count}? "`. The rules text the engine relies on stays in
`content/`; this is what one interface says around it, and may repeat the rules' words.
"""

from __future__ import annotations

from collections.abc import Mapping
from functools import cache
from pathlib import Path

import yaml

SCREENS = Path(__file__).parent / "screens"


class ScreenTextError(Exception):
    """A screen text is missing, malformed, or lacks a field to fill in."""


class ScreenText:
    """The screen texts by key; remembers the keys used, so a test can find unused ones."""

    def __init__(self, texts: Mapping[str, str]) -> None:
        self._texts = dict(texts)
        self.used: set[str] = set()

    @property
    def keys(self) -> frozenset[str]:
        return frozenset(self._texts)

    def __call__(self, key: str, **fields: object) -> str:
        """The text of the key, its fields filled in."""
        try:
            text = self._texts[key]
        except KeyError:
            raise ScreenTextError(f"no screen text {key!r}") from None
        try:
            filled = text.format(**fields)
        except (KeyError, IndexError) as error:
            raise ScreenTextError(f"screen text {key!r} needs the field {error}") from None
        self.used.add(key)
        return filled


@cache
def _load(folder: Path) -> dict[str, str]:
    texts: dict[str, str] = {}
    for path in sorted(folder.glob("*.yaml")):
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            raise ScreenTextError(f"{path}: a mapping of keys to texts")
        texts.update(_flatten(raw, path.stem, path))
    return texts


def _flatten(raw: Mapping, prefix: str, path: Path) -> dict[str, str]:
    texts: dict[str, str] = {}
    for key, value in raw.items():
        full = f"{prefix}.{key}"
        if isinstance(value, dict):
            texts.update(_flatten(value, full, path))
        elif isinstance(value, str):
            texts[full] = value
        else:
            raise ScreenTextError(f"{path}: {full} is not a text")
    return texts


def load_screen_text(folder: Path = SCREENS) -> ScreenText:
    """Every screen's text, from the YAML files of the folder."""
    return ScreenText(_load(folder))
