"""E5a: book mode, reading (design/mvp-scope.md, Book mode; design/game-flow.md, Mission).

A turn: move, arrive, then free actions. Arriving rolls the table the rules call for (Town
Exploration in a new box, a 1 in 6 chance of a Random Encounter in a visited one) and resolves
the box before anything else: each entry reached leads on as its text says, until it leads
nowhere. A copied entry the engine knows how to follow plays itself: it rolls on the table it
names, asks when the text gives a choice, rolls the die when the text rolls one. A table not
copied yet is still rolled, but only the player can read where its entry leads: the engine asks
(a table, a numbered event, or nowhere else). Everything reached is recorded, and a place table
rolled in a box is a place of that box. The free actions are moving, attaching a new sheet
once one is full, and quitting.

Scenarios are played by a scripted interface; the dice show the faces given.
"""

import random

import pytest

from alone_against_fear.content import load_content
from alone_against_fear.dice import RandomDice, ScriptedDice
from alone_against_fear.engine import Arrival, Game, GameError, Happened, Level, Position
from alone_against_fear.engine.game import Rolled
from alone_against_fear.engine.leads import LEADS, Auto, Choice, DieRoll
from alone_against_fear.engine.loop import play
from alone_against_fear.engine.manual import Manual
from alone_against_fear.engine.protocol import (
    Action,
    Book,
    Choose,
    EventPlayed,
    LeadRolled,
    Number,
    Quit,
    SheetAttached,
    Text,
    Topic,
    Wandering,
)
from alone_against_fear.engine.town import boxes_of
from alone_against_fear.interface.scripted import ScriptedInterface

HOME = Position(2, 2)
EAST = Position(3, 2)
FOOD = 3
"""The placeholder character's Food die."""


@pytest.fixture(scope="module")
def content():
    return load_content()


def new_game(content, *faces):
    return Game(dice=ScriptedDice([FOOD, *faces]), content=content)


def game_with_character(content, *faces):
    """A game whose character exists already: no Food die is rolled."""
    game = Game(dice=ScriptedDice(faces), content=content)
    game.create_character(life=8, sanity=8, food=3)
    return game


def rolled(interface):
    return [event for event in interface.told if isinstance(event, Rolled)]


def asked(interface, topic):
    return [request for request in interface.asked if request.topic is topic]


def explore_east(*answers):
    """Home, then a move to the new box east of it, with the answers its resolution needs,
    then quit."""
    return [HOME, Action.MOVE, EAST, *answers, Action.QUIT]


# --- Scenario: a new box rolls Town Exploration and resolves it ------------------------------


def test_entering_a_new_box_rolls_town_exploration(content):
    # given a new box whose 2d6 show 3 and 5 (entry 8: Store or Street); then the Street's
    # d6 shows 4 and its text leads nowhere else
    game = new_game(content, 3, 5, 4)
    interface = ScriptedInterface(explore_east("table.street", Book.DONE))

    # when the player moves to the new box
    play(game, interface)

    # then the interface is told the box, then the Town Exploration entry 8
    arrival = interface.told.index(Arrival(EAST, 2, new=True))
    assert interface.told[arrival + 1] == Rolled(
        "table.town_exploration", (8,), "table.town_exploration.8"
    )
    # and the entry is recorded as played, for the campaign and the character
    assert game.history(Level.CAMPAIGN).has(Happened.PLAYED, "table.town_exploration.8")
    assert game.history(Level.CHARACTER).has(Happened.PLAYED, "table.town_exploration.8")


def test_home_rolls_nothing(content):
    game = new_game(content)
    interface = ScriptedInterface([HOME, Action.QUIT])

    play(game, interface)

    assert interface.told[0] == Arrival(HOME, 1, new=True)
    assert rolled(interface) == []


def test_your_choice_offers_only_the_tables_named(content):
    # given Town Exploration 8: "the Store table or the Street table, your choice"
    game = new_game(content, 3, 5, 4)
    interface = ScriptedInterface(explore_east("table.store", Book.DONE))

    play(game, interface)

    # then the player chose between the two tables only, before any free action
    assert interface.asked[3] == Choose(Topic.CHOICE, ("table.store", "table.street"))
    assert rolled(interface)[-1] == Rolled("table.store", (4,), None)


