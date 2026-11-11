"""T1: feedback written while playing. A line starting with # at any prompt is a feedback note:
it is kept with the seed, the drill and the box number, so the moment can be found in the log,
then the same question is asked again. Notes are triaged at the next review or playtest."""

from alone_against_fear.content import load_content
from alone_against_fear.dice import ScriptedDice
from alone_against_fear.engine import Game, Position
from alone_against_fear.engine.loop import play
from alone_against_fear.interface.feedback import FeedbackLog
from alone_against_fear.interface.terminal import TerminalInterface, main

CONTENT = load_content()
HOME_TOP_LEFT = "1"
QUIT = "q"


class Typist:
    def __init__(self, lines):
        self.lines = list(lines)
        self.prompts = []

    def __call__(self, prompt=""):
        self.prompts.append(prompt)
        if not self.lines:
            raise EOFError
        return self.lines.pop(0)


def ready():
    game = Game(dice=ScriptedDice([]), content=CONTENT)
    game.create_character(life=8, sanity=8, food=3, name="Ann")
    return game


def test_a_feedback_note_is_kept_and_the_question_asked_again(tmp_path):
    # given a game at Home, with feedback kept in a file
    game = ready()
    path = tmp_path / "feedback.md"
    feedback = FeedbackLog(path, seed=7, drill="walk", log_file="logs/x.log")
    typist = Typist([HOME_TOP_LEFT, "# the map is hard to read", QUIT])
    output = []

    # when the player types a note at the action prompt, then quits
    play(game, TerminalInterface(game, typist, output.append, feedback=feedback))

    # then the note is kept with where it was written
    text = path.read_text()
    assert "drill walk · seed 7 · box 1" in text
    assert "- Character: Ann" in text
    assert "- Asked: What do you do?" in text
    assert "- Log: logs/x.log" in text
    assert "the map is hard to read" in text
    # and the same question was asked again
    assert typist.prompts[-2:] == ["What do you do? ", "What do you do? "]
    assert "Feedback saved." in output
    assert game.campaign.position == Position(0, 0)


def test_feedback_works_at_number_and_text_prompts(tmp_path):
    # given creation: the name, then the points on Life and Sanity
    game = Game(dice=ScriptedDice([]), content=CONTENT)
    path = tmp_path / "feedback.md"
    feedback = FeedbackLog(path, seed=1, drill=None, log_file="l.log")
    typist = Typist(["# what name?", "Ann", "l", "# how many?"])

    play(game, TerminalInterface(game, typist, lambda line: None, feedback=feedback))

    # then both notes are kept, before any character exists, with no drill
    text = path.read_text()
    assert text.count("seed 1 · box 0") == 2
    assert "drill" not in text.split("\n## ", 1)[1]
    assert "what name?" in text and "how many?" in text
    assert "- Character: none yet" in text


def test_notes_are_appended_under_a_heading(tmp_path):
    path = tmp_path / "feedback" / "feedback.md"
    feedback = FeedbackLog(path, seed=3, drill=None, log_file="l.log")
    game = ready()

    feedback.write(game, "What do you do? ", "first")
    feedback.write(game, "What do you do? ", "second")

    text = path.read_text()
    assert text.startswith("# Feedback")
    assert text.count("\n## ") == 2
    assert text.index("first") < text.index("second")


def test_without_a_feedback_file_a_note_is_not_an_answer():
    game = ready()
    typist = Typist([HOME_TOP_LEFT, "# hello", QUIT])
    output = []

    play(game, TerminalInterface(game, typist, output.append))

    assert "No feedback file in this game." in output


def test_main_keeps_feedback_with_the_seed_and_the_log_file(tmp_path):
    path = tmp_path / "notes.md"
    typist = Typist(["1", HOME_TOP_LEFT, "# odd wording", QUIT])
    output = []

    main(
        [
            "--drill",
            "walk",
            "--seed",
            "7",
            "--log-dir",
            str(tmp_path),
            "--feedback-file",
            str(path),
        ],
        input_fn=typist,
        output_fn=output.append,
    )

    [log_file] = tmp_path.glob("*.log")
    text = path.read_text()
    assert "drill walk · seed 7 · box 1" in text
    assert f"- Log: {log_file}" in text
    assert "feedback at box 1: odd wording" in log_file.read_text()
    assert any("Type # and a note at any prompt" in line for line in output)
