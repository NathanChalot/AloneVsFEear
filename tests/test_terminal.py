"""E4: the minimal terminal interface.

It shows the character, the map and each request with numbered options, reads the player's
choice and checks it before answering; it narrates what the engine tells it. It reads the game
state to show it, and changes it only through its answers. Input and output are passed in, so a
test plays the terminal with typed lines.
"""

import pytest

from alone_against_fear.content import Effect, load_content
from alone_against_fear.dice import ScriptedDice
from alone_against_fear.effect_targets import RollType
from alone_against_fear.engine import Game, Position, book_mode, drills
from alone_against_fear.engine.creation import create
from alone_against_fear.engine.loop import play
from alone_against_fear.engine.protocol import End
from alone_against_fear.engine.state import SkillLevel
from alone_against_fear.engine.town import boxes_of
from alone_against_fear.interface.screen_text import load_screen_text
from alone_against_fear.interface.terminal import TerminalInterface, main


@pytest.fixture(scope="module")
def content():
    return load_content()


class Typist:
    """Types the given lines, one per prompt, and remembers the prompts."""

    def __init__(self, lines):
        self.lines = list(lines)
        self.prompts = []

    def __call__(self, prompt=""):
        self.prompts.append(prompt)
        if not self.lines:
            raise EOFError
        return self.lines.pop(0)


def ready(content, *faces):
    """A game whose character is created already: Life and Sanity 8, Food 3."""
    game = Game(dice=ScriptedDice(faces), content=content)
    game.create_character(life=8, sanity=8, food=3)
    return game


def terminal(game, lines):
    """A terminal that reads the game to show it, typing the given lines."""
    output = []
    return TerminalInterface(game, input_fn=Typist(lines), output_fn=output.append), output


# Boxes are numbered from 1 in reading order (row by row). Home in the top-left box is option
# 1; from there the box to the right is option 1, and from that box the top-left box is option 1
# again. Actions have letters: m to move, q to quit; d says a text leads nowhere else.
HOME_TOP_LEFT = "1"
QUIT = "q"
EXPLORE = (3, 4, 4, 2)
"""A new box: Town Exploration 7 (3 and 4), its d6 shows 4 (the House), the House's d6 2."""
RESOLVE = "d"
"""The House is not copied yet: its text leads nowhere else."""
NO_ENCOUNTER = 4
"""The 1 in 6 of a visited box, missed."""
FIRST_MOVE = ["m", "1", RESOLVE]
"""To the new box right of Home, resolved."""
BACK_AND_FORTH = ["m", "1"]
"""Between the two visited boxes."""


def test_a_player_walks_ten_boxes_in_the_terminal(content):
    # given a game played in the terminal: Food 3, one new box, then nine visited ones
    game = ready(content, *EXPLORE, *[NO_ENCOUNTER] * 9)
    interface, output = terminal(game, [HOME_TOP_LEFT, *FIRST_MOVE, *BACK_AND_FORTH * 9, QUIT])

    # when the player types Home, ten moves, then quit
    end = play(game, interface)

    # then ten boxes were walked after Home, between the two top-left boxes
    assert end is End.QUIT
    assert game.campaign.box_counter == 11
    assert game.campaign.position == Position(0, 0)
    assert game.campaign.map.boxes[Position(1, 0)].numbers == [2, 4, 6, 8, 10]
    # and the terminal showed the character, the box numbers and the end
    text = "\n".join(output)
    assert "Life 8" in text and "Sanity 8" in text and "Food 1" in text
    assert "Box 11" in text
    assert "quit" in output[-1].lower()


def test_the_map_shows_where_the_character_stands_and_the_numbered_choices(content):
    game = ready(content, *EXPLORE)
    interface, output = terminal(game, [HOME_TOP_LEFT, *FIRST_MOVE, QUIT])

    play(game, interface)

    text = "\n".join(output)
    assert "@" in text  # where the character stands
    assert "[1]" in text  # an option on the map


def test_a_wrong_choice_is_asked_again(content):
    game = ready(content)
    typist = Typist(["x", "99", HOME_TOP_LEFT, QUIT])
    output = []
    interface = TerminalInterface(game, input_fn=typist, output_fn=output.append)

    play(game, interface)

    assert game.campaign.home == Position(0, 0)
    assert sum("choose" in line.lower() for line in output) >= 2


