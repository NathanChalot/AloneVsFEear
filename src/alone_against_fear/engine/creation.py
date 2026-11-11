"""Creating a character (E6): `1_1_main_rules.md`, Your Character; design/character.md.

The player names the character and spends 3 points: on Life and Sanity (8 each), or traded for
1 extra Skill or 1 extra roll on the Random Weapon, Random Objects or Useful Stuff table. Then 2
Skills (no Arcane, no Expert) and the gear a Skill gives at creation (Bow, Faith), a random
weapon and a knife or stick, 1 Random Object and 1 Useful Stuff, d6 Food. The rulings
(design/rulings.md): the knife or stick, and the bat or hammer of Random Weapon 1, are the
player's choice; Faith's holy symbol is the Religious symbol; a duplicate is anything already
given at creation (the same item or weapon, or the same entry for what is neither), and its
table is rolled again.

What an entry or a Skill gives is read from the content (`item`, the weapons of `refs`,
`count`, `uses`, `starting_gear`); the entries that give something else are behaviour, keyed
here by entry ID: the samurai sword rolled authentic or replica, Food points, and the books
(book mode until E18).

A sample pregenerated character (T1) is made from its sheet instead, with no question: the
drills start from one.
"""

from __future__ import annotations

from enum import StrEnum

from ..content import Count, Entry
from ..dice import DiceCode
from . import book_mode
from .game import Game
from .leads import DieRoll
from .protocol import (
    Changed,
    Choose,
    Duplicate,
    Interface,
    ItemTaken,
    LeadRolled,
    Number,
    Step,
    StepStarted,
    Text,
    Topic,
    ask,
)
from .state import Character, Item, Stat

BASE = 8
"""Life and Sanity before the points."""
POINTS = 3
STARTING_SKILLS = 2
RANDOM_WEAPON = "table.random_weapon"
RANDOM_OBJECTS = "table.random_objects"
USEFUL_STUFF = "table.useful_stuff"
FREE_WEAPONS = ("weapon.knife", "weapon.stick")
"""The knife or stick every character starts with (design/rulings.md)."""
FOOD = DiceCode.parse("d6")
D6 = DiceCode.parse("d6")

PICKED_BY_DIE = {
    "table.random_objects.54": DieRoll(
        ((2, "weapon.samurai_sword_authentic"), (6, "weapon.samurai_sword_cheap_replica"))
    ),
}
"""Entries that roll a die to pick the weapon they give."""
FOOD_POINTS = frozenset({"table.random_objects.33"})
"""Entries that give Food points, their count."""


class Points(StrEnum):
    """What the 3 creation points buy."""

    STATS = "stats"
    """Life and Sanity: the player splits the 3 points."""
    SKILL = "skill"
    """1 more Skill."""
    WEAPON = "weapon"
    """1 more roll on the Random Weapon table."""
    OBJECT = "object"
    """1 more roll on the Random Objects table."""
    USEFUL = "useful"
    """1 more roll on the Useful Stuff table."""


STEPS = {RANDOM_WEAPON: Step.WEAPONS, RANDOM_OBJECTS: Step.GEAR}
"""The tables that start a step of creation."""

EXTRA_ROLL = {
    RANDOM_WEAPON: Points.WEAPON,
    RANDOM_OBJECTS: Points.OBJECT,
    USEFUL_STUFF: Points.USEFUL,
}


