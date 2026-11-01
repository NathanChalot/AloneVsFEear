"""E4: the minimal terminal interface.

It shows the character, the map and each request with numbered options, reads the player's
choice and checks it before answering; it narrates what the engine tells it. It reads the game
state to show it, and changes it only through its answers. Input and output are passed in, so a
test plays the terminal with typed lines.
"""

import pytest

from alone_against_fear.content import load_content
from alone_against_fear.dice import ScriptedDice
from alone_against_fear.engine import Game, Position, book_mode
from alone_against_fear.engine.loop import play
from alone_against_fear.engine.protocol import End
from alone_against_fear.engine.town import boxes_of
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
    # given a new game played in the terminal: Food 3, one new box, then nine visited ones
    game = Game(dice=ScriptedDice([3, *EXPLORE, *[NO_ENCOUNTER] * 9]), content=content)
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
    game = Game(dice=ScriptedDice([3, *EXPLORE]), content=content)
    interface, output = terminal(game, [HOME_TOP_LEFT, *FIRST_MOVE, QUIT])

    play(game, interface)

    text = "\n".join(output)
    assert "@" in text  # where the character stands
    assert "[1]" in text  # an option on the map


def test_a_wrong_choice_is_asked_again(content):
    game = Game(dice=ScriptedDice([3]), content=content)
    typist = Typist(["x", "99", HOME_TOP_LEFT, QUIT])
    output = []
    interface = TerminalInterface(game, input_fn=typist, output_fn=output.append)

    play(game, interface)

    assert game.campaign.home == Position(0, 0)
    assert sum("choose" in line.lower() for line in output) >= 2


def test_ending_the_input_quits(content):
    # Ctrl-D (end of input) is the same as choosing to quit
    game = Game(dice=ScriptedDice([3]), content=content)
    interface, _ = terminal(game, [HOME_TOP_LEFT])

    assert play(game, interface) is End.QUIT


def test_main_writes_the_log_to_a_file_with_the_seed_and_the_answers(tmp_path):
    typist = Typist([HOME_TOP_LEFT, QUIT])
    output = []

    code = main(
        ["--seed", "7", "--log-dir", str(tmp_path)], input_fn=typist, output_fn=output.append
    )

    assert code == 0
    [log_file] = tmp_path.glob("*.log")
    log = log_file.read_text()
    assert "dice seed 7" in log
    assert "answer home: (0, 0)" in log
    assert "answer action: quit" in log


def test_the_free_actions_have_letters(content):
    game = Game(dice=ScriptedDice([3]), content=content)
    interface, output = terminal(game, [HOME_TOP_LEFT, QUIT])

    play(game, interface)

    assert "m) move  s) search  a) apply an effect  q) quit" in output


# --- Resolving a box -------------------------------------------------------------------------


def test_a_new_box_shows_its_entry_and_your_choice(content):
    # given a new box whose 2d6 show 3 and 5: Town Exploration 8; then the Street's d6 shows 4
    game = Game(dice=ScriptedDice([3, 3, 5, 4]), content=content)
    interface, output = terminal(game, [HOME_TOP_LEFT, "m", "1", "2", RESOLVE, QUIT])

    play(game, interface)

    text = "\n".join(output)
    assert "Town Exploration table: 8" in text
    assert "Roll on the Store table or the Street table, your choice." in text
    # and only the entry reached: not entry 9
    assert "Sewers" not in text.split("Town Exploration table: 8")[1]
    # and the choice offers the two tables only
    assert "1) Store table  2) Street table" in text
    assert "Street table: 4" in text


def test_a_die_rolled_by_an_entry_is_shown(content):
    game = Game(dice=ScriptedDice([3, *EXPLORE]), content=content)
    interface, output = terminal(game, [HOME_TOP_LEFT, *FIRST_MOVE, QUIT])

    play(game, interface)

    assert "  Rolled 4: House table" in output


def test_a_table_not_copied_yet_points_to_its_source_and_asks_where_it_leads(content):
    game = Game(dice=ScriptedDice([3, *EXPLORE]), content=content)
    interface, output = terminal(game, [HOME_TOP_LEFT, *FIRST_MOVE, QUIT])

    play(game, interface)

    text = "\n".join(output)
    assert "House table: 2" in text
    assert "read entry 2 in gameRules/tables/places/5_7_house_table.md" in text
    assert "t) a table  e) a numbered event  g) gain  l) lose  v) roll vs L" in text


def test_a_table_s_rules_are_shown_the_first_time_then_on_request(content):
    # given two new boxes in a row, along the top row (from the second box, option 2 is new)
    game = Game(dice=ScriptedDice([3, *EXPLORE, *EXPLORE]), content=content)
    lines = [HOME_TOP_LEFT, *FIRST_MOVE, "m", "2", "r", RESOLVE, QUIT]
    interface, output = terminal(game, lines)

    play(game, interface)

    rules = [line for line in output if "every time you move into an unexplored area" in line]
    # once on the first roll, once more on request; not on the second roll
    assert len(rules) == 2
    second_roll = max(i for i, line in enumerate(output) if line == "Town Exploration table: 7")
    asked = [i for i, line in enumerate(output) if "every time you move" in line][-1]
    assert output[second_roll + 1].startswith("  Roll d6.")  # the entry, without the rules
    assert asked > second_roll