def test_ending_the_input_quits(content):
    # Ctrl-D (end of input) is the same as choosing to quit
    game = ready(content)
    interface, _ = terminal(game, [HOME_TOP_LEFT])

    assert play(game, interface) is End.QUIT


def test_main_writes_the_log_to_a_file_with_the_seed_and_the_answers(tmp_path):
    # seed 7 rolls Random Weapon 3: the grenade (1) or the bow; then the knife (1)
    typist = Typist(["Ann", "l", "2", "1", "18", "1", "1", "", HOME_TOP_LEFT, QUIT])
    output = []

    code = main(
        ["--seed", "7", "--log-dir", str(tmp_path)], input_fn=typist, output_fn=output.append
    )

    assert code == 0
    [log_file] = tmp_path.glob("*.log")
    log = log_file.read_text()
    assert "dice seed 7" in log
    assert "answer name: Ann" in log
    assert "answer home: (0, 0)" in log
    assert "answer action: quit" in log


def test_the_free_actions_have_letters(content):
    game = ready(content)
    interface, output = terminal(game, [HOME_TOP_LEFT, QUIT])

    play(game, interface)

    assert "m) move  s) search  a) apply an effect  q) quit" in output


# --- Resolving a box -------------------------------------------------------------------------


def test_a_new_box_shows_its_entry_and_your_choice(content):
    # given a new box whose 2d6 show 3 and 5: Town Exploration 8; then the Street's d6 shows 4
    game = ready(content, 3, 5, 4)
    interface, output = terminal(game, [HOME_TOP_LEFT, "m", "1", "2", RESOLVE, QUIT])

    play(game, interface)

    text = "\n".join(output)
    assert "Town Exploration table, rolled 8" in text
    assert "Roll on the Store table or the Street table, your choice." in text
    # and only the entry reached: not entry 9
    assert "Sewers" not in text.split("Town Exploration table, rolled 8")[1]
    # and the choice offers the two tables only
    assert "1) Store table  2) Street table" in text
    assert "Street table, rolled 4" in text


def test_a_roll_names_the_table_the_number_and_the_entry_s_name(content):
    # given the Injury table rolled: 1, the Facial scar
    game = ready(content, 1)
    interface, output = terminal(game, [])

    interface.tell(game.roll_table("table.injury"))

    assert output[0] == "Injury table, rolled 1: Facial scar"


def test_a_die_rolled_by_an_entry_is_shown(content):
    game = ready(content, *EXPLORE)
    interface, output = terminal(game, [HOME_TOP_LEFT, *FIRST_MOVE, QUIT])

    play(game, interface)

    assert "  Rolled 4: House table" in output


def test_a_table_not_copied_yet_points_to_its_source_and_asks_where_it_leads(content):
    game = ready(content, *EXPLORE)
    interface, output = terminal(game, [HOME_TOP_LEFT, *FIRST_MOVE, QUIT])

    play(game, interface)

    assert (
        "House table, rolled 2: not copied yet, read entry 2 in "
        "gameRules/tables/places/5_7_house_table.md"
    ) in output
    # book mode: one line to explain it, then where the text leads and what to do by hand
    explanation = output.index(
        "The game cannot apply this text by itself: do what it says by hand, then choose where "
        "it leads."
    )
    assert output[explanation - 1] == output[explanation + 1] == ""
    assert output[explanation + 2] == "  Leads to: t) a table  e) a numbered event  d) nowhere else"
    assert output[explanation + 3].startswith("  By hand:  g) gain  l) lose  v) roll vs L")
    assert "Your choice? " in interface._input.prompts


def test_a_table_s_rules_are_shown_the_first_time_then_on_request(content):
    # given two new boxes in a row, along the top row (from the second box, option 2 is new)
    game = ready(content, *EXPLORE, *EXPLORE)
    lines = [HOME_TOP_LEFT, *FIRST_MOVE, "m", "2", "r", RESOLVE, QUIT]
    interface, output = terminal(game, lines)

    play(game, interface)

    rules = [line for line in output if "every time you move into an unexplored area" in line]
    # once on the first roll, once more on request; not on the second roll
    assert len(rules) == 2
    second_roll = max(
        i for i, line in enumerate(output) if line.startswith("Town Exploration table, rolled 7")
    )
    asked = [i for i, line in enumerate(output) if "every time you move" in line][-1]
    assert output[second_roll + 1].startswith("  Roll d6.")  # the entry, without the rules
    assert asked > second_roll