def test_a_single_table_is_rolled_without_asking(content):
    # given Town Exploration 6 (3 and 3): "Roll on Street table"; the Street's d6 shows 2
    game = new_game(content, 3, 3, 2)
    interface = ScriptedInterface(explore_east(Book.DONE))

    play(game, interface)

    assert [r.table_id for r in rolled(interface)] == ["table.town_exploration", "table.street"]
    assert asked(interface, Topic.CHOICE) == []


def test_the_engine_rolls_the_die_an_entry_rolls(content):
    # given Town Exploration 7 (3 and 4): "Roll d6. On a 1-5, House. On a 6, Special Events."
    # the d6 shows 6, then the Special Events table's d6 shows 1
    game = new_game(content, 3, 4, 6, 1)
    interface = ScriptedInterface(explore_east(Book.DONE))

    play(game, interface)

    assert LeadRolled("table.town_exploration.7", 6, "table.special_events") in interface.told
    assert rolled(interface)[-1] == Rolled("table.special_events", (1,), None)


def test_town_exploration_7_leads_to_the_house_on_1_to_5(content):
    game = new_game(content, 3, 4, 5, 1)
    interface = ScriptedInterface(explore_east(Book.DONE))

    play(game, interface)

    assert rolled(interface)[-1].table_id == "table.house"


def test_a_nested_table_is_rolled_down_to_its_entry_and_followed(content):
    # given Town Exploration 2 (1 and 1): "Roll on the Random Encounter table"; its dice show
    # 3 then 6 (the Unique Vampires), whose d6 shows 2
    game = new_game(content, 1, 1, 3, 6, 2)
    interface = ScriptedInterface(explore_east(Book.DONE))

    play(game, interface)

    assert rolled(interface) == [
        Rolled("table.town_exploration", (2,), "table.town_exploration.2"),
        Rolled("table.random_encounter", (3, 6), "table.random_encounter.3.6"),
        Rolled("table.unique_vampires", (2,), None),
    ]
    # Random Encounter and the creatures are not places
    assert game.campaign.map.boxes[EAST].places == []


def test_a_table_not_copied_yet_asks_where_its_text_leads(content):
    # given the Street's d6 shows 4: the engine cannot read its entry
    game = new_game(content, 3, 3, 4)
    interface = ScriptedInterface(explore_east(Book.DONE))

    play(game, interface)

    # then its roll is told with no entry, and the player says where the text leads
    assert rolled(interface)[-1] == Rolled("table.street", (4,), None)
    [book] = asked(interface, Topic.BOOK)
    assert book.options[:2] == (Book.TABLE, Book.EVENT)
    assert book.options[-1] is Book.DONE  # the manual actions in between (E5b)
    # and the Street is a place of this box
    assert game.campaign.map.boxes[EAST].places == ["table.street"]


def test_the_text_of_a_table_not_copied_yet_can_lead_to_any_table(content):
    # given the Street's entry sends the player to the Undead table, whose d6 shows 2
    game = new_game(content, 3, 3, 4, 2)
    interface = ScriptedInterface(explore_east(Book.TABLE, "table.undead", Book.DONE))

    play(game, interface)

    # then every table was offered, copied or not, and the box goes on until nowhere else
    [choose] = asked(interface, Topic.TABLE)
    assert {"table.town_exploration", "table.undead", "table.random_book"} <= set(choose.options)
    assert rolled(interface)[-1] == Rolled("table.undead", (2,), None)
    assert len(asked(interface, Topic.BOOK)) == 2


def test_the_text_of_a_table_not_copied_yet_can_lead_to_a_numbered_event(content):
    game = new_game(content, 3, 3, 4)
    interface = ScriptedInterface(explore_east(Book.EVENT, "event.12", Book.DONE))

    play(game, interface)

    [choose] = asked(interface, Topic.EVENT)
    assert choose.options == tuple(f"event.{n}" for n in range(1, 43))
    assert EventPlayed("event.12") in interface.told
    assert game.history(Level.CAMPAIGN).count(Happened.PLAYED, "event.12") == 1
    assert game.history(Level.CHARACTER).count(Happened.PLAYED, "event.12") == 1
    # an event not copied yet is read in its source: the player says where it leads
    assert len(asked(interface, Topic.BOOK)) == 2


