"""E4: the engine/interface protocol and the game loop (design/game-flow.md, Mission).

The engine asks, the interface answers: every choice is a `Choose` request whose answer must be
one of its options, and the engine tells the interface what happened. The loop: choose Home on
the first game, then each turn choose an action (move or quit) and, to move, a box. It ends at
death (Life 0), insanity (Sanity 0) or when the player quits.

Scenarios are played by a scripted interface that gives the answers in order.
"""

import logging

import pytest

from alone_against_fear.content import load_content
from alone_against_fear.dice import ScriptedDice
from alone_against_fear.engine import Arrival, Game, GameError, Position, Upkeep
from alone_against_fear.engine.loop import PLACEHOLDER_LIFE, PLACEHOLDER_SANITY, play
from alone_against_fear.engine.protocol import Action, Book, Choose, End, Ended, Topic
from alone_against_fear.engine.town import boxes_of
from alone_against_fear.interface.scripted import ScriptedInterface, ScriptError

HOME = Position(2, 2)
# Ten moves from Home, all on the first sheet: down, then back up the next column.
WALK = [
    Position(2, 3),
    Position(2, 4),
    Position(2, 5),
    Position(3, 5),
    Position(3, 4),
    Position(3, 3),
    Position(3, 2),
    Position(3, 1),
    Position(3, 0),
    Position(2, 0),
]


@pytest.fixture(scope="module")
def content():
    return load_content()


def new_game(content, *faces):
    return Game(dice=ScriptedDice(faces), content=content)


EXPLORE = (3, 3, 4)
"""A new box: Town Exploration 6 (3 and 3) sends to the Street table, whose d6 shows 4."""
WALK_DICE = EXPLORE * len(WALK)
"""Every box of the walk is new."""


def moves(*positions):
    """The answers of a turn spent moving to a new box, for each position: the Street table
    is not copied yet, so the player says its text leads nowhere else."""
    answers = []
    for position in positions:
        answers += [Action.MOVE, position, Book.DONE]
    return answers


# --- Scenario: a first game, ten boxes walked ----------------------------------------------


def test_a_scripted_player_walks_ten_boxes_and_quits(content):
    # given a new game, whose placeholder character rolls 3 Food
    game = new_game(content, 3, *WALK_DICE)
    interface = ScriptedInterface([HOME, *moves(*WALK), Action.QUIT])

    # when the player chooses Home, moves ten times and quits
    end = play(game, interface)

    # then the game ended because the player quit, eleven boxes numbered on the clock
    assert end is End.QUIT
    assert game.campaign.box_counter == 11
    assert game.campaign.position == WALK[-1]
    # and the Food upkeep ran on boxes 5 and 10
    assert game.character.food == 1
    # and every answer was used
    assert interface.remaining == 0


def test_the_interface_is_told_every_arrival_then_the_end(content):
    # given a new game with 3 Food
    game = new_game(content, 3, *WALK_DICE)
    interface = ScriptedInterface([HOME, *moves(*WALK), Action.QUIT])

    # when the player walks ten boxes and quits
    play(game, interface)

    # then the interface heard of Home, each box entered in order, then the end
    arrivals = [event for event in interface.told if isinstance(event, Arrival)]
    assert [arrival.position for arrival in arrivals] == [HOME, *WALK]
    assert [arrival.number for arrival in arrivals] == list(range(1, 12))
    assert [arrival.upkeep for arrival in arrivals if arrival.upkeep] == [Upkeep.ATE] * 2
    assert arrivals[4].upkeep is arrivals[9].upkeep is Upkeep.ATE  # boxes 5 and 10
    assert interface.told[-1] == Ended(End.QUIT)


# --- The starting character -----------------------------------------------------------------


def test_a_new_game_starts_with_the_placeholder_character(content):
    # given a new game whose Food die shows 4
    game = new_game(content, 4)

    # when the player chooses Home and quits at once
    play(game, ScriptedInterface([HOME, Action.QUIT]))

    # then the character has the base Life and Sanity, d6 Food and no items
    assert (game.character.life, game.character.sanity) == (8, 8)
    assert (PLACEHOLDER_LIFE, PLACEHOLDER_SANITY) == (8, 8)
    assert game.character.food == 4
    assert game.character.items == []


def test_a_game_that_has_a_character_keeps_it(content):
    # given a game whose character already exists
    game = new_game(content)
    game.create_character(life=11, sanity=8, food=2)

    # when the game is played
    play(game, ScriptedInterface([HOME, Action.QUIT]))

    # then no placeholder replaces it (and no Food die is rolled)
    assert (game.character.life, game.character.food) == (11, 2)