def test_an_entry_shows_the_notes_it_points_to(content):
    # given Town Exploration 2 (1 and 1), then Random Encounter 6 then 1: the Unique Vampires,
    # whose d6 shows 3
    game = ready(content, 1, 1, 6, 1, 3)
    interface, output = terminal(game, [HOME_TOP_LEFT, "m", "1", RESOLVE, QUIT])

    play(game, interface)

    text = "\n".join(output)
    assert "Random Encounter table, rolled 6, then 1" in text
    assert "Note: When rolling on tables of Unique creatures" in text
    assert "Unique Vampires table, rolled 3" in text


def test_the_text_can_lead_to_any_table_and_any_event(content):
    # given Town Exploration 6 (3 and 3): the Street, whose d6 shows 4; its text sends the
    # player to the Undead table (d6: 2), then to event #12
    game = ready(content, 3, 3, 4, 2)
    undead = str(table_names(content).index("Undead table") + 1)
    lines = [HOME_TOP_LEFT, "m", "1", "t", undead, "e", "12", RESOLVE, QUIT]
    interface, output = terminal(game, lines)

    play(game, interface)

    text = "\n".join(output)
    assert "Undead table, rolled 2" in text
    assert "Event #12, The sewer people: read it in gameRules/6_unique_events.md" in text


def table_names(content):
    """The table names in the order "a table" lists them."""
    game = Game(dice=ScriptedDice([]), content=content)
    names = {**content.tables, **content.catalogue}
    return [names[id_].name for id_ in book_mode.tables(game)]


def test_a_visited_box_says_whether_an_encounter_came(content):
    game = ready(content, *EXPLORE, NO_ENCOUNTER)
    interface, output = terminal(game, [HOME_TOP_LEFT, *FIRST_MOVE, *BACK_AND_FORTH, QUIT])

    play(game, interface)

    assert "No encounter. (1 in 6: rolled 4)" in output


def test_a_player_attaches_a_sheet_once_the_first_is_full_and_walks_onto_it(content):
    # given a first sheet all visited, the character on its right edge
    game = Game(dice=ScriptedDice(EXPLORE), content=content)
    game.create_character(life=8, sanity=8, food=3)
    game.choose_home(Position(0, 0))
    for box in boxes_of(Position(0, 0)):
        game.number_box(box)
    game.campaign.position = Position(4, 2)
    # the sides are listed above, left, right, below; from (4, 2) the box to the right is
    # option 5 (reading order: three above, left, right, three below)
    interface, output = terminal(game, ["n", "3", "m", "5", RESOLVE, QUIT])

    play(game, interface)

    text = "\n".join(output)
    assert "m) move  s) search  a) apply an effect  n) attach a new sheet  q) quit" in text
    assert "3) right of" in text
    assert "A new sheet is attached." in text
    assert game.campaign.position == Position(5, 2)
    assert "Box 32." in text
    assert "Town Exploration table, rolled 7" in text


# --- Manual actions (E5b) --------------------------------------------------------------------


def test_the_player_applies_an_entry_with_manual_actions(content):
    # given the House's entry, not copied yet: the player loses 2 Sanity, then leaves it
    game = ready(content, *EXPLORE)
    interface, output = terminal(game, [HOME_TOP_LEFT, "m", "1", "l", "2", "2", RESOLVE, QUIT])

    play(game, interface)

    text = "\n".join(output)
    assert "1) Life  2) Sanity  3) Food" in text
    assert "You lose 2 Sanity (Sanity 6)." in text
    assert game.character.sanity == 6


def test_a_wrong_number_is_asked_again(content):
    game = ready(content, *EXPLORE)
    lines = [HOME_TOP_LEFT, "m", "1", "g", "5", "two", "0", "1", RESOLVE, QUIT]
    interface, output = terminal(game, lines)

    play(game, interface)

    assert output.count("Type a whole number, 1 or more.") == 2
    assert game.character.clues == 1


SAVE = "3"
"""The Save, third of the rolls vs L."""


def test_a_roll_vs_l_shows_the_die_and_the_result(content):
    # the die shows 3; a Save vs L4 with no modifier (Enter)
    game = ready(content, *EXPLORE, 3)
    interface, output = terminal(game, [HOME_TOP_LEFT, "m", "1", "v", SAVE, "4", "", RESOLVE, QUIT])

    play(game, interface)

    assert (
        "1) Attack  2) Defense  3) Save  4) Escape  5) Stealth  6) Charisma  7) Strength  "
        "8) Magic  9) Will" in output
    )
    assert "Save vs L4: rolled 3. Failure." in output