def test_free_actions_come_only_once_the_box_is_resolved(content):
    game = new_game(content, 3, 3, 4)
    interface = ScriptedInterface(explore_east(Book.DONE))

    play(game, interface)

    # the turn's actions: Home, then after the box east was resolved; never in between
    topics = [request.topic for request in interface.asked]
    assert topics == [Topic.HOME, Topic.ACTION, Topic.MOVE, Topic.BOOK, Topic.ACTION]
    assert interface.asked[-1].topic is Topic.ACTION


# --- Scenario: a visited box has a 1 in 6 Random Encounter -----------------------------------


def test_a_visited_box_has_no_encounter_on_2_to_6(content):
    # given a new box east of Home (Street, entry 4), then back Home: the die shows 2
    game = new_game(content, 3, 3, 4, 2)
    interface = ScriptedInterface(
        [HOME, Action.MOVE, EAST, Book.DONE, Action.MOVE, HOME, Action.QUIT]
    )

    play(game, interface)

    # then Home was entered again, nothing came, and the free actions followed
    assert Arrival(HOME, 3, new=False) in interface.told
    assert interface.told[interface.told.index(Arrival(HOME, 3)) + 1] == Wandering(2, False)
    assert len(rolled(interface)) == 2


def test_a_visited_box_has_a_random_encounter_on_1(content):
    # given back Home: the die shows 1, then Random Encounter rolls 5 and 2 (the Ghosts
    # table), whose d6 shows 3
    game = new_game(content, 3, 3, 4, 1, 5, 2, 3)
    interface = ScriptedInterface(
        [HOME, Action.MOVE, EAST, Book.DONE, Action.MOVE, HOME, Book.DONE, Action.QUIT]
    )

    play(game, interface)

    after = interface.told[interface.told.index(Arrival(HOME, 3)) + 1 :]
    assert after[:3] == [
        Wandering(1, True),
        Rolled("table.random_encounter", (5, 2), "table.random_encounter.5.1-5"),
        Rolled("table.ghosts", (3,), None),
    ]


# --- How the copied entries lead on ----------------------------------------------------------


def test_every_lead_names_the_tables_of_its_entry(content):
    for entry_id, lead in LEADS.items():
        assert set(lead.refs) == set(content.entry(entry_id).refs), entry_id


def test_every_entry_of_the_arrival_tables_has_a_lead(content):
    for table_id in ("table.town_exploration", "table.random_encounter"):
        for entry in content.table(table_id).walk():
            if entry.table is None:
                assert entry.id in LEADS, entry.id


def test_town_exploration_leads_as_its_text_says():
    assert LEADS["table.town_exploration.6"] == Auto("table.street")
    assert LEADS["table.town_exploration.8"] == Choice(("table.store", "table.street"))
    assert isinstance(LEADS["table.town_exploration.7"], DieRoll)


# --- Rolling a table: the engine API ---------------------------------------------------------


def test_rolling_an_unknown_table_is_refused(content):
    game = new_game(content)
    with pytest.raises(GameError):
        game.roll_table("table.nowhere")
    with pytest.raises(GameError):
        game.roll_table("event.1")


def test_playing_something_that_is_not_an_event_is_refused(content):
    game = game_with_character(content)
    with pytest.raises(GameError):
        game.play_event("table.street")


def test_a_place_rolled_again_in_the_same_box_is_kept_once(content):
    game = game_with_character(content, 1, 2)
    game.choose_home(HOME)

    game.roll_table("table.street")
    game.roll_table("table.street")

    assert game.campaign.map.boxes[HOME].places == ["table.street"]
    assert game.history(Level.CAMPAIGN).count(Happened.PLAYED, "table.street") == 0