# --- What the engine asks -------------------------------------------------------------------


def test_home_is_chosen_among_the_boxes_of_the_first_sheet(content):
    game = new_game(content, 3)
    interface = ScriptedInterface([HOME, Action.QUIT])

    play(game, interface)

    first = interface.asked[0]
    assert first.topic is Topic.HOME
    assert set(first.options) == set(boxes_of(Position(0, 0)))
    assert game.campaign.home == HOME


def test_each_turn_offers_move_and_quit(content):
    game = new_game(content, 3)
    interface = ScriptedInterface([HOME, Action.QUIT])

    play(game, interface)

    # and Search while the box has not been Searched, apply an effect (E5b)
    assert interface.asked[1] == Choose(
        Topic.ACTION, (Action.MOVE, Action.SEARCH, Action.APPLY, Action.QUIT)
    )


def test_moving_offers_the_boxes_the_engine_allows(content):
    game = new_game(content, 3, *EXPLORE)
    interface = ScriptedInterface([HOME, *moves(WALK[0]), Action.QUIT])

    play(game, interface)

    move = interface.asked[2]
    assert move.topic is Topic.MOVE
    assert set(move.options) == _neighbours_of_home()


def _neighbours_of_home():
    return {
        Position(HOME.column + dc, HOME.row + dr)
        for dc in (-1, 0, 1)
        for dr in (-1, 0, 1)
        if (dc, dr) != (0, 0)
    }


def test_a_game_already_under_way_does_not_ask_for_home_again(content):
    # given a campaign whose character stands Home
    game = new_game(content)
    game.create_character(life=8, sanity=8, food=3)
    game.choose_home(HOME)

    # when the game is played again
    interface = ScriptedInterface([Action.QUIT])
    play(game, interface)

    # then the first request is the turn's action, not Home
    assert interface.asked[0].topic is Topic.ACTION


def test_an_answer_that_is_not_an_option_is_refused(content):
    game = new_game(content, 3)
    far_away = Position(4, 5)

    with pytest.raises(GameError):
        play(game, ScriptedInterface([HOME, Action.MOVE, far_away]))


def test_a_scripted_interface_out_of_answers_says_so(content):
    game = new_game(content, 3)

    with pytest.raises(ScriptError):
        play(game, ScriptedInterface([HOME]))


def test_every_answer_is_logged(content, caplog):
    game = new_game(content, 3, *EXPLORE)
    caplog.set_level(logging.INFO, logger="alone_against_fear")

    play(game, ScriptedInterface([HOME, *moves(WALK[0]), Action.QUIT]))

    answers = [r.getMessage() for r in caplog.records if r.getMessage().startswith("answer")]
    assert answers == [
        "answer home: (2, 2)",
        "answer action: move",
        "answer move: (2, 3)",
        "answer book: done",
        "answer action: quit",
    ]


# --- How a game ends ---------------------------------------------------------------------------


def test_starving_to_death_ends_the_game(content):
    # given a character with 1 Life and no Food, standing Home
    game = new_game(content, *EXPLORE * 3)
    game.create_character(life=1, sanity=8, food=0)
    game.choose_home(HOME)
    interface = ScriptedInterface([*moves(*WALK[:3]), Action.MOVE, WALK[3]])

    # when the player walks to box 5, where the Food upkeep costs 1 Life
    end = play(game, interface)

    # then the character is dead, the box is not explored and the engine asks nothing more
    assert end is End.DEAD
    assert game.character.life == 0
    assert interface.remaining == 0
    assert interface.told[-1] == Ended(End.DEAD)


def test_a_character_at_zero_sanity_is_insane(content):
    # given a character whose Sanity went to 0
    game = new_game(content)
    game.create_character(life=8, sanity=1, food=3)
    game.choose_home(HOME)
    game.lose("sanity", 1)
    interface = ScriptedInterface([])

    # when the game is played
    end = play(game, interface)

    # then it ends at once: the character is insane
    assert end is End.INSANE
    assert interface.asked == []
    assert interface.told == [Ended(End.INSANE)]


def test_death_comes_before_insanity(content):
    game = new_game(content)
    game.create_character(life=0, sanity=0, food=3)
    game.choose_home(HOME)

    assert play(game, ScriptedInterface([])) is End.DEAD
