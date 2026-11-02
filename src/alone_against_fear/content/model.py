"""The rules text as the engine sees it: tables, entries, and the checks they must pass.

See docs/content.md. The text is data only: what an entry does is Python, keyed by ID.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterator, Mapping
from dataclasses import dataclass, field

from ..dice import DiceCode

KINDS = frozenset(
    {
        "table",
        "mission",
        "event",
        "weapon",
        "item",
        "skill",
        "arcane_skill",
        "injury",
        "mental_scar",
    }
)
"""First segment of every ID. A YAML batch adds the kinds it needs."""


class ContentError(Exception):
    """The YAML content is malformed and cannot be loaded."""


@dataclass(frozen=True)
class Roll:
    """The results an entry covers: one number or a range, as printed."""

    low: int
    high: int

    def __contains__(self, result: int) -> bool:
        return self.low <= result <= self.high

    @property
    def label(self) -> str:
        return str(self.low) if self.low == self.high else f"{self.low}-{self.high}"


type Count = str | int
"""A dice code in standard form ("2d6+3"), or a fixed number ("Salt (6 doses)")."""


@dataclass(frozen=True)
class Entry:
    id: str
    roll: Roll
    text: str | None = None
    name: str | None = None
    refs: tuple[str, ...] = ()
    """Tables and events the entry tells you to roll on or play."""
    notes: tuple[str, ...] = ()
    """Keys of the top table's notes that apply to this entry."""
    table: Table | None = None
    """A nested table: roll d6, then another d6."""
    item: str | None = None
    """The item the entry gives (`item.`); two entries may give the same one. A weapon the
    entry gives is in `refs`."""
    count: Count | Mapping[str, Count] | None = None
    """How many objects the entry gives: one count, or one per thing when it gives a
    choice."""
    uses: Count | None = None
    """How many times the single item it gives can be used (a First Aid Kit's points)."""

    def count_of(self, id_: str) -> Count | None:
        """How many of `id_` the entry gives: a dice code to roll, a number, or None."""
        if isinstance(self.count, Mapping):
            return self.count.get(id_)
        return self.count


@dataclass(frozen=True)
class Table:
    id: str
    dice: str
    """A dice code in standard form (see dice.DiceCode)."""
    entries: tuple[Entry, ...]
    name: str | None = None
    text: str | None = None
    """The table's own rules: when to roll it, its modifiers."""
    source: str | None = None
    """The readable Markdown copy, from the repository root."""
    notes: Mapping[str, str] = field(default_factory=dict)
    """Named passages that some entries point to."""

    def entry_for(self, result: int) -> Entry:
        for entry in self.entries:
            if result in entry.roll:
                return entry
        raise KeyError(f"{self.id}: no entry for {result}")

    def walk(self) -> Iterator[Entry]:
        """Every entry, nested ones included, in table order."""
        for entry in self.entries:
            yield entry
            if entry.table is not None:
                yield from entry.table.walk()

    def nested_tables(self) -> Iterator[Table]:
        for entry in self.entries:
            if entry.table is not None:
                yield entry.table
                yield from entry.table.nested_tables()


@dataclass(frozen=True)
class CatalogueTable:
    """A table of the book that is not copied yet: book mode points to its source."""

    id: str
    name: str
    dice: str
    source: str


@dataclass(frozen=True)
class CatalogueEvent:
    """A numbered event of the book that is not copied yet (R6): book mode points to its
    source and records it as played."""

    id: str
    number: int
    name: str
    source: str


@dataclass(frozen=True)
class Weapon:
    """A weapon of the weapon summary: its name and rules as printed. A heading that names
    two weapons ("Baseball bat or hammer") lists them as variants: each is a weapon of its
    own, with the heading's text, so the character holds the exact one."""

    id: str
    name: str
    text: str
    source: str
    variants: tuple[str, ...] = ()
    """The IDs of the weapons a heading names; none when it names one."""
    heading: str | None = None
    """For a variant: the ID of its heading."""
    extra: str | None = None
    """For a variant: a sentence of its own, already at the end of `text` (the hammer drives
    stakes, the baseball bat does not)."""


@dataclass(frozen=True)
class Gear:
    """Something a Skill gives when taken at creation (the Bow's bow and arrows)."""

    id: str
    count: Count | None = None
    uses: Count | None = None