def skilled(content, *skills, faces=()):
    game = Game(dice=ScriptedDice([*EXPLORE, *faces]), content=content)
    game.create_character(life=8, sanity=8, food=3, skills=skills)
    return game


def test_a_roll_asks_about_the_skills_that_depend_on_it_and_names_each_modifier(content):
    # given Resilient; a save vs poison at -1 from a note; the die shows 4
    game = skilled(content, "skill.resilient", faces=[4])
    interface, output = terminal(
        game, [HOME_TOP_LEFT, "m", "1", "v", SAVE, "4", "y", "-1", RESOLVE, QUIT]
    )

    play(game, interface)

    assert interface._input.prompts[6] == (
        "Does this Save involve poison, infection or disease? (Resilient +1) [y/n] "
    )
    assert "Save vs L4: rolled 4, Resilient +1, modifier -1, total 4. Success." in output


def test_a_bonus_set_aside_is_shown(content):
    # Agile and Dodge do not stack: the higher applies, the other is shown set aside
    game = skilled(content, "skill.dodge", "skill.agile", faces=[3])
    game.character.skills["skill.dodge"] = SkillLevel.EXPERT
    interface, output = terminal(game, [HOME_TOP_LEFT, "m", "1", "v", "2", "5", "", RESOLVE, QUIT])

    play(game, interface)

    assert (
        "Defense vs L5: rolled 3, Dodge +2 (Agile +1 does not stack), total 5. Success." in output
    )


def test_a_wrong_answer_to_a_yes_or_no_is_asked_again(content):
    game = skilled(content, "skill.fighter", faces=[3])
    interface, output = terminal(
        game, [HOME_TOP_LEFT, "m", "1", "v", "1", "3", "maybe", "n", "", RESOLVE, QUIT]
    )

    play(game, interface)

    assert "Choose one of y, n." in output
    assert "Attack vs L3: rolled 3. Success." in output


def test_investigator_is_named_on_the_search(content):
    game = skilled(content, "skill.investigator", faces=[])
    game.dice = ScriptedDice([4])
    interface, output = terminal(game, [HOME_TOP_LEFT, "s", QUIT])

    play(game, interface)

    assert "Search: rolled 4, Investigator +1." in output


def test_marking_a_safe_house_takes_the_search_away(content):
    game = ready(content, *EXPLORE)
    interface, output = terminal(game, [HOME_TOP_LEFT, "m", "1", "h", RESOLVE, QUIT])

    play(game, interface)

    assert "This box is a Safe House." in output
    assert output[-2].startswith("m) move  a) apply an effect  q) quit")


def test_search_with_no_notes_rolls_at_once(content):
    # the Search die shows 3: Nothing found
    game = ready(content, 3)
    interface, output = terminal(game, [HOME_TOP_LEFT, "s", QUIT])

    play(game, interface)

    text = "\n".join(output)
    assert "Search: rolled 3." in text
    assert "Search table, rolled 3" in text
    assert "Nothing found." in text
    assert "Modifier (Enter for none): " not in interface._input.prompts


def test_notes_are_shown_and_asked_for_a_modifier(content):
    # the player writes a note, then Searches: the notes come back above the modifier
    game = ready(content, 4)
    lines = [HOME_TOP_LEFT, "a", "w", "cursed: -1 to Search", "b", "s", "-1", QUIT]
    interface, output = terminal(game, lines)

    play(game, interface)

    assert "Noted: cursed: -1 to Search" in output
    assert output.count("Notes: (1) box 1: cursed: -1 to Search") == 3  # menu, modifier, menu
    assert "w) write a note" in "\n".join(output)
    assert "Search: rolled 4, modifier -1." in output


def test_an_empty_note_is_asked_again(content):
    game = ready(content)
    interface, output = terminal(game, [HOME_TOP_LEFT, "a", "w", "  ", "cursed", "b", QUIT])

    play(game, interface)

    assert "Type some text." in output
    assert [note.text for note in game.character.notes] == ["cursed"]


