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

Moments and lasting effects (E8): a meal ("You eat 1 Food") and an effect that ends ("Ended: -1
on all rolls.") are told after the arrival. The status line shows the next meal, with the
Injuries, Mental Scars and lasting effects under it ("-1 on all rolls (ends at box 14)"). `f`
adds a lasting effect (all rolls or one roll type, numbered; the modifier; the boxes, Enter for
until removed), `u` removes one.

Drills (T1): `--drill NAME` says what the drill tries, then plays it; a drill with a
pregenerated character lists the two sheets, numbered. When the drill is over, the character
is shown once more.

Creation screens (T2): each creation step (`StepStarted`) has a heading and says what it
asks, and each answer what it gave ("→ Life 10, Sanity 9."). The Skills keep their numbers on
every list, the ones taken marked; `r` hides or shows their texts. The knife or stick shows the
text they share once, and the stick's own sentence as an aside. A roll reads "Injury table,
rolled 1: Facial scar". Book mode says in one line what it is, then where the text leads and
what to do by hand on two lines. The wording is in `screens/` (`screen_text`). At the
keyboard, the arrow keys edit the line typed.

Feedback (T1): a line starting with # at any prompt is a note kept with the seed, the drill and
the box (`feedback.FeedbackLog`, `--feedback-file`), then the same question is asked again.
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
from ..engine import Arrival, Game, Position, Stat, Upkeep, drills
from ..engine.creation import BASE, STARTING_SKILLS, Points
from ..engine.creation import POINTS as CREATION_POINTS
from ..engine.effects import PLAYER, Held, Modifier
from ..engine.game import Purchase, Rolled, RolledVsL, Searched
from ..engine.loop import play
from ..engine.manual import Manual
from ..engine.protocol import (
    Action,
    Book,
    Bought,
    Changed,
    Choose,
    Created,
    Duplicate,
    EffectEnded,
    End,
    Ended,
    Event,
    EventPlayed,
    FoodUpkeep,
    ItemTaken,
    LastingAdded,
    LastingRemoved,
    LeadRolled,
    Marked,
    NoteRemoved,
    NoteWritten,
    Number,
    Quit,
    Request,
    SheetAttached,
    Step,
    StepStarted,
    Text,
    Topic,
    Wandering,
)
from ..engine.state import Item, Lasting, Note, SkillLevel
from ..engine.town import SHEET_COLUMNS, SHEET_ROWS, sheet_neighbours
from .feedback import PREFIX, FeedbackLog
from .screen_text import ScreenText, load_screen_text

CELL = 5
"""Width of a box on the map: room for "[30]" or a box number in the thousands."""

ENDINGS = {
    End.DEAD: "You are dead. The game is over.",
    End.INSANE: "You have gone insane. The game is over.",
    End.QUIT: "You quit the game.",
    End.DRILL_OVER: "The drill is over.",
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
    Manual.ADD_LASTING: ("f", "add a lasting effect"),
    Manual.REMOVE_LASTING: ("u", "remove a lasting effect"),
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
    Points.STATS: "l",
    Points.SKILL: "k",
    Points.WEAPON: "w",
    Points.OBJECT: "o",
    Points.USEFUL: "u",
}
"""What the 3 creation points buy, by letter; their wording is in `screens/creation.yaml`."""

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
    Topic.AMOUNT: "How much? ",
    Topic.LEVEL: "L? ",
    Topic.MODIFIER: "Modifier (Enter for none): ",
    Topic.BOXES: "For the next how many boxes? (Enter: until removed) ",
}
ENTER_IS_0 = frozenset({Topic.MODIFIER, Topic.BOXES})
"""Numbers where Enter alone means 0: no modifier, until removed."""
RULES_KEY = "r"

SIDES = {(0, -1): "above", (-1, 0): "left of", (1, 0): "right of", (0, 1): "below"}