@dataclass(frozen=True)
class Skill:
    """A Skill (`skill.`) or an Arcane Skill (`arcane_skill.`): its name, XP cost and rules
    as printed, the Expert line apart."""

    id: str
    name: str
    xp: int
    text: str
    source: str
    expert: str | None = None
    """The Expert line, without its label; None when there is no Expert level."""
    components: str | None = None
    """Arcane Skills only: the tools the ritual needs, as printed."""
    sacrifice: str | None = None
    """Arcane Skills only: what the ritual uses up, as printed."""
    starting_gear: tuple[Gear, ...] = ()
    """What the Skill gives when taken at creation, as its text says."""


@dataclass(frozen=True)
class Content:
    tables: Mapping[str, Table]
    catalogue: Mapping[str, CatalogueTable | CatalogueEvent]
    """Tables and events known but not copied yet."""
    entries: Mapping[str, Entry]
    weapons: Mapping[str, Weapon] = field(default_factory=dict)
    """The weapon summary, in the book's order: its headings."""
    variants: Mapping[str, Weapon] = field(default_factory=dict)
    """The weapons a heading names, when it names two."""
    items: Mapping[str, tuple[str, ...]] = field(default_factory=dict)
    """Every item, with the IDs of the entries that give it."""
    skills: Mapping[str, Skill] = field(default_factory=dict)
    """The Skills, in the book's order."""
    arcane_skills: Mapping[str, Skill] = field(default_factory=dict)
    """The Arcane Skills, in the book's order."""

    def table(self, id_: str) -> Table:
        return self.tables[id_]

    def entry(self, id_: str) -> Entry:
        return self.entries[id_]

    def weapon(self, id_: str) -> Weapon:
        """A heading of the weapon summary, or a variant."""
        return self.weapons[id_] if id_ in self.weapons else self.variants[id_]

    def skill(self, id_: str) -> Skill:
        """A Skill or an Arcane Skill."""
        return self.skills[id_] if id_ in self.skills else self.arcane_skills[id_]

    def events(self) -> list[CatalogueEvent]:
        """Every numbered event, in the book's order."""
        events = [item for item in self.catalogue.values() if isinstance(item, CatalogueEvent)]
        return sorted(events, key=lambda event: event.number)

    def __contains__(self, id_: str) -> bool:
        return (
            id_ in self.tables
            or id_ in self.catalogue
            or id_ in self.entries
            or id_ in self.weapons
            or id_ in self.variants
            or id_ in self.items
            or id_ in self.skills
            or id_ in self.arcane_skills
        )


def coverage_problems(table: Table) -> list[str]:
    """Every result of the table's dice has exactly one entry. Nested tables are not
    included: check each one."""
    results = DiceCode.parse(table.dice).results()
    problems = []
    counts: Counter[int] = Counter()
    for entry in table.entries:
        for end in sorted({entry.roll.low, entry.roll.high}):
            if end not in results:
                problems.append(f"{table.id}: {end} is not on {table.dice}")
        counts.update(result for result in results if result in entry.roll)
    for result in results:
        if counts[result] == 0:
            problems.append(f"{table.id}: no entry for {result}")
        elif counts[result] > 1:
            problems.append(f"{table.id}: {counts[result]} entries for {result}")
    return problems


def reference_problems(content: Content) -> list[str]:
    """Every reference points to a table, an entry, or a catalogued table or event; every
    Skill's starting gear exists."""
    problems = [
        f"{entry.id}: no such ID {ref}"
        for table in content.tables.values()
        for entry in table.walk()
        for ref in entry.refs
        if ref not in content
    ]
    skills = [*content.skills.values(), *content.arcane_skills.values()]
    problems += [
        f"{skill.id}: no such ID {gear.id}"
        for skill in skills
        for gear in skill.starting_gear
        if gear.id not in content
    ]
    return problems


def note_problems(content: Content) -> list[str]:
    """Every note an entry points to exists in its top table."""
    return [
        f"{entry.id}: no note {note} in {table.id}"
        for table in content.tables.values()
        for entry in table.walk()
        for note in entry.notes
        if note not in table.notes
    ]
