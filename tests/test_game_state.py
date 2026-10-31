"""E2: the game state, built, queried and changed through the engine API.

Levels nest: the campaign outlives its characters, a character outlives its missions
(design/encounters.md, What the game remembers). Rules that limit or gate content read the
history of a level: what was played, found or killed there, and its keywords.
"""

import dataclasses
import logging
from collections import Counter
from enum import Enum

import pytest

from alone_against_fear.content import load_content
from alone_against_fear.dice import ScriptedDice
from alone_against_fear.engine import Game, GameError, Happened, Level, Position, Stat

BACON = "mission.bring_home_the_bacon"


@pytest.fixture(scope="module")
def content():
    return load_content()


@pytest.fixture
def game(content):
    return Game(dice=ScriptedDice([]), content=content)


@pytest.fixture
def playing(game):
    """A game with a character on a mission."""
    game.create_character(life=7, sanity=6, food=4, items=["Knife", "Pistol"])
    game.start_mission(BACON)
    return game


# --- A new campaign ---------------------------------------------------------


def test_a_new_campaign_is_empty(game):
    campaign = game.campaign
    assert campaign.box_counter == 0
    assert campaign.map.boxes == {}
    assert campaign.character is None
    assert campaign.history.count(Happened.PLAYED, "event.1") == 0
    assert campaign.history.keywords == set()


def test_a_game_can_continue_a_campaign(game, content):
    # given a campaign with a character
    game.create_character(life=5, sanity=5, food=3)
    # when a new game is built from it
    resumed = Game(dice=ScriptedDice([]), content=content, campaign=game.campaign)
    # then it plays the same campaign
    assert resumed.character.food == 3


# --- The character ------------------------------------------------------------


def test_creating_a_character(game):
    character = game.create_character(life=7, sanity=6, food=4, items=["Knife"])
    assert (character.life, character.sanity, character.food) == (7, 6, 4)
    assert (character.xp, character.clues) == (0, 0)
    assert character.items == ["Knife"]
    assert character.mission is None
    assert game.character is character


def test_there_is_no_character_before_one_is_created(game):
    with pytest.raises(GameError):
        _ = game.character
    with pytest.raises(GameError):
        game.gain(Stat.FOOD, 1)


@pytest.mark.parametrize("stat", list(Stat))
def test_every_number_can_be_gained_and_lost(playing, stat):
    before = getattr(playing.character, stat)
    assert playing.gain(stat, 3) == before + 3
    assert playing.lose(stat, 2) == before + 1
    assert getattr(playing.character, stat) == before + 1


@pytest.mark.parametrize("change", ["gain", "lose"])
def test_a_negative_amount_is_refused(playing, change):
    with pytest.raises(GameError):
        getattr(playing, change)(Stat.LIFE, -1)


def test_items_are_added_and_removed_by_name(playing):
    playing.add_item("Knife")
    playing.remove_item("Pistol")
    assert playing.character.items == ["Knife", "Knife"]


def test_removing_an_item_the_character_does_not_have_is_refused(playing):
    with pytest.raises(GameError):
        playing.remove_item("Shotgun")


# --- Missions -----------------------------------------------------------------


def test_a_mission_is_started_by_id(playing):
    mission = playing.character.mission
    assert mission.id == BACON
    assert mission.history.count(Happened.FOUND, "x") == 0


def test_an_unknown_mission_is_refused(playing):
    with pytest.raises(GameError):
        playing.start_mission("mission.nowhere")


def test_a_new_mission_forgets_the_last_one(playing):
    # given something found during the mission
    playing.record(Level.MISSION, Happened.FOUND, "table.childrens_stuff.3")
    # when a new mission is rolled
    playing.start_mission(BACON)
    # then the new mission has found nothing yet
    assert not playing.history(Level.MISSION).has(Happened.FOUND, "table.childrens_stuff.3")


def test_there_is_no_mission_history_without_a_mission(game):
    game.create_character(life=5, sanity=5, food=3)
    with pytest.raises(GameError):
        game.record(Level.MISSION, Happened.PLAYED, "event.9")


# --- The map and the box counter ------------------------------------------------