def test_an_entry_shows_the_notes_it_points_to(content):
    # given Town Exploration 2 (1 and 1), then Random Encounter 6 then 1: the Unique Vampires,
    # whose d6 shows 3
    game = Game(dice=ScriptedDice([3, 1, 1, 6, 1, 3]), content=content)
    interface, output = terminal(game, [HOME_TOP_LEFT, "m", "1", RESOLVE, QUIT])

    play(game, interface)

    text = "\n".join(output)
    assert "Random Encounter table: 6, then 1" in text
    assert "Note: When rolling on tables of Unique creatures" in text
    assert "Unique Vampires table: 3" in text


def test_the_text_can_lead_to_any_table_and_any_event(content):
    # given Town Exploration 6 (3 and 3): the Street, whose d6 shows 4; its text sends the
    # player to the Undead table (d6: 2), then to event #12
    game = Game(dice=ScriptedDice([3, 3, 3, 4, 2]), content=content)
    undead = str(table_names(content).index("Undead table") + 1)
    lines = [HOME_TOP_LEFT, "m", "1", "t", undead, "e", "12", RESOLVE, QUIT]
    interface, output = terminal(game, lines)

    play(game, interface)

    text = "\n".join(output)
    assert "Undead table: 2" in text
    assert "Event #12, The sewer people: read it in gameRules/6_unique_events.md" in text


def table_names(content):
    """The table names in the order "a table" lists them."""
    game = Game(dice=ScriptedDice([]), content=content)
    names = {**content.tables, **content.catalogue}
    return [names[id_].name for id_ in book_mode.tables(game)]


def test_a_visited_box_says_whether_an_encounter_came(content):
    game = Game(dice=ScriptedDice([3, *EXPLORE, NO_ENCOUNTER]), content=content)
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
    assert "Town Exploration table: 7" in text


# --- Manual actions (E5b) --------------------------------------------------------------------


def test_the_player_applies_an_entry_with_manual_actions(content):
    # given the House's entry, not copied yet: the player loses 2 Sanity, then leaves it
    game = Game(dice=ScriptedDice([3, *EXPLORE]), content=content)
    interface, output = terminal(game, [HOME_TOP_LEFT, "m", "1", "l", "2", "2", RESOLVE, QUIT])

    play(game, interface)

    text = "\n".join(output)
    assert "1) Life  2) Sanity  3) Food" in text
    assert "You lose 2 Sanity (Sanity 6)." in text
    assert game.character.sanity == 6


def test_a_wrong_number_is_asked_again(content):
    game = Game(dice=ScriptedDice([3, *EXPLORE]), content=content)
    lines = [HOME_TOP_LEFT, "m", "1", "g", "5", "two", "0", "1", RESOLVE, QUIT]
    interface, output = terminal(game, lines)

    play(game, interface)

    assert output.count("Type a whole number, 1 or more.") == 2
    assert game.character.clues == 1


def test_a_roll_vs_l_shows_the_die_and_the_result(content):
    # the die shows 3; L4 with no modifier (Enter)
    game = Game(dice=ScriptedDice([3, *EXPLORE, 3]), content=content)
    interface, output = terminal(game, [HOME_TOP_LEFT, "m", "1", "v", "4", "", RESOLVE, QUIT])

    play(game, interface)

    assert "Roll vs L4: rolled 3. Failure." in output


def test_marking_a_safe_house_takes_the_search_away(content):
    game = Game(dice=ScriptedDice([3, *EXPLORE]), content=content)
    interface, output = terminal(game, [HOME_TOP_LEFT, "m", "1", "h", RESOLVE, QUIT])

    play(game, interface)

    assert "This box is a Safe House." in output
    assert output[-2].startswith("m) move  a) apply an effect  q) quit")


def test_search_with_no_notes_rolls_at_once(content):
    # the Search die shows 3: Nothing found
    game = Game(dice=ScriptedDice([3, 3]), content=content)
    interface, output = terminal(game, [HOME_TOP_LEFT, "s", QUIT])

    play(game, interface)

    text = "\n".join(output)
    assert "Search: rolled 3." in text
    assert "Search table: 3" in text
    assert "Nothing found." in text
    assert "Modifier (Enter for none): " not in interface._input.prompts


def test_notes_are_shown_and_asked_for_a_modifier(content):
    # the player writes a note, then Searches: the notes come back above the modifier
    game = Game(dice=ScriptedDice([3, 4]), content=content)
    lines = [HOME_TOP_LEFT, "a", "w", "cursed: -1 to Search", "b", "s", "-1", QUIT]
    interface, output = terminal(game, lines)

    play(game, interface)

    assert "Noted: cursed: -1 to Search" in output
    assert output.count("Notes: (1) box 1: cursed: -1 to Search") == 3  # menu, modifier, menu
    assert "w) write a note" in "\n".join(output)
    assert "Search: rolled 4, -1." in output


def test_an_empty_note_is_asked_again(content):
    game = Game(dice=ScriptedDice([3]), content=content)
    interface, output = terminal(game, [HOME_TOP_LEFT, "a", "w", "  ", "cursed", "b", QUIT])

    play(game, interface)

    assert "Type some text." in output
    assert [note.text for note in game.character.notes] == ["cursed"]


def test_a_note_is_removed_by_its_number(content):
    game = Game(dice=ScriptedDice([3]), content=content)
    lines = [HOME_TOP_LEFT, "a", "w", "cursed", "w", "blessed", "x", "1", "b", QUIT]
    interface, output = terminal(game, lines)

    play(game, interface)

    assert "Note removed: cursed" in output
    assert [note.text for note in game.character.notes] == ["blessed"]