def test_a_note_is_removed_by_its_number(content):
    game = ready(content)
    lines = [HOME_TOP_LEFT, "a", "w", "cursed", "w", "blessed", "x", "1", "b", QUIT]
    interface, output = terminal(game, lines)

    play(game, interface)

    assert "Note removed: cursed" in output
    assert [note.text for note in game.character.notes] == ["blessed"]


# --- Creation and XP (E6) ----------------------------------------------------------------------

CREATION_DICE = (5, 3, 4, 1, 1, 1, 3, 4)
"""A pistol with 7 bullets, a rope, a small bell, 4 Food."""
CREATING = ["Ann", "l", "2", "1", "19", "1", ""]
"""Ann; the points on Life and Sanity, 2 on Life; Agile (1), then Tough (19th, its number
on both lists); the knife (1); Enter after the recap (T2)."""


def test_a_player_creates_a_character_in_the_terminal(content):
    game = Game(dice=ScriptedDice(CREATION_DICE), content=content)
    interface, output = terminal(game, [*CREATING, HOME_TOP_LEFT, QUIT])

    play(game, interface)

    text = "\n".join(output)
    assert game.character.skills.keys() == {"skill.agile", "skill.tough"}
    # the choices are shown with what they mean
    assert "l) Share them between Life and Sanity" in text
    assert "1) Agile (8 XP): Add +1 to your Defense rolls" in text
    assert "  1) Knife" in output
    # what was taken, and the character sheet at the first turn
    assert "You take: Pistol (7)." in text
    # Tough: 2 more Life (E7)
    assert (
        "Ann · Box 1 · Life 12/12 · Sanity 9/9 · Food 4 (next meal: box 5) · XP 0 · Clues 0" in text
    )
    assert "Skills: Agile, Tough" in text
    assert "Items: Pistol (7), Knife, Rope, Small bell" in text


# --- Creation screens (T2) ----------------------------------------------------------------
# Feedback from the creation drill: each step says what it asks, and each answer what it gave.


def test_creation_says_what_each_step_asks(content):
    # given a new game in the terminal
    game = Game(dice=ScriptedDice(CREATION_DICE), content=content)
    interface, output = terminal(game, CREATING)

    # when the player creates Ann
    create(game, interface)

    # then an introduction, then each step under its heading, in order
    text = "\n".join(output)
    headings = [
        "Character creation",
        "Step 1 of 5 — Your name",
        "Step 2 of 5 — Your 3 extra points",
        "Step 3 of 5 — Choose 2 Skills",
        "Step 4 of 5 — Weapons",
        "Step 5 of 5 — Objects and Food",
    ]
    assert [line for line in output if line in headings] == headings
    assert "Give your character a name" in text
    assert "share them between Life and Sanity, or give all 3 up" in text
    assert "Arcane Skills cannot be taken at creation." in text
    assert "You also start with a knife, or a stick if you prefer." in text
    assert "anything you have already is rolled again" in text


def test_the_introduction_lists_the_steps(content):
    # given a new game in the terminal
    game = Game(dice=ScriptedDice(CREATION_DICE), content=content)
    interface, output = terminal(game, CREATING)

    # when the player creates Ann
    create(game, interface)

    # then the introduction lists the 5 steps, one per line, before the first heading
    start = output.index("It takes 5 steps to create your character:")
    assert output[start + 1 : start + 6] == [
        "1. Your name",
        "2. Your 3 extra points",
        "3. Your Skills",
        "4. Weapons",
        "5. Objects and Food",
    ]
    assert start < output.index("Step 1 of 5 — Your name")


def test_the_rolls_made_for_the_player_say_rolled(content):
    # given a new game in the terminal
    game = Game(dice=ScriptedDice(CREATION_DICE), content=content)
    interface, output = terminal(game, CREATING)

    # when the player creates Ann
    create(game, interface)

    # then the screens say the game rolls, not the player (T2 drill feedback)
    text = "\n".join(output)
    assert "(rolled twice if you traded your points for it)" in text
    assert "roll twice" not in text


def test_the_points_are_explained_and_their_result_shown(content):
    game = Game(dice=ScriptedDice(CREATION_DICE), content=content)
    interface, output = terminal(game, CREATING)

    create(game, interface)

    text = "\n".join(output)
    assert "l) Share them between Life and Sanity" in text
    assert "k) Trade them for a 3rd Skill" in text
    assert "u) Trade them for 1 more Useful Stuff roll" in text
    prompts = interface._input.prompts
    assert "How many of the 3 points go to Life? The rest go to Sanity. [0-3] " in prompts
    assert "→ Life 10, Sanity 9." in output