def create(game: Game, interface: Interface) -> Character:
    """Walk the player through creation; the new character continues the campaign."""
    interface.tell(StepStarted(Step.NAME))
    name = ask(interface, Text(Topic.NAME))
    interface.tell(StepStarted(Step.POINTS))
    points = ask(interface, Choose(Topic.POINTS, tuple(Points)))
    life = sanity = BASE
    if points is Points.STATS:
        on_life = ask(interface, Number(Topic.LIFE_POINTS, 0, POINTS))
        life, sanity = life + on_life, sanity + POINTS - on_life
    interface.tell(StepStarted(Step.SKILLS))
    skills: list[str] = []
    for _ in range(STARTING_SKILLS + (points is Points.SKILL)):
        options = tuple(skill for skill in game.content.skills if skill not in skills)
        skills.append(ask(interface, Choose(Topic.SKILL, options)))
    character = game.create_character(life, sanity, food=0, name=name, skills=skills)

    giving = _Giving(game, interface)
    for skill_id in skills:
        for gear in game.content.skill(skill_id).starting_gear:
            count, uses = giving.amount(gear.count), giving.amount(gear.uses)
            giving.take(Item(gear.id, skill_id, count, uses))
    for table_id in (RANDOM_WEAPON, RANDOM_OBJECTS, USEFUL_STUFF):
        if table_id in STEPS:
            interface.tell(StepStarted(STEPS[table_id]))
        giving.roll(table_id)
        if points is EXTRA_ROLL[table_id]:
            giving.roll(table_id)
        if table_id == RANDOM_WEAPON:
            giving.take(Item(ask(interface, Choose(Topic.WEAPON, FREE_WEAPONS))))
    giving.gain_food(FOOD.roll(game.dice).total)
    return character


def pregenerated(game: Game, pregenerated_id: str) -> Character:
    """Make a sample pregenerated character as its sheet gives it; they continue the campaign.
    Their printed Life and Sanity are the base of the max: neither sheet has a Skill that
    raises them."""
    sheet = game.content.pregenerated[pregenerated_id]
    items = [Item(gear.id, count=gear.count, uses=gear.uses) for gear in sheet.gear]
    return game.create_character(
        sheet.life, sheet.sanity, sheet.food, items, name=sheet.name, skills=sheet.skills
    )


class _Giving:
    """What the creation rolls give, and what was given already."""

    def __init__(self, game: Game, interface: Interface) -> None:
        self.game = game
        self.interface = interface
        self.reached: set[str] = set()
        """Entries that gave neither an item nor a weapon (Food, a book)."""

    def roll(self, table_id: str) -> None:
        """Roll the table until its entry gives something new."""
        while True:
            rolled = self.game.roll_table(table_id)
            self.interface.tell(rolled)
            entry = self.game.content.entry(rolled.entry_id)
            if self._give(entry, rolled):
                return
            self.interface.tell(Duplicate(entry.id))

    def take(self, item: Item) -> None:
        self.game.add_item(item)
        self.interface.tell(ItemTaken(item))

    def gain_food(self, amount: int) -> None:
        before = self.game.character.food
        value = self.game.gain(Stat.FOOD, amount)
        self.interface.tell(Changed(Stat.FOOD, value - before, value))

    def _give(self, entry: Entry, rolled) -> bool:
        """Give what the entry gives; False when it is a duplicate."""
        held = {item.id for item in self.game.character.items}
        if entry.item is not None:
            if entry.item in held:
                return False
            count, uses = entry.count_of(entry.item), entry.uses
            self.take(Item(entry.item, entry.id, self.amount(count), self.amount(uses)))
            return True
        weapons = tuple(ref for ref in entry.refs if ref.startswith("weapon."))
        if weapons:
            weapon = self._weapon(entry, weapons, held)
            if weapon is None:
                return False
            self.take(Item(weapon, entry.id, self.amount(entry.count_of(weapon))))
            return True
        if entry.id in self.reached:
            return False
        self.reached.add(entry.id)
        if entry.id in FOOD_POINTS:
            self.gain_food(self.amount(entry.count))
        else:  # a book: the player reads it in book mode
            book_mode.lead_on(self.game, self.interface, rolled)
        return True

    def _weapon(self, entry: Entry, weapons: tuple[str, ...], held: set[str]) -> str | None:
        """The weapon the entry gives: rolled, the only one, or the player's choice among
        those not held yet. None when all are held."""
        if (die := PICKED_BY_DIE.get(entry.id)) is not None:
            face = D6.roll(self.game.dice).total
            weapon = die.ref_for(face)
            self.interface.tell(LeadRolled(entry.id, face, weapon))
            return None if weapon in held else weapon
        options = tuple(weapon for weapon in weapons if weapon not in held)
        if len(options) <= 1:
            return options[0] if options else None
        return ask(self.interface, Choose(Topic.WEAPON, options))

    def amount(self, count: Count | None) -> int | None:
        """A count or uses: rolled when it is dice."""
        if count is None or isinstance(count, int):
            return count
        return DiceCode.parse(count).roll(self.game.dice).total