def test_an_entry_reached_on_a_mission_is_recorded_for_the_mission_too(content):
    game = game_with_character(content, 6)
    game.start_mission("mission.bring_home_the_bacon")

    game.roll_table("table.search")

    assert game.history(Level.MISSION).has(Happened.PLAYED, "table.search.6")


# --- Scenario: a full sheet lets the player attach a new one ---------------------------------


def full_first_sheet(content, position):
    """A game whose first sheet is all visited, the character standing at `position`."""
    game = game_with_character(content)
    game.choose_home(Position(0, 0))
    for box in boxes_of(Position(0, 0)):
        game.number_box(box)
    game.campaign.position = position
    return game


def test_attaching_a_sheet_is_offered_only_once_a_sheet_is_full(content):
    game = new_game(content)
    interface = ScriptedInterface([HOME, Action.QUIT])

    play(game, interface)

    assert Action.SHEET not in asked(interface, Topic.ACTION)[-1].options


def test_a_player_attaches_a_sheet_and_walks_onto_it(content):
    # given a full first sheet, the character on its right edge; the new box's 2d6 show 3
    # and 3 (Town Exploration 6: Street), whose d6 shows 1
    edge = Position(4, 2)
    game = full_first_sheet(content, edge)
    game.dice = ScriptedDice([3, 3, 1])
    interface = ScriptedInterface(
        [Action.SHEET, Position(1, 0), Action.MOVE, Position(5, 2), Book.DONE, Action.QUIT]
    )

    # when the player attaches a sheet to the right, then steps onto it
    play(game, interface)

    # then the sheet could go on any side, the new box was explored like any other
    assert asked(interface, Topic.ACTION)[0].options == (
        Action.MOVE,
        Action.SEARCH,
        Action.APPLY,
        Action.SHEET,
        Action.QUIT,
    )
    [choose] = asked(interface, Topic.SHEET)
    assert choose.options == (Position(0, -1), Position(-1, 0), Position(1, 0), Position(0, 1))
    assert SheetAttached(Position(1, 0)) in interface.told
    assert Arrival(Position(5, 2), 32, new=True) in interface.told
    assert rolled(interface)[0].entry_id == "table.town_exploration.6"


# --- A long random game ----------------------------------------------------------------------


class RandomPlayer:
    """Picks a random option for a number of requests, then quits. It prefers boxes not
    visited yet and attaches a sheet when it can, so sheets fill up; it says "nowhere else"
    half the time, so boxes get resolved, and moves most of the time. It types small numbers
    and short notes (manual actions, Search)."""

    def __init__(self, game, seed, requests):
        self.game = game
        self.random = random.Random(seed)
        self.left = requests
        self.told = []

    def ask(self, request):
        self.left -= 1
        if self.left <= 0:
            raise Quit
        if isinstance(request, Number):  # an amount, an L, a modifier: small numbers
            low = request.minimum if request.minimum is not None else -2
            return self.random.randint(low, low + 3)
        if isinstance(request, Text):  # a note
            return f"note {self.random.randint(1, 9)}"
        options = [option for option in request.options if option is not Action.QUIT]
        if Action.SHEET in options:
            return Action.SHEET
        if Book.DONE in options and self.random.random() < 0.5:
            return Book.DONE
        if Manual.BACK in options and self.random.random() < 0.5:
            return Manual.BACK
        if Action.MOVE in options and self.random.random() < 0.7:
            return Action.MOVE
        if request.topic is Topic.MOVE:
            new = [box for box in options if box not in self.game.campaign.map.boxes]
            options = new or options
        return self.random.choice(options)

    def tell(self, event):
        self.told.append(event)


@pytest.mark.parametrize("seed", range(5))
def test_a_long_random_game_reaches_only_known_content(content, seed):
    game = Game(dice=RandomDice(seed), content=content)
    game.create_character(life=99, sanity=99, food=99)  # so the walk lasts
    # Long enough that every seed fills a sheet (seed 0 needed more once R2 was copied).
    player = RandomPlayer(game, seed, 500)

    play(game, player)

    for event in player.told:
        if isinstance(event, Rolled):
            assert event.table_id in content
            assert event.entry_id is None or event.entry_id in content.entries
    assert len(game.campaign.map.sheets) > 1