def test_points_traded_for_a_skill_ask_for_3(content):
    # given the points traded for a 3rd Skill: Agile, Tough, then Bow (its d6+3 arrows: 2)
    game = Game(dice=ScriptedDice((2, *CREATION_DICE)), content=content)
    interface, output = terminal(game, ["Ann", "k", "1", "19", "2", "1", ""])

    create(game, interface)

    assert "→ Life 8, Sanity 8, and a 3rd Skill." in output
    assert "Step 3 of 5 — Choose 3 Skills" in output
    assert "Skill 3 of 3? [1-22] " in interface._input.prompts


def test_the_skills_keep_their_numbers_and_the_taken_one_is_marked(content):
    game = Game(dice=ScriptedDice(CREATION_DICE), content=content)
    interface, output = terminal(game, CREATING)

    create(game, interface)

    # both lists have the texts and the same numbers
    assert interface._input.prompts[3:5] == ["Skill 1 of 2? [1-22] ", "Skill 2 of 2? [1-22] "]
    assert "→ Agile." in output
    assert "  1) (TAKEN) Agile (TAKEN)" in output
    tough = [line for line in output if line.startswith(" 19) Tough (8 XP): Add +2")]
    assert len(tough) == 2
    # r hides or shows the texts, on a line of its own under the list
    assert "  r) Hide the descriptions" in output
    assert "→ Tough." in output


def test_a_taken_skill_is_refused_and_r_hides_or_shows_the_texts(content):
    # given the player hides the texts on the first list, then shows them on the second
    game = Game(dice=ScriptedDice(CREATION_DICE), content=content)
    interface, output = terminal(game, ["Ann", "l", "2", "r", "1", "1", "r", "19", "1", ""])

    create(game, interface)

    assert "Agile is already taken." in output
    # the texts: on the first list, hidden on r and on the next list, then shown again on r
    bow = [line for line in output if line.startswith("  2) Bow (3 XP)")]
    assert [line == "  2) Bow (3 XP)" for line in bow] == [False, True, True, False]
    assert output.count("  r) Show the descriptions") == 3  # twice for the Skills, once after
    assert list(game.character.skills) == ["skill.agile", "skill.tough"]


def test_the_knife_or_stick_shows_what_they_share_once(content):
    game = Game(dice=ScriptedDice(CREATION_DICE), content=content)
    interface, output = terminal(game, CREATING)

    create(game, interface)

    question = output.index("Knife or stick: -1 to Attack rolls.")
    assert output[question + 1 : question + 3] == [
        "  1) Knife",
        "  2) Stick (you may pick up a stick every time you visit a park)",
    ]
    assert "Knife or stick? [1-2] " in interface._input.prompts


def test_two_weapons_of_different_headings_show_their_texts(content):
    # given Random Weapon 2: a chainsaw or an authentic samurai sword
    game = Game(dice=ScriptedDice((2, 1, 1, 1, 3, 4)), content=content)
    interface, output = terminal(game, ["Ann", "l", "2", "1", "19", "1", "1", ""])

    create(game, interface)

    assert any(line.startswith("  1) Chainsaw: ") for line in output)
    assert "Which weapon? [1-2] " in interface._input.prompts


def test_a_recap_shows_the_character_once_made(content):
    # given Ann created with a pistol, the knife, a rope, a small bell and 4 Food
    game = Game(dice=ScriptedDice(CREATION_DICE), content=content)
    interface, output = terminal(game, CREATING)

    create(game, interface)

    # then the character, one thing a line, names only, until the player goes on
    recap = output.index("Your character")
    assert output[recap - 1] == ""
    assert output[recap + 1 :] == [
        "  Ann · Food 4 · XP 0 · Clues 0",
        "    - Life 12/12",
        "    - Sanity 9/9",
        "  Skills:",
        "    - Agile",
        "    - Tough",
        "  Weapons:",
        "    - Pistol (7)",
        "    - Knife",
        "  Items:",
        "    - Rope",
        "    - Small bell",
        "  r) Show the descriptions",
    ]
    assert interface._input.prompts[-1] == "Press Enter to go on: "