class TerminalInterface:
    def __init__(
        self,
        game: Game,
        input_fn: Callable[[str], str] = input,
        output_fn: Callable[[str], None] = print,
        feedback: FeedbackLog | None = None,
        text: ScreenText | None = None,
    ) -> None:
        self.game = game
        self.screen = text or load_screen_text()
        """The terminal's own wording (`screens/`)."""
        self._input = input_fn
        self._feedback = feedback
        self._output = output_fn
        self._seen: set[str] = set()
        """Tables whose own rules were shown in this game."""
        self._rules: Table | None = None
        """The last table with rules rolled in this box, to show them on request."""
        self._recap = False
        """The character was just shown, at the end of creation."""
        self._sheet_texts = False
        """The recap shows the descriptions (`r` switches)."""
        self._skill_texts = True
        """The Skills are listed with their text (`r` switches)."""
        self._skill_count = STARTING_SKILLS
        """How many Skills creation asks for: one more when the points are traded for one."""

    # --- The protocol --------------------------------------------------------------------

    def ask(self, request: Request) -> object:
        if isinstance(request, Number):
            if request.topic is Topic.MODIFIER and self.game.character.notes:
                self._output(self._notes())
            if request.topic is Topic.LIFE_POINTS:
                return self._life_points(request)
            return self._number(request)
        if isinstance(request, Text):
            if request.topic is Topic.NAME:
                return self._text(self.screen("creation.name.prompt"))
            return self._text("Note: ")
        options = request.options
        match request.topic:
            case Topic.POINTS:
                return self._points(request)
            case Topic.SKILL:
                return self._skills(request)
            case Topic.PREGENERATED:
                for n, option in _numbered(options):
                    self._output(f"{n}) {self._pregenerated(option)}")
                return self._read(_by_number(options), f"Which character? [1-{len(options)}] ")
            case Topic.WEAPON:
                return self._weapons(request)
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
            case Topic.TARGET:
                labels = ["All rolls", *(_roll(o) for o in options[1:])]
                self._output("  ".join(f"{n}) {label}" for n, label in _numbered(labels)))
                return self._read(_by_number(options), f"On which rolls? [1-{len(options)}] ")
            case Topic.LASTING:
                for n, lasting in _numbered(options):
                    self._output(f"{n}) {self._lasting_with_end(lasting)}")
                return self._read(_by_number(options), f"Which one? [1-{len(options)}] ")
            case Topic.NOTES:
                for n, note in _numbered(options):
                    self._output(f"{n}) {_note(note)}")
                return self._read(_by_number(options), f"Which note? [1-{len(options)}] ")
            case Topic.CHOICE:
                return self._menu(options, "Your choice: ")
            case Topic.BOOK:
                return self._book(options)
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
                self._recap = False
                self._rules = None
                self._output("Home is box 1.")
            case Arrival(number=number):
                self._recap = False
                self._rules = None
                self._output(f"Box {number}.")
            case FoodUpkeep(result=Upkeep.ATE):
                self._output(f"You eat 1 Food (Food {self.game.character.food}).")
            case FoodUpkeep(result=Upkeep.STARVED):
                self._output(f"No Food: you lose 1 Life (Life {self.game.character.life}).")
            case EffectEnded(lasting=lasting):
                self._output(f"Ended: {self._lasting(lasting)}.")
            case LastingAdded(lasting=lasting):
                self._output(f"Lasting effect: {self._lasting_with_end(lasting)}.")
            case LastingRemoved(lasting=lasting):
                self._output(f"Removed: {self._lasting(lasting)}.")
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
            case StepStarted(step=step):
                self._step(step)
            case Created():
                self._recap_sheet()
                self._recap = True
            case Bought(purchase=purchase):
                self._output(f"{self._purchase_done(purchase)}: {purchase.cost} XP spent.")
            case Ended(end=end):
                self._output(ENDINGS[end])
                shown = self._recap  # the creation drill ends on the recap
                if end is End.DRILL_OVER and self.game.campaign.character is not None and not shown:
                    self._output(self._status())

    # --- Reading ----------------------------------------------------------------------------

    def _read(self, keys: dict[str, object], prompt: str, rules: bool = False) -> object:
        """Ask until the player types one of the keys; `r` shows the last table's rules."""
        while True:
            line = self._line(prompt).lower()
            if line in keys:
                return keys[line]
            if rules and line == RULES_KEY and self._rules is not None:
                self._show_rules(self._rules)
                continue
            self._output(f"Choose one of {', '.join(keys) if len(keys) < 10 else _span(keys)}.")

    def _number(self, request: Number, prompt: str | None = None) -> int:
        """Ask until the player types a whole number within the bounds; Enter alone is 0 when
        0 fits (no modifier)."""
        prompt = prompt or NUMBER_PROMPTS.get(request.topic, "Number? ")
        while True:
            line = self._line(prompt)
            try:
                number = int(line) if line else 0
            except ValueError:
                number = None
            if number is not None and (line or request.topic in ENTER_IS_0):
                if request.fits(number):
                    return number
            self._output(f"Type a whole number{_bounds(request)}.")

    def _text(self, prompt: str) -> str:
        """Ask until the player types something."""
        while True:
            if line := self._line(prompt):
                return line
            self._output("Type some text.")

    def _line(self, prompt: str) -> str:
        """The player's next line. A feedback note (# first) is kept, and the question asked
        again; end of input quits."""
        while True:
            try:
                line = self._input(prompt).strip()
            except (EOFError, KeyboardInterrupt):
                raise Quit from None
            if not line.startswith(PREFIX):
                return line
            note = line.removeprefix(PREFIX).strip()
            if self._feedback is None:
                self._output("No feedback file in this game.")
            elif note:
                self._feedback.write(self.game, prompt, note)
                self._output("Feedback saved.")
            else:
                self._output("Type your note after the #.")

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

    def _book(self, options: Sequence[object]) -> object:
        """Book mode: what the text cannot do by itself. The explanation, then where the text
        leads (numbered tables and events, `t`, `e`, `d`) and the manual actions by letter, on
        two lines; `r` for the rules of the last table rolled in this box."""
        keys: dict[str, object] = {}
        numbered = (option for option in options if option not in KEYS)
        for n, option in enumerate(numbered, start=1):
            keys[str(n)] = option
        for option in options:
            if option in KEYS:
                keys[KEYS[option][0]] = option
        leads = [k for k, option in keys.items() if not isinstance(option, Manual)]
        by_hand = [k for k, option in keys.items() if isinstance(option, Manual)]
        labels = (self.screen("book_mode.leads"), self.screen("book_mode.by_hand"))
        width = max(len(label) for label in labels)
        self._output("")
        self._output(self.screen("book_mode.explanation"))
        self._output("")
        for label, shown in zip(labels, (leads, by_hand), strict=True):
            if shown:
                options_shown = "  ".join(f"{k}) {self._label(keys[k])}" for k in shown)
                self._output(f"  {label.ljust(width)} {options_shown}")
        if self._rules is not None:
            self._output(f"  {RULES_KEY}) rules of the {self._rules.name}")
        return self._read(keys, self.screen("book_mode.prompt"), rules=True)

    def _label(self, option: object) -> str:
        if option in KEYS:
            return KEYS[option][1]
        if isinstance(option, Purchase):
            return self._purchase(option)
        return self._name(str(option))

    # --- The character ----------------------------------------------------------------------

    def _step(self, step: Step) -> None:
        """A creation step's heading and what it asks; the introduction before the first."""
        if step is Step.NAME:
            self._output("")
            self._output(self.screen("creation.title"))
            for line in self.screen("creation.intro").splitlines():
                self._output(line)
        self._output("")
        self._output(self.screen(f"creation.{step}.heading", count=self._skill_count))
        self._output(self.screen(f"creation.{step}.text"))

    def _points(self, request: Choose) -> object:
        """The 3 points by letter; a trade says what it gave."""
        for option in request.options:
            if option is Points.STATS:
                label = self.screen("creation.points.share")
            else:
                label = self.screen("creation.points.trade", extra=self._extra(option))
            self._output(f"  {POINTS[option]}) {label}")
        keys = {POINTS[option]: option for option in request.options}
        points = self._read(keys, self.screen("creation.points.prompt"))
        if points is Points.SKILL:
            self._skill_count = STARTING_SKILLS + 1
        if points is not Points.STATS:
            self._output(
                self.screen(
                    "creation.points.traded", life=BASE, sanity=BASE, extra=self._extra(points)
                )
            )
        return points

    def _extra(self, points: Points) -> str:
        return self.screen(f"creation.points.extra.{points}")

    def _life_points(self, request: Number) -> int:
        """The points on Life, the rest on Sanity; then Life and Sanity."""
        prompt = self.screen(
            "creation.points.life", minimum=request.minimum, maximum=request.maximum
        )
        on_life = self._number(request, prompt)
        life, sanity = BASE + on_life, BASE + CREATION_POINTS - on_life
        self._output(self.screen("creation.points.shared", life=life, sanity=sanity))
        return on_life

    def _skills(self, request: Choose) -> object:
        """Skills to choose from at creation, numbered in the book's order on every list,
        the ones taken marked and refused; `r` hides or shows the texts, for the next list
        too."""
        content = self.game.content
        every = list(content.skills)
        n = len(every) - len(request.options) + 1
        self._skill_list(request.options)
        keys = {str(i): skill for i, skill in _numbered(every) if skill in request.options}
        taken = {str(i): skill for i, skill in _numbered(every) if skill not in request.options}
        prompt = self.screen(
            "creation.skills.prompt", n=n, count=self._skill_count, last=len(every)
        )
        while True:
            line = self._line(prompt).lower()
            if line in keys:
                self._output(
                    self.screen("creation.skills.chosen", name=content.skill(keys[line]).name)
                )
                return keys[line]
            if line in taken:
                name = content.skill(taken[line]).name
                self._output(self.screen("creation.skills.already", name=name))
            elif line == RULES_KEY:
                self._skill_texts = not self._skill_texts
                self._skill_list(request.options)
            else:
                self._output(f"Choose one of 1 to {len(every)}.")

    def _skill_list(self, offered: Sequence[object]) -> None:
        """Every Skill, numbered: name and XP, with the text unless hidden; a taken one
        marked. Then `r` to hide or show the texts."""
        content = self.game.content
        for n, skill_id in _numbered(list(content.skills)):
            skill = content.skill(skill_id)
            if skill_id not in offered:
                self._output(f"{n:>3}) " + self.screen("creation.skills.taken", name=skill.name))
            elif self._skill_texts:
                self._output(_indented(skill.text, f"{n:>3}) {skill.name} ({skill.xp} XP): "))
            else:
                self._output(f"{n:>3}) {skill.name} ({skill.xp} XP)")
        toggle = "creation.skills.hide" if self._skill_texts else "creation.skills.show"
        self._output(f"{RULES_KEY:>3}) " + self.screen(toggle))

    def _weapons(self, request: Choose) -> object:
        """Weapons to choose from. Variants of one heading (the knife or stick) show the
        heading's text once, then each one's own sentence; others show their whole text."""
        content = self.game.content
        weapons = [content.weapon(option) for option in request.options]
        headings = {weapon.heading for weapon in weapons}
        last = len(weapons)
        if len(headings) == 1 and None not in headings:
            heading = content.weapon(weapons[0].heading)
            self._output(f"{heading.name}: {heading.text}")
            for n, weapon in _numbered(weapons):
                aside = f" ({_aside(weapon.extra)})" if weapon.extra else ""
                self._output(f"  {n}) {weapon.name}{aside}")
            prompt = self.screen("creation.weapons.prompt_named", name=heading.name, last=last)
        else:
            for n, weapon in _numbered(weapons):
                self._output(f"  {n}) {weapon.name}: {weapon.text}")
            prompt = self.screen("creation.weapons.prompt", last=last)
        return self._read(_by_number(request.options), prompt)

    def _source(self, source: str | None) -> str:
        """Where a modifier comes from: a Skill, an Injury or a Mental Scar, or the text."""
        content = self.game.content
        if source is None:
            return "modifier"
        if source == PLAYER:
            return "lasting effect"
        if source.startswith(("skill.", "arcane_skill.")):
            return content.skill(source).name
        return content.entry(source).name or source

    def _modifiers(self, modifiers: Sequence[Modifier], set_aside: Sequence[Modifier] = ()) -> str:
        """ ", Resilient +1, modifier -1", each set aside after the one it gives way to."""
        shown = "".join(f", {self._source(m.source)} {m.amount:+d}" for m in modifiers)
        for m in set_aside:
            shown += f" ({self._source(m.source)} {m.amount:+d} does not stack)"
        return shown

    def _lasting(self, lasting: Lasting) -> str:
        """What a lasting effect changes: "-1 on all rolls", "-1 on Stealth rolls", named
        after its source unless the player added it."""
        effect = lasting.effect
        amount = effect.amount(expert=False)
        if effect.parameter is not None:
            what = f"{amount:+d} to the {effect.parameter.replace('_', ' ')}"
        elif effect.roll is None:
            what = f"{amount:+d} on all rolls"
        else:
            what = f"{amount:+d} on {_roll(effect.roll)} rolls"
        if lasting.source == PLAYER:
            return what
        return f"{self._source(lasting.source)}: {what}"

    def _lasting_with_end(self, lasting: Lasting) -> str:
        """A lasting effect, then when it ends: "-1 on all rolls (ends at box 14)"."""
        ends_at = self.game.ends_at(lasting)
        end = "until removed" if ends_at is None else f"ends at box {ends_at}"
        return f"{self._lasting(lasting)} ({end})"

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
            self._output(
                self.screen(
                    "rolls.not_copied", table=source.name, results=results, source=source.source
                )
            )
            return
        table = content.table(rolled.table_id)
        entry = content.entry(rolled.entry_id)
        if entry.name:
            self._output(
                self.screen("rolls.named", table=table.name, results=results, name=entry.name)
            )
        else:
            self._output(self.screen("rolls.rolled", table=table.name, results=results))
        if table.text:
            self._rules = table
            if table.id not in self._seen:
                self._show_rules(table)
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
        """The status line, then the Skills, Injuries, Mental Scars, items and lasting
        effects, if any."""
        game, c = self.game, self.game.character
        name = f"{c.name} · " if c.name else ""
        lines = [
            f"{name}Box {game.campaign.box_counter} · "
            f"Life {c.life}/{game.max(Stat.LIFE)} · Sanity {c.sanity}/{game.max(Stat.SANITY)} · "
            f"Food {c.food}{self._next_meal()} · XP {c.xp} · Clues {c.clues}"
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
        if c.lasting:
            lasting = ", ".join(self._lasting_with_end(lasting) for lasting in c.lasting)
            lines.append(f"Lasting effects: {lasting}")
        return "\n".join(lines)

    def _recap_sheet(self) -> None:
        """The character once made, until the player goes on (Enter); `r` hides or shows the
        descriptions. A pause of the terminal's own: nothing is answered to the engine."""
        while True:
            self._output("")
            self._output(self.screen("creation.recap.title"))
            for line in self._sheet(self._sheet_texts):
                self._output(line)
            toggle = "creation.recap.hide" if self._sheet_texts else "creation.recap.show"
            self._output(f"  {RULES_KEY}) " + self.screen(toggle))
            line = None
            while line not in ("", RULES_KEY):  # anything else: asked again
                line = self._line(self.screen("creation.recap.prompt")).lower()
            if not line:
                return
            self._sheet_texts = not self._sheet_texts

    def _sheet(self, texts: bool = False) -> list[str]:
        """The character sheet, one thing a line: the numbers, then the Skills, the weapons,
        the other items and the notes, each with its description when asked. Shown after
        creation (T2); meant to grow into the sheet shown during play."""
        game, c = self.game, self.game.character
        content = game.content
        name = f"{c.name} · " if c.name else ""
        weapons = [i for i in c.items if i.id in content.weapons or i.id in content.variants]
        others = [item for item in c.items if item not in weapons]
        skills = [
            (
                content.skill(id_).name + (" (Expert)" if level is SkillLevel.EXPERT else ""),
                content.skill(id_).text,
            )
            for id_, level in c.skills.items()
        ]
        sections = [
            ("skills", skills),
            ("weapons", [(self._item(i), content.weapon(i.id).text) for i in weapons]),
            ("items", [(self._item(item), self._item_text(item)) for item in others]),
            ("notes", [(note.text, None) for note in c.notes]),
        ]
        lines = [
            f"  {name}Food {c.food} · XP {c.xp} · Clues {c.clues}",
            f"    - Life {c.life}/{game.max(Stat.LIFE)}",
            f"    - Sanity {c.sanity}/{game.max(Stat.SANITY)}",
        ]
        for key, shown in sections:
            if shown:
                lines.append("  " + self.screen(f"creation.recap.{key}"))
                for label, text in shown:
                    if texts and text:
                        described = _indented(text, f"    - {label}: ", "      ")
                        lines += [line.rstrip() for line in described.splitlines()]
                    else:
                        lines.append(f"    - {label}")
        return lines

    def _item_text(self, item: Item) -> str | None:
        """An item's description: the text of the entry that gave it, or of the first entry
        that gives it (one item, one text)."""
        content = self.game.content
        source = item.source if item.source in content.entries else None
        if source is None:
            source = next(iter(content.items.get(item.id, ())), None)
        return content.entry(source).text if source is not None else None

    def _pregenerated(self, id_: str) -> str:
        """A pregenerated character in one line: "Anna Miller: Life 10, Sanity 9, Food 4;
        Will, Occultist"."""
        sheet = self.game.content.pregenerated[id_]
        skills = ", ".join(self.game.content.skill(skill).name for skill in sheet.skills)
        return (
            f"{sheet.name}: Life {sheet.life}, Sanity {sheet.sanity}, Food {sheet.food}; {skills}"
        )

    def _next_meal(self) -> str:
        """When the next meal comes, once the interval can change (E8): " (next meal: box
        10)". On its own, so it is easy to drop."""
        return f" (next meal: box {self.game.next_meal()})"

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


def _aside(sentence: str) -> str:
    """A sentence as an aside in parentheses: "(you may pick up a stick…)"."""
    return sentence[0].lower() + sentence[1:].rstrip(".")


def _span(keys: dict[str, object]) -> str:
    return f"{next(iter(keys))} to {list(keys)[-1]}"


def _indented(text: str, first: str = "  ", rest: str = "  ") -> str:
    lines = text.strip().splitlines()
    return "\n".join([first + lines[0], *(rest + line for line in lines[1:])])


# --- Starting a game ------------------------------------------------------------------------


def _line_editing() -> None:
    """At the keyboard, the arrow keys move in the line typed and go back to lines typed
    before (T2): loading `readline` is enough for `input`. Some systems have none."""
    try:
        import readline  # noqa: F401
    except ImportError:
        pass


def main(
    argv: Sequence[str] | None = None,
    *,
    input_fn: Callable[[str], str] = input,
    output_fn: Callable[[str], None] = print,
) -> int:
    parser = argparse.ArgumentParser(description="Play Alone Against Fear in the terminal.")
    parser.add_argument("--seed", type=int, help="dice seed (default: picked and logged)")
    parser.add_argument("--log-dir", default="logs", help="where the log file goes")
    parser.add_argument(
        "--feedback-file",
        default="feedback/feedback.md",
        help="where feedback notes (# at any prompt) go",
    )
    parser.add_argument(
        "--drill", choices=list(drills.DRILLS), help="play a short scoped run (a drill)"
    )
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
        output_fn(f"Type {PREFIX} and a note at any prompt to leave feedback.")
        dice = RandomDice(args.seed)
        game = Game(dice=dice, content=load_content())
        feedback = FeedbackLog(args.feedback_file, dice.seed, args.drill, log_file)
        if input_fn is input:
            _line_editing()
        interface = TerminalInterface(game, input_fn, output_fn, feedback)
        if args.drill is None:
            play(game, interface)
        else:
            output_fn(f"Drill {args.drill}: {drills.DRILLS[args.drill].about}")
            drills.run(args.drill, game, interface)
    finally:
        logger.removeHandler(handler)
        logger.setLevel(level)
        handler.close()
    return 0
