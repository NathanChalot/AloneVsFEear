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

Manual actions (E5b): with an entry the engine cannot read, the player applies its text first
(`g` gain, `l` lose, `v` roll vs L, `w` write a note, `x` remove one, `h` mark a Safe House),
typing the numbers it gives; Enter alone is no modifier. The free actions add Search (`s`) and
apply an effect (`a`, back with `b`); attaching a sheet moved to `n`. The notes are shown under
the status line, and above a modifier to type.

Creation and XP (E6): the 3 points have letters (`l` Life and Sanity, `k` a Skill, `w`, `o`,
`u` an extra roll); Skills and weapons are numbered, with their text. The status line names the
character and shows Life and Sanity against their max, with the Skills and items under it.
Spending XP is the free action `p`.

Rolls and effects (E7): a roll vs L asks which roll (numbered), the L, then a yes or no (`y`,
`n`) for each Skill whose bonus depends on what the roll is about, then the text's modifier.
The result names each modifier, and a bonus that does not stack with a higher one is shown set
aside: "Defense vs L5: rolled 3, Dodge +2 (Agile +1 does not stack), total 5. Success."
"""

from __future__ import annotations

import argparse
import logging
from collections.abc import Callable, Sequence
from datetime import datetime
from pathlib import Path

from ..content import CatalogueEvent, CatalogueTable, Table, load_content
from ..dice import RandomDice
from ..effect_targets import RollType, Tag
from ..engine import Arrival, Game, Position, Stat, Upkeep
from ..engine.creation import Points
from ..engine.effects import Held, Modifier
from ..engine.game import Purchase, Rolled, RolledVsL, Searched
from ..engine.loop import play
from ..engine.manual import Manual
from ..engine.protocol import (
    Action,
    Book,
    Bought,
    Changed,
    Choose,
    Duplicate,
    End,
    Ended,
    Event,
    EventPlayed,
    ItemTaken,
    LeadRolled,
    Marked,
    NoteRemoved,
    NoteWritten,
    Number,
    Quit,
    Request,
    SheetAttached,
    Text,
    Topic,
    Wandering,
)
from ..engine.state import Item, Note, SkillLevel
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
    Action.SEARCH: ("s", "search"),
    Action.APPLY: ("a", "apply an effect"),
    Action.SPEND_XP: ("p", "spend XP"),
    Action.SHEET: ("n", "attach a new sheet"),
    Action.QUIT: ("q", "quit"),
    Book.TABLE: ("t", "a table"),
    Book.EVENT: ("e", "a numbered event"),
    Manual.GAIN: ("g", "gain"),
    Manual.LOSE: ("l", "lose"),
    Manual.ROLL: ("v", "roll vs L"),
    Manual.WRITE_NOTE: ("w", "write a note"),
    Manual.REMOVE_NOTE: ("x", "remove a note"),
    Manual.SAFE_HOUSE: ("h", "mark a Safe House"),
    Manual.BACK: ("b", "back"),
    Book.DONE: ("d", "nowhere else"),
}
"""Options with a letter of their own; tables and events to choose from are numbered."""

STATS = {
    Stat.LIFE: "Life",
    Stat.SANITY: "Sanity",
    Stat.FOOD: "Food",
    Stat.XP: "XP",
    Stat.CLUES: "Clues",
}

POINTS = {
    Points.STATS: ("l", "Life and Sanity"),
    Points.SKILL: ("k", "1 more Skill"),
    Points.WEAPON: ("w", "1 more Random Weapon roll"),
    Points.OBJECT: ("o", "1 more Random Objects roll"),
    Points.USEFUL: ("u", "1 more Useful Stuff roll"),
}
"""What the 3 creation points buy, by letter."""

TAGS = {
    Tag.HAND_TO_HAND: "a hand-to-hand weapon",
    Tag.RANGED: "a ranged weapon",
    Tag.BOW: "a bow",
    Tag.UNARMED: "an unarmed attack",
    Tag.VAMPIRE: "a vampire",
    Tag.ZOMBIE: "a zombie",
    Tag.POISON: "poison",
    Tag.INFECTION: "infection",
    Tag.DISEASE: "disease",
    Tag.FEAR: "fear",
    Tag.MAGIC: "magic",
    Tag.HYPNOTISM: "hypnotism",
    Tag.PSIONICS: "psionics",
    Tag.CLIMB: "climbing",
    Tag.JUMP: "jumping",
    Tag.AVOID_DANGER: "avoiding danger",
}
"""How a tag reads in a question: "Does this Save involve poison?"."""

YES_NO = {"y": True, "n": False}

NUMBER_PROMPTS = {
    Topic.LIFE_POINTS: "How many of the 3 points on Life (the rest on Sanity)? ",
    Topic.AMOUNT: "How much? ",
    Topic.LEVEL: "L? ",
    Topic.MODIFIER: "Modifier (Enter for none): ",
}
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
        self._skills_shown = False
        """The Skills' text was shown once at creation."""

    # --- The protocol --------------------------------------------------------------------

    def ask(self, request: Request) -> object:
        if isinstance(request, Number):
            if request.topic is Topic.MODIFIER and self.game.character.notes:
                self._output(self._notes())
            return self._number(request)
        if isinstance(request, Text):
            return self._text(
                "Your character's name: " if request.topic is Topic.NAME else "Note: "
            )
        options = request.options
        match request.topic:
            case Topic.POINTS:
                self._output("Your 3 points: on Life and Sanity (8 each), or traded.")
                keys = {POINTS[option][0]: option for option in options}
                self._output("  ".join(f"{key}) {POINTS[o][1]}" for key, o in keys.items()))
                return self._read(keys, "Your choice: ")
            case Topic.SKILL:
                return self._skills(request)
            case Topic.WEAPON:
                for n, option in _numbered(options):
                    weapon = self.game.content.weapon(option)
                    self._output(f"{n}) {weapon.name}: {weapon.text}")
                return self._read(_by_number(options), f"Which weapon? [1-{len(options)}] ")
            case Topic.PURCHASE:
                return self._menu(options, "Spend XP on? ")
            case Topic.ACTION:
                self._output("")
                self._output(self._status())
                if self.game.character.notes:
                    self._output(self._notes())
                return self._menu(options, "What do you do? ")
            case Topic.APPLY:
                return self._menu(options, "Which effect? ")
            case Topic.NOTES:
                for n, note in _numbered(options):
                    self._output(f"{n}) {_note(note)}")
                return self._read(_by_number(options), f"Which note? [1-{len(options)}] ")
            case Topic.CHOICE:
                return self._menu(options, "Your choice: ")
            case Topic.BOOK:
                return self._menu(options, "Apply the text, then where does it lead? ")
            case Topic.ROLL:
                self._output("  ".join(f"{n}) {_roll(o)}" for n, o in _numbered(options)))
                return self._read(_by_number(options), f"Which roll? [1-{len(options)}] ")
            case Topic.TAG:
                held = request.about
                assert isinstance(held, Held) and held.effect.roll is not None
                tags = [TAGS[tag] for tag in TAGS if tag in held.effect.tags]
                about = ", ".join(tags[:-1]) + f" or {tags[-1]}" if len(tags) > 1 else tags[0]
                prompt = (
                    f"Does this {_roll(held.effect.roll)} involve {about}? "
                    f"({self._source(held.source)} {held.amount:+d}) [y/n] "
                )
                return self._read(YES_NO, prompt)
            case Topic.STAT:
                self._output("  ".join(f"{n}) {STATS[stat]}" for n, stat in _numbered(options)))
                return self._read(_by_number(options), f"Which? [1-{len(options)}] ")
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
            case Changed(stat=stat, amount=0, value=value):
                self._output(f"You are at your max {STATS[stat]} ({value}).")
            case Changed(stat=stat, amount=amount, value=value):
                verb = "gain" if amount > 0 else "lose"
                self._output(f"You {verb} {abs(amount)} {STATS[stat]} ({STATS[stat]} {value}).")
            case RolledVsL():
                self._output(self._vs_l(event))
            case NoteWritten(note=note):
                self._output(f"Noted: {note.text}")
            case NoteRemoved(note=note):
                self._output(f"Note removed: {note.text}")
            case Marked():
                self._output("This box is a Safe House.")
            case Searched(face=face, modifiers=modifiers):
                line = f"Search: rolled {face}"
                if modifiers:
                    line += ": a natural 1 stays 1" if face == 1 else self._modifiers(modifiers)
                self._output(f"{line}.")
            case ItemTaken(item=item):
                self._output(f"You take: {self._item(item)}.")
            case Duplicate():
                self._output("You have it already: roll again.")
            case Bought(purchase=purchase):
                self._output(f"{self._purchase_done(purchase)}: {purchase.cost} XP spent.")
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

    def _number(self, request: Number) -> int:
        """Ask until the player types a whole number within the bounds; Enter alone is 0 when
        0 fits (no modifier)."""
        while True:
            try:
                line = self._input(NUMBER_PROMPTS.get(request.topic, "Number? ")).strip()
            except (EOFError, KeyboardInterrupt):
                raise Quit from None
            try:
                number = int(line) if line else 0
            except ValueError:
                number = None
            if number is not None and (line or request.topic is Topic.MODIFIER):
                if request.fits(number):
                    return number
            self._output(f"Type a whole number{_bounds(request)}.")

    def _text(self, prompt: str) -> str:
        """Ask until the player types something."""
        while True:
            try:
                line = self._input(prompt).strip()
            except (EOFError, KeyboardInterrupt):
                raise Quit from None
            if line:
                return line
            self._output("Type some text.")

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
        if isinstance(option, Purchase):
            return self._purchase(option)
        return self._name(str(option))

    # --- The character ----------------------------------------------------------------------

    def _skills(self, request: Choose) -> object:
        """Skills to choose from at creation: with their text the first time, by name after."""
        content = self.game.content
        for n, option in _numbered(request.options):
            skill = content.skill(option)
            if self._skills_shown:
                self._output(f"{n:>3}) {skill.name}")
            else:
                self._output(_indented(skill.text, f"{n:>3}) {skill.name} ({skill.xp} XP): "))
        self._skills_shown = True
        return self._read(_by_number(request.options), f"Skill? [1-{len(request.options)}] ")

    def _source(self, source: str | None) -> str:
        """Where a modifier comes from: a Skill, an Injury or a Mental Scar, or the text."""
        content = self.game.content
        if source is None:
            return "modifier"
        if source.startswith(("skill.", "arcane_skill.")):
            return content.skill(source).name
        return content.entry(source).name or source

    def _modifiers(self, modifiers: Sequence[Modifier], set_aside: Sequence[Modifier] = ()) -> str:
        """ ", Resilient +1, modifier -1", each set aside after the one it gives way to."""
        shown = "".join(f", {self._source(m.source)} {m.amount:+d}" for m in modifiers)
        for m in set_aside:
            shown += f" ({self._source(m.source)} {m.amount:+d} does not stack)"
        return shown

    def _vs_l(self, rolled: RolledVsL) -> str:
        result = "Success." if rolled.success else "Failure."
        if rolled.face == 1:
            result = "A natural 1 always fails."
        elif rolled.face == 6:
            result = "A natural 6 always succeeds."
        modifiers = self._modifiers(rolled.modifiers, rolled.set_aside)
        total = f", total {rolled.total}" if rolled.modifiers else ""
        return (
            f"{_roll(rolled.roll)} vs L{rolled.level}: rolled {rolled.face}{modifiers}{total}. "
            f"{result}"
        )

    def _purchase(self, purchase: Purchase) -> str:
        name = self.game.content.skill(purchase.skill_id).name
        expert = " (Expert)" if purchase.level is SkillLevel.EXPERT else ""
        return f"{name}{expert}: {purchase.cost} XP"

    def _purchase_done(self, purchase: Purchase) -> str:
        name = self.game.content.skill(purchase.skill_id).name
        if purchase.level is SkillLevel.EXPERT:
            return f"{name} becomes Expert"
        return f"You learn {name}"

    def _item(self, item: Item) -> str:
        """An item's name, then how many or how many uses."""
        content = self.game.content
        if item.id in content.weapons or item.id in content.variants:
            name = content.weapon(item.id).name
        else:
            name = item.id.split(".", 1)[1].replace("_", " ").capitalize()
        if item.count is not None:
            name += f" ({item.count})"
        if item.uses is not None:
            name += f" ({item.uses} uses)"
        return name

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
        if id_ in content.weapons or id_ in content.variants:
            return content.weapon(id_).name
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
        """The status line, then the Skills, Injuries, Mental Scars and items, if any."""
        game, c = self.game, self.game.character
        name = f"{c.name} · " if c.name else ""
        lines = [
            f"{name}Box {game.campaign.box_counter} · "
            f"Life {c.life}/{game.max(Stat.LIFE)} · Sanity {c.sanity}/{game.max(Stat.SANITY)} · "
            f"Food {c.food} · XP {c.xp} · Clues {c.clues}"
        ]
        if c.skills:
            skills = (
                game.content.skill(id_).name + (" (Expert)" if level is SkillLevel.EXPERT else "")
                for id_, level in c.skills.items()
            )
            lines.append(f"Skills: {', '.join(skills)}")
        for label, held in (("Injuries", c.injuries), ("Mental Scars", c.mental_scars)):
            if held:
                lines.append(f"{label}: {', '.join(self._source(id_) for id_ in held)}")
        if c.items:
            lines.append(f"Items: {', '.join(self._item(item) for item in c.items)}")
        return "\n".join(lines)

    def _notes(self) -> str:
        notes = "  ".join(
            f"({n}) {_note(note)}" for n, note in _numbered(self.game.character.notes)
        )
        return f"Notes: {notes}"

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


def _note(note: Note) -> str:
    return f"box {note.box}: {note.text}"


def _bounds(request: Number) -> str:
    match request.minimum, request.maximum:
        case None, None:
            return ""
        case low, None:
            return f", {low} or more"
        case None, high:
            return f", {high} or less"
        case low, high:
            return f" from {low} to {high}"


def _roll(roll: RollType) -> str:
    return roll.capitalize()


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