def test_numbering_a_box_advances_the_counter(playing):
    assert playing.number_box(Position(2, 3)) == 1
    assert playing.number_box(Position(3, 3)) == 2
    assert playing.campaign.box_counter == 2


def test_a_box_keeps_every_number_written_in_it(playing):
    for position in [Position(2, 3), Position(3, 3), Position(2, 3)]:
        playing.number_box(position)
    assert playing.campaign.map.boxes[Position(2, 3)].numbers == [1, 3]
    assert playing.campaign.map.boxes[Position(3, 3)].numbers == [2]


# --- What each level remembers ----------------------------------------------------


def test_each_level_counts_what_happened(playing):
    playing.record(Level.CAMPAIGN, Happened.KILLED, "creature.slasher")
    playing.record(Level.CAMPAIGN, Happened.KILLED, "creature.slasher")
    playing.record(Level.CHARACTER, Happened.FOUND, "book.necronomicon")
    playing.record(Level.MISSION, Happened.PLAYED, "event.9")

    assert playing.history(Level.CAMPAIGN).count(Happened.KILLED, "creature.slasher") == 2
    assert playing.history(Level.CHARACTER).has(Happened.FOUND, "book.necronomicon")
    assert playing.history(Level.MISSION).has(Happened.PLAYED, "event.9")
    assert not playing.history(Level.CAMPAIGN).has(Happened.PLAYED, "event.9")


def test_keywords_are_kept_per_level(playing):
    playing.add_keyword(Level.CAMPAIGN, "SNOWY")
    playing.add_keyword(Level.CHARACTER, "CLOWNFACE")
    assert playing.history(Level.CAMPAIGN).keywords == {"SNOWY"}
    assert playing.history(Level.CHARACTER).keywords == {"CLOWNFACE"}


def test_a_new_character_continues_the_campaign_but_not_the_old_character(playing):
    # given a campaign that remembers the town and a character who remembers themself
    playing.number_box(Position(0, 0))
    playing.record(Level.CAMPAIGN, Happened.PLAYED, "event.7")
    playing.add_keyword(Level.CHARACTER, "CLOWNFACE")
    playing.gain(Stat.CLUES, 2)
    # when the character dies and a new one is created
    playing.create_character(life=6, sanity=6, food=2)
    # then the town is the same, the person is new
    assert playing.campaign.box_counter == 1
    assert playing.history(Level.CAMPAIGN).has(Happened.PLAYED, "event.7")
    assert playing.history(Level.CHARACTER).keywords == set()
    assert playing.character.clues == 0
    assert playing.character.mission is None


# --- The state is plain data ----------------------------------------------------------


PLAIN = (int, str, bool, type(None), Enum)


def assert_plain(value, path="campaign"):
    """Only numbers, strings, enums, containers of them and dataclasses of them: no code."""
    if isinstance(value, PLAIN):
        return
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        for field in dataclasses.fields(value):
            assert_plain(getattr(value, field.name), f"{path}.{field.name}")
    elif isinstance(value, (dict, Counter)):
        for key, item in value.items():
            assert_plain(key, f"{path} key")
            assert_plain(item, f"{path}[{key!r}]")
    elif isinstance(value, (list, tuple, set, frozenset)):
        for item in value:
            assert_plain(item, f"{path} item")
    else:
        pytest.fail(f"{path} holds {type(value).__name__}, which is not plain data")


def test_the_state_holds_only_plain_data(playing):
    playing.number_box(Position(1, 1))
    playing.record(Level.CAMPAIGN, Happened.KILLED, "creature.slasher")
    playing.add_keyword(Level.MISSION, "DOSES")
    assert_plain(playing.campaign)


def test_the_plain_data_check_catches_code():
    @dataclasses.dataclass
    class Holder:
        rule: object

    with pytest.raises(pytest.fail.Exception):
        assert_plain(Holder(rule=lambda: None))


# --- Every change is logged -------------------------------------------------------------


def test_changes_are_logged(playing, caplog):
    with caplog.at_level(logging.INFO, logger="alone_against_fear"):
        playing.lose(Stat.FOOD, 1)
        playing.record(Level.CAMPAIGN, Happened.KILLED, "creature.slasher")
    assert "food" in caplog.text.lower()
    assert "creature.slasher" in caplog.text