def test_r_shows_the_descriptions_in_the_recap(content):
    game = Game(dice=ScriptedDice(CREATION_DICE), content=content)
    interface, output = terminal(game, [*CREATING[:-1], "r", ""])

    create(game, interface)

    assert (
        "    - Agile: Add +1 to your Defense rolls and rolls performed to climb, jump, or avoid "
        "danger."
    ) in output
    assert "    - Knife: -1 to Attack rolls." in output
    assert any(line.startswith("    - Rope: ") for line in output)
    assert output[-1] == "  r) Hide the descriptions"


BOOK_AT_CREATION = (5, 3, 4, 4, 5, 1, 3, 4)
"""A pistol, Random Objects 45 (a random book), a small bell, 4 Food."""
NOTING_THE_BOOK = [*CREATING[:-1], "w", "The Occult Guide", "d", ""]
"""Creating Ann; the book is written as a note, and its text leads nowhere else."""


def test_a_note_written_at_creation_shows_in_the_recap(content):
    game = Game(dice=ScriptedDice(BOOK_AT_CREATION), content=content)
    interface, output = terminal(game, NOTING_THE_BOOK)

    create(game, interface)

    assert output[-3:] == ["  Notes:", "    - The Occult Guide", "  r) Show the descriptions"]


def test_the_creation_drill_shows_the_character_once(content):
    game = Game(dice=ScriptedDice(CREATION_DICE), content=content)
    interface, output = terminal(game, CREATING)

    drills.run("creation", game, interface)

    assert output[-1] == "The drill is over."
    assert sum("Ann · " in line for line in output) == 1


def test_every_creation_text_is_used(content):
    # given one screen text shared by the plays above that cover every branch
    text = load_screen_text()
    plays = [
        (CREATION_DICE, ["Ann", "l", "2", "r", "1", "1", "r", "19", "1", "r", ""]),
        ((2, *CREATION_DICE), ["Ann", "k", "1", "19", "2", "1", ""]),
        ((2, 1, 1, 1, 3, 4), ["Ann", "l", "2", "1", "19", "1", "1", ""]),
        (BOOK_AT_CREATION, NOTING_THE_BOOK),
    ]
    for dice, lines in plays:
        game = Game(dice=ScriptedDice(dice), content=content)
        interface = TerminalInterface(game, Typist(lines), lambda line: None, text=text)
        create(game, interface)

    # then no creation text is left unused
    assert {key for key in text.keys if key.startswith("creation.")} - text.used == set()


def test_a_player_spends_xp_in_the_terminal(content):
    game = ready(content)
    game.gain("xp", 8)
    interface, output = terminal(game, [HOME_TOP_LEFT, "p", "1", QUIT])

    play(game, interface)

    text = "\n".join(output)
    assert "p) spend XP" in text
    assert "1) Agile: 8 XP" in text
    assert "You learn Agile: 8 XP spent." in text
    assert game.character.skills == {"skill.agile": "basic"}


def test_healing_at_max_says_so(content):
    game = ready(content, *EXPLORE)
    interface, output = terminal(game, [HOME_TOP_LEFT, "m", "1", "g", "1", "2", RESOLVE, QUIT])

    play(game, interface)

    assert "You are at your max Life (8)." in output


# --- Injuries and Mental Scars (E8) --------------------------------------------------------


def test_the_status_lists_injuries_and_mental_scars(content):
    game = ready(content)
    game.gain_injury("injury.limping")
    game.gain_mental_scar("mental_scar.eating_disorder")
    interface, output = terminal(game, [HOME_TOP_LEFT, QUIT])

    play(game, interface)

    assert "Injuries: Limping\nMental Scars: Eating Disorder" in "\n".join(output)


def test_a_modifier_from_an_injury_or_a_mental_scar_is_named_after_it(content):
    # their roll modifiers are written with E13; the name is ready for them
    interface, _ = terminal(ready(content), [])

    assert interface._source("injury.limping") == "Limping"
    assert interface._source("mental_scar.phobic") == "Phobic"
    assert interface._source("skill.agile") == "Agile"


# --- Moments and lasting effects (E8) --------------------------------------------------------


def test_a_lasting_effect_that_ends_is_told(content):
    # given -1 on all rolls for the next box, at Home; the player walks two boxes
    game = ready(content, *EXPLORE, NO_ENCOUNTER)
    game.choose_home(Position(0, 0))
    game.add_lasting(Effect(basic=-1), boxes=1)
    interface, output = terminal(game, ["m", "1", RESOLVE, "m", "1", QUIT])

    play(game, interface)

    # then it ends as box 3 starts
    assert output.index("Box 3.") < output.index("Ended: -1 on all rolls.")
    assert "Ended: -1 on all rolls." not in output[: output.index("Box 3.")]


