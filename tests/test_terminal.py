"""E4: the minimal terminal interface.

It shows the character, the map and each request with numbered options, reads the player's
choice and checks it before answering; it narrates what the engine tells it. It reads the game
state to show it, and changes it only through its answers. Input and output are passed in, so a
test plays the terminal with typed lines.
"""

import pytest

from alone_against_fear.content import load_content
from alone_against_fear.dice import ScriptedDice
from alone_against_fear.engine import Game, Position
from alone_against_fear.engine.loop import play
from alone_against_fear.engine.protocol import End
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


# Options are numbered from 1 in reading order (row by row). Home in the top-left box is
# option 1; from there the box to the right is option 1, and from that box the top-left box is
# option 1 again. Each turn: 1 to move, 2 to quit.
HOME_TOP_LEFT = "1"
BACK_AND_FORTH = ["1", "1"]
QUIT = "2"


def test_a_player_walks_ten_boxes_in_the_terminal(content):
    # given a new game played in the terminal
    game = Game(dice=ScriptedDice([3]), content=content)
    interface, output = terminal(game, [HOME_TOP_LEFT, *BACK_AND_FORTH * 10, QUIT])

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
    game = Game(dice=ScriptedDice([3]), content=content)
    interface, output = terminal(game, [HOME_TOP_LEFT, "1", "1", QUIT])

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
    typist = Typist([HOME_TOP_LEFT, "1", "1", QUIT])
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
