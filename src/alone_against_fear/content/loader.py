"""Load the rules text from the YAML files of this package (docs/content.md)."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

from ..dice import DiceCode, DiceError
from ..effect_targets import Parameter, RollType, Tag
from .model import (
    CatalogueEvent,
    CatalogueTable,
    Content,
    ContentError,
    Count,
    Effect,
    Entry,
    Gear,
    Roll,
    Skill,
    Table,
    Weapon,
)

CONTENT_DIR = Path(__file__).parent
CATALOGUE = "catalogue.yaml"

_TABLE_KEYS = {"id", "name", "dice", "text", "source", "notes", "entries"}
_NESTED_KEYS = {"dice", "entries"}
_ENTRY_KEYS = {
    "roll",
    "id",
    "name",
    "text",
    "refs",
    "notes",
    "table",
    "item",
    "count",
    "uses",
    "effects",
}
_CATALOGUE_KEYS = {"id", "name", "dice", "source"}
_CATALOGUE_EVENT_KEYS = {"id", "name", "source"}
_WEAPONS_KEYS = {"name", "source", "weapons"}
_WEAPON_KEYS = {"id", "name", "text", "variants"}
_VARIANT_KEYS = {"id", "name", "extra"}
_SKILL_KEYS = {"id", "name", "xp", "text", "expert", "starting_gear", "effects"}
_TARGET_KEYS = {"roll", "tags", "parameter", "group"}
_EFFECT_KEYS = _TARGET_KEYS | {"basic", "expert"}
_ENTRY_EFFECT_KEYS = _TARGET_KEYS | {"amount"}
_GEAR_KEYS = {"id", "count", "uses"}
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

    tables, entries, weapons, variants = {}, {}, {}, {}
    items: dict[str, list[str]] = {}
    skills: dict[str, dict[str, Skill]] = {key: {} for key in _SKILL_LISTS}
    for path in sorted(root.rglob("*.yaml")):
        if path == catalogue_path:
            continue
        raw = _read(path)
        if isinstance(raw, dict) and "weapons" in raw:
            for weapon in _weapons(raw, path):
                register(weapon.id, path)
                (weapons if weapon.heading is None else variants)[weapon.id] = weapon
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
            if entry.item is not None:
                items.setdefault(entry.item, []).append(entry.id)
    for item in items:
        if item in seen:
            raise ContentError(f"{item} is an item and is defined in {seen[item]}")

    return Content(
        tables=tables,
        catalogue=catalogue,
        entries=entries,
        weapons=weapons,
        variants=variants,
        items={item: tuple(given) for item, given in items.items()},
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
    """A list of weapons with no dice (the weapon summary): each its ID, name and text, and
    the variants of a heading that names two weapons, each just after its heading."""
    _check_keys(raw, _WEAPONS_KEYS, _WEAPONS_KEYS, str(path))
    weapons = []
    for item in raw["weapons"] or []:
        what = f"{path}: {item.get('id', '?') if isinstance(item, dict) else item}"
        _check_keys(item, _WEAPON_KEYS, {"id", "name", "text"}, what)
        _check_weapon_id(item["id"], what)
        named = []
        for variant in item.get("variants") or []:
            named_what = (
                f"{path}: {variant.get('id', '?') if isinstance(variant, dict) else variant}"
            )
            _check_keys(variant, _VARIANT_KEYS, {"id", "name"}, named_what)
            _check_weapon_id(variant["id"], named_what)
            extra = variant.get("extra")
            text = item["text"] if extra is None else f"{item['text']} {extra}"
            named.append(
                Weapon(
                    variant["id"],
                    variant["name"],
                    text,
                    raw["source"],
                    heading=item["id"],
                    extra=extra,
                )
            )
        variants = tuple(variant.id for variant in named)
        weapons += [Weapon(item["id"], item["name"], item["text"], raw["source"], variants), *named]
    return weapons


def _check_weapon_id(id_: Any, what: str) -> None:
    if not str(id_).startswith("weapon."):
        raise ContentError(f"{what}: a weapon ID starts with weapon.")


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
                starting_gear=tuple(_gear(gear, what) for gear in item.get("starting_gear") or []),
                effects=tuple(
                    _effect(effect, what, "expert" in item) for effect in item.get("effects") or []
                ),
            )
        )
    return skills


def _entry_effect(raw: Any, what: str) -> Effect:
    """An entry's effect (an Injury, a Mental Scar, E8): a target and a single amount, read
    as a Basic amount with no Expert level."""
    _check_keys(raw, _ENTRY_EFFECT_KEYS, {"amount"}, f"{what} effect")
    return _effect(
        {**{k: v for k, v in raw.items() if k != "amount"}, "basic": raw["amount"]},
        what,
        has_expert=False,
    )


def _effect(raw: Any, what: str, has_expert: bool) -> Effect:
    """A Skill's effect: a roll (type, tags, group) or a parameter, and its amounts. Every
    name is checked against `effect_targets`, so a misspelt one fails here."""
    what = f"{what} effect"
    _check_keys(raw, _EFFECT_KEYS, {"basic"}, what)
    if ("roll" in raw) == ("parameter" in raw):
        raise ContentError(f"{what}: an effect changes a roll or a parameter, got {raw}")
    if "roll" not in raw:
        for key in ("tags", "group"):
            if key in raw:
                raise ContentError(
                    f"{what}: {'tags need' if key == 'tags' else 'a group needs'} a roll"
                )
    if has_expert != ("expert" in raw):
        if has_expert:
            raise ContentError(
                f"{what}: the Skill has an Expert line: its effects need an expert amount"
            )
        raise ContentError(
            f"{what}: the Skill has no Expert line: its effects have no expert amount"
        )
    for key in ("basic", "expert"):
        if key in raw and (not isinstance(raw[key], int) or isinstance(raw[key], bool)):
            raise ContentError(f"{what}: an amount is a whole number, got {raw[key]!r}")
    return Effect(
        basic=raw["basic"],
        expert=raw.get("expert"),
        roll=None if "roll" not in raw else _named(RollType, raw["roll"], "roll type", what),
        tags=frozenset(_named(Tag, tag, "tag", what) for tag in raw.get("tags") or []),
        parameter=(
            None
            if "parameter" not in raw
            else _named(Parameter, raw["parameter"], "parameter", what)
        ),
        group=raw.get("group"),
    )


def _named[E: (RollType, Tag, Parameter)](kind: type[E], raw: Any, called: str, what: str) -> E:
    try:
        return kind(raw)
    except ValueError:
        raise ContentError(f"{what}: unknown {called} {raw!r}") from None


def _gear(raw: Any, what: str) -> Gear:
    _check_keys(raw, _GEAR_KEYS, {"id"}, f"{what} starting gear")
    count, uses = raw.get("count"), raw.get("uses")
    return Gear(
        id=raw["id"],
        count=None if count is None else _count(count, what),
        uses=None if uses is None else _count(uses, what, "uses are"),
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
    item = raw.get("item")
    if item is not None and not str(item).startswith("item."):
        raise ContentError(f"{what}: an item ID starts with item., got {item!r}")
    refs = _strings(raw.get("refs"), f"{what} refs")
    return Entry(
        id=id_,
        roll=roll,
        text=raw.get("text"),
        name=raw.get("name"),
        refs=refs,
        notes=_strings(raw.get("notes"), f"{what} notes"),
        table=_table(raw["table"], path, id_) if "table" in raw else None,
        item=item,
        count=_counts(raw.get("count"), {*refs, item}, what),
        uses=_uses(raw.get("uses"), item, what),
        effects=tuple(_entry_effect(effect, what) for effect in raw.get("effects") or []),
    )


def _uses(raw: Any, item: str | None, what: str) -> Count | None:
    if raw is None:
        return None
    if item is None:
        raise ContentError(f"{what}: uses need an item")
    return _count(raw, what, "uses are")


def _counts(raw: Any, given: set[str | None], what: str) -> Count | dict[str, Count] | None:
    """One count, or one per thing the entry gives (a ref or its item)."""
    if raw is None:
        return None
    if not isinstance(raw, dict):
        return _count(raw, what)
    for id_ in raw:
        if id_ not in given:
            raise ContentError(f"{what}: a count for {id_}, which the entry does not give")
    return {id_: _count(count, what) for id_, count in raw.items()}


def _count(raw: Any, what: str, called: str = "a count is") -> Count:
    if isinstance(raw, int) and not isinstance(raw, bool) and raw > 0:
        return raw
    try:
        return str(DiceCode.parse(str(raw)))
    except DiceError as error:
        raise ContentError(f"{what}: {called} a dice code or a number, got {raw!r}") from error


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
