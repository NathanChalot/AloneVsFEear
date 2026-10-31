"""Load the rules text from the YAML files of this package (design/content.md)."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

from .model import TABLE_DICE, CatalogueTable, Content, ContentError, Entry, Roll, Table

CONTENT_DIR = Path(__file__).parent
CATALOGUE = "catalogue.yaml"

_TABLE_KEYS = {"id", "name", "dice", "text", "source", "notes", "entries"}
_NESTED_KEYS = {"dice", "entries"}
_ENTRY_KEYS = {"roll", "id", "name", "text", "refs", "notes", "table"}
_CATALOGUE_KEYS = {"id", "name", "dice", "source"}
_RANGE = re.compile(r"(\d+)-(\d+)")


def load_content(root: Path | str | None = None) -> Content:
    """Read the catalogue and every table file under `root` (this package by default)."""
    root = Path(root) if root is not None else CONTENT_DIR
    seen: dict[str, Path] = {}

    def register(id_: str, where: Path) -> None:
        if id_ in seen:
            raise ContentError(f"{id_} is defined twice: in {seen[id_]} and in {where}")
        seen[id_] = where

    catalogue = {}
    catalogue_path = root / CATALOGUE
    for raw in _read(catalogue_path) or []:
        table = _catalogue_table(raw, catalogue_path)
        register(table.id, catalogue_path)
        catalogue[table.id] = table

    tables, entries = {}, {}
    for path in sorted(root.rglob("*.yaml")):
        if path == catalogue_path:
            continue
        table = _table(_read(path), path)
        register(table.id, path)
        tables[table.id] = table
        for entry in table.walk():
            register(entry.id, path)
            entries[entry.id] = entry

    return Content(tables=tables, catalogue=catalogue, entries=entries)


def _read(path: Path) -> Any:
    with path.open(encoding="utf-8") as file:
        return yaml.safe_load(file)


def _check_keys(raw: Any, allowed: set[str], required: set[str], what: str) -> None:
    if not isinstance(raw, dict):
        raise ContentError(f"{what}: expected a mapping, got {raw!r}")
    if unknown := raw.keys() - allowed:
        raise ContentError(f"{what}: unknown keys {sorted(unknown)}")
    if missing := required - raw.keys():
        raise ContentError(f"{what}: missing keys {sorted(missing)}")


def _dice(raw: dict, what: str) -> str:
    dice = raw["dice"]
    if dice not in TABLE_DICE:
        raise ContentError(f"{what}: unknown dice {dice!r}")
    return dice


def _catalogue_table(raw: Any, path: Path) -> CatalogueTable:
    what = f"{path}: {raw.get('id', raw) if isinstance(raw, dict) else raw}"
    _check_keys(raw, _CATALOGUE_KEYS, _CATALOGUE_KEYS, what)
    return CatalogueTable(
        id=raw["id"], name=raw["name"], dice=_dice(raw, what), source=raw["source"]
    )


def _table(raw: Any, path: Path, id_: str | None = None) -> Table:
    """A table file, or a nested table (given the ID of the entry that holds it)."""
    nested = id_ is not None
    what = f"{path}: {id_ or (raw.get('id', '?') if isinstance(raw, dict) else '?')}"
    if nested:
        _check_keys(raw, _NESTED_KEYS, _NESTED_KEYS, what)
    else:
        _check_keys(raw, _TABLE_KEYS, {"id", "name", "dice", "source", "entries"}, what)
        id_ = raw["id"]
    return Table(
        id=id_,
        dice=_dice(raw, what),
        entries=tuple(_entry(e, id_, path) for e in raw["entries"] or []),
        name=raw.get("name"),
        text=raw.get("text"),
        source=raw.get("source"),
        notes=dict(raw.get("notes") or {}),
    )


def _entry(raw: Any, table_id: str, path: Path) -> Entry:
    what = f"{path}: entry of {table_id}"
    _check_keys(raw, _ENTRY_KEYS, {"roll"}, what)
    roll = _roll(raw["roll"], what)
    id_ = raw.get("id") or f"{table_id}.{roll.label}"
    return Entry(
        id=id_,
        roll=roll,
        text=raw.get("text"),
        name=raw.get("name"),
        refs=_strings(raw.get("refs"), f"{what} refs"),
        notes=_strings(raw.get("notes"), f"{what} notes"),
        table=_table(raw["table"], path, id_) if "table" in raw else None,
    )


def _roll(raw: Any, what: str) -> Roll:
    if isinstance(raw, int) and not isinstance(raw, bool):
        return Roll(raw, raw)
    if isinstance(raw, str) and (match := _RANGE.fullmatch(raw)):
        low, high = int(match[1]), int(match[2])
        if low < high:
            return Roll(low, high)
    raise ContentError(f"{what}: bad roll {raw!r}, expected a number or a range like 2-5")


def _strings(raw: Any, what: str) -> tuple[str, ...]:
    if raw is None:
        return ()
    if not isinstance(raw, list) or not all(isinstance(item, str) for item in raw):
        raise ContentError(f"{what}: expected a list of IDs, got {raw!r}")
    return tuple(raw)
