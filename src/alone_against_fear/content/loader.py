"""Load the rules text from the YAML files of this package (docs/content.md)."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

from ..dice import DiceCode, DiceError
from .model import (
    CatalogueEvent,
    CatalogueTable,
    Content,
    ContentError,
    Entry,
    Roll,
    Skill,
    Table,
    Weapon,
)

CONTENT_DIR = Path(__file__).parent
CATALOGUE = "catalogue.yaml"

_TABLE_KEYS = {"id", "name", "dice", "text", "source", "notes", "entries"}
_NESTED_KEYS = {"dice", "entries"}
_ENTRY_KEYS = {"roll", "id", "name", "text", "refs", "notes", "table"}
_CATALOGUE_KEYS = {"id", "name", "dice", "source"}
_CATALOGUE_EVENT_KEYS = {"id", "name", "source"}
_WEAPONS_KEYS = {"name", "source", "weapons"}
_WEAPON_KEYS = {"id", "name", "text"}
_SKILL_KEYS = {"id", "name", "xp", "text", "expert"}
_ARCANE_KEYS = _SKILL_KEYS | {"components", "sacrifice"}
_SKILL_LISTS = {
    # key of the list: (ID prefix, what to call it, keys of an item)
    "skills": ("skill.", "a Skill", _SKILL_KEYS),
    "arcane_skills": ("arcane_skill.", "an Arcane Skill", _ARCANE_KEYS),
}
_RANGE = re.compile(r"(\d+)-(\d+)")
_EVENT_ID = re.compile(r"event\.(\d+)")


def load_content(root: Path | str | None = None) -> Content:
    """Read the catalogue, every table file, weapon list and Skill list under `root` (this
    package by default)."""
    root = Path(root) if root is not None else CONTENT_DIR
    seen: dict[str, Path] = {}

    def register(id_: str, where: Path) -> None:
        if id_ in seen:
            raise ContentError(f"{id_} is defined twice: in {seen[id_]} and in {where}")
        seen[id_] = where

    catalogue = {}
    catalogue_path = root / CATALOGUE
    for raw in _read(catalogue_path) or []:
        item = _catalogued(raw, catalogue_path)
        register(item.id, catalogue_path)
        catalogue[item.id] = item

    tables, entries, weapons = {}, {}, {}
    skills: dict[str, dict[str, Skill]] = {key: {} for key in _SKILL_LISTS}
    for path in sorted(root.rglob("*.yaml")):
        if path == catalogue_path:
            continue
        raw = _read(path)
        if isinstance(raw, dict) and "weapons" in raw:
            for weapon in _weapons(raw, path):
                register(weapon.id, path)
                weapons[weapon.id] = weapon
            continue
        if isinstance(raw, dict) and (key := next((k for k in _SKILL_LISTS if k in raw), None)):
            for skill in _skills(raw, path, key):
                register(skill.id, path)
                skills[key][skill.id] = skill
            continue
        table = _table(raw, path)
        register(table.id, path)
        tables[table.id] = table
        for entry in table.walk():
            register(entry.id, path)
            entries[entry.id] = entry

    return Content(
        tables=tables,
        catalogue=catalogue,
        entries=entries,
        weapons=weapons,
        skills=skills["skills"],
        arcane_skills=skills["arcane_skills"],
    )


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
    try:
        return str(DiceCode.parse(str(raw["dice"])))
    except DiceError as error:
        raise ContentError(f"{what}: {error}") from error


def _catalogued(raw: Any, path: Path) -> CatalogueTable | CatalogueEvent:
    """A catalogued table, or a numbered event (its ID starts with `event.`)."""
    what = f"{path}: {raw.get('id', raw) if isinstance(raw, dict) else raw}"
    if isinstance(raw, dict) and str(raw.get("id", "")).startswith("event."):
        _check_keys(raw, _CATALOGUE_EVENT_KEYS, _CATALOGUE_EVENT_KEYS, what)
        if not (match := _EVENT_ID.fullmatch(raw["id"])):
            raise ContentError(f"{what}: an event ID is event. and its number")
        return CatalogueEvent(
            id=raw["id"], number=int(match[1]), name=raw["name"], source=raw["source"]
        )
    _check_keys(raw, _CATALOGUE_KEYS, _CATALOGUE_KEYS, what)
    return CatalogueTable(
        id=raw["id"], name=raw["name"], dice=_dice(raw, what), source=raw["source"]
    )


def _weapons(raw: dict, path: Path) -> list[Weapon]:
    """A list of weapons with no dice (the weapon summary): each its ID, name and text."""
    _check_keys(raw, _WEAPONS_KEYS, _WEAPONS_KEYS, str(path))
    weapons = []
    for item in raw["weapons"] or []:
        what = f"{path}: {item.get('id', '?') if isinstance(item, dict) else item}"
        _check_keys(item, _WEAPON_KEYS, _WEAPON_KEYS, what)
        if not str(item["id"]).startswith("weapon."):
            raise ContentError(f"{what}: a weapon ID starts with weapon.")
        weapons.append(Weapon(item["id"], item["name"], item["text"], raw["source"]))
    return weapons


def _skills(raw: dict, path: Path, key: str) -> list[Skill]:
    """A list of Skills or of Arcane Skills, with no dice: each its ID, name, XP cost and
    text, the Expert line apart."""
    prefix, called, allowed = _SKILL_LISTS[key]
    _check_keys(raw, {"name", "source", key}, {"name", "source", key}, str(path))
    skills = []
    for item in raw[key] or []:
        what = f"{path}: {item.get('id', '?') if isinstance(item, dict) else item}"
        _check_keys(item, allowed, {"id", "name", "xp", "text"}, what)
        if not str(item["id"]).startswith(prefix):
            raise ContentError(f"{what}: {called} ID starts with {prefix}")
        xp = item["xp"]
        if not isinstance(xp, int) or isinstance(xp, bool) or xp < 1:
            raise ContentError(f"{what}: the XP cost is a whole number above 0, got {xp!r}")
        skills.append(
            Skill(
                id=item["id"],
                name=item["name"],
                xp=xp,
                text=item["text"],
                source=raw["source"],
                expert=item.get("expert"),
                components=item.get("components"),
                sacrifice=item.get("sacrifice"),
            )
        )
    return skills


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