def test_a_meal_is_told_after_the_arrival(content):
    # given Eating Disorder: a meal every 3 boxes
    game = ready(content, *EXPLORE, NO_ENCOUNTER)
    game.gain_mental_scar("mental_scar.eating_disorder")
    interface, output = terminal(game, [HOME_TOP_LEFT, "m", "1", RESOLVE, "m", "1", QUIT])

    play(game, interface)

    assert output[output.index("Box 3.") + 1] == "You eat 1 Food (Food 2)."


def test_the_status_shows_the_next_meal(content):
    # with Eating Disorder, the meal after Home comes at box 3
    game = ready(content)
    game.gain_mental_scar("mental_scar.eating_disorder")
    interface, output = terminal(game, [HOME_TOP_LEFT, QUIT])

    play(game, interface)

    status = "Box 1 · Life 8/8 · Sanity 8/8 · Food 3 (next meal: box 3) · XP 0 · Clues 0"
    assert status in "\n".join(output).splitlines()


def test_a_player_adds_a_lasting_effect_and_sees_it_in_the_status(content):
    # given painkillers at Home: -1 on all rolls for the next 3 boxes (f, 1 all rolls, -1, 3);
    # then +1 on Stealth until removed (Enter); the player removes the first one (u, 1)
    game = ready(content)
    lines = [HOME_TOP_LEFT, "a", "f", "1", "-1", "3", "f", "6", "1", "", "b"]
    interface, output = terminal(game, [*lines, "a", "u", "1", "b", QUIT])

    play(game, interface)

    text = "\n".join(output)
    assert "f) add a lasting effect" in text
    assert "1) All rolls  2) Attack  3) Defense  4) Save  5) Escape  6) Stealth" in text
    assert interface._input.prompts[5] == "For the next how many boxes? (Enter: until removed) "
    assert "Lasting effect: -1 on all rolls (ends at box 5)." in output
    assert "Lasting effect: +1 on Stealth rolls (until removed)." in output
    assert (
        "Lasting effects: -1 on all rolls (ends at box 5), +1 on Stealth rolls (until removed)"
        in text
    )
    assert "1) -1 on all rolls (ends at box 5)" in output
    assert "Removed: -1 on all rolls." in output
    assert game.character.lasting[0].effect == Effect(basic=1, roll=RollType.STEALTH)


# --- Drills (T1) ---------------------------------------------------------------------------


def test_a_drill_starts_with_what_to_try_and_asks_for_a_pregenerated_character(tmp_path):
    # given the walk drill: Douglas (2), Home, then quit
    typist = Typist(["2", HOME_TOP_LEFT, QUIT])
    output = []

    main(
        ["--drill", "walk", "--seed", "7", "--log-dir", str(tmp_path)],
        input_fn=typist,
        output_fn=output.append,
    )

    # then the drill says what to try, and the two sheets are listed with their numbers
    shown = "\n".join(output)
    assert "Drill walk: A pregenerated character at Home walks 10 boxes" in shown
    assert "1) Anna Miller: Life 10, Sanity 9, Food 4; Will, Occultist" in shown
    assert "2) Douglas Harrison: Life 11, Sanity 8, Food 4; Slippery, Strong" in shown
    assert "Which character? [1-2] " in typist.prompts
    assert "Douglas Harrison · Box 1" in shown
    [log_file] = tmp_path.glob("*.log")
    assert "drill walk" in log_file.read_text()


def test_a_drill_over_says_so_and_shows_the_character(tmp_path):
    # given the creation drill (seed 7 as above)
    typist = Typist(["Ann", "l", "2", "1", "18", "1", "1", ""])
    output = []

    main(
        ["--drill", "creation", "--seed", "7", "--log-dir", str(tmp_path)],
        input_fn=typist,
        output_fn=output.append,
    )

    # then once the character is made and shown (T2), the drill is over, with no Home
    assert "Your character" in output
    assert output[-1] == "The drill is over."
    assert typist.lines == []


def test_an_unknown_drill_is_refused_with_the_list(tmp_path, capsys):
    with pytest.raises(SystemExit):
        main(["--drill", "nothing", "--log-dir", str(tmp_path)], input_fn=Typist([]))
    assert "creation" in capsys.readouterr().err
