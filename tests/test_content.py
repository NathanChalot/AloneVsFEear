"""The rules text copied into YAML: checks over the whole content, then what each
table says, written from the book (see docs/content.md)."""

import re
from collections import Counter
from pathlib import Path

import pytest

from alone_against_fear.content import (
    KINDS,
    coverage_problems,
    load_content,
    note_problems,
    reference_problems,
)

REPO = Path(__file__).resolve().parents[1]
CONTENT = load_content()


def all_tables():
    """Every copied table, nested tables included."""
    for table in CONTENT.tables.values():
        yield table
        yield from table.nested_tables()


def all_entries():
    for table in all_tables():
        yield from table.entries


# --- Checks over the whole content ------------------------------------------


@pytest.mark.parametrize("table", list(all_tables()), ids=lambda t: t.id)
def test_every_table_covers_its_dice_range(table):
    assert coverage_problems(table) == []


def test_every_reference_points_to_an_existing_id():
    assert reference_problems(CONTENT) == []


def test_every_note_an_entry_points_to_exists():
    assert note_problems(CONTENT) == []


def test_ids_follow_the_scheme():
    segment = r"[a-z0-9]+(?:[_-][a-z0-9]+)*"
    pattern = re.compile(rf"{segment}(?:\.{segment})+")
    ids = list(CONTENT.tables) + list(CONTENT.catalogue) + [e.id for e in all_entries()]
    for id_ in ids:
        assert pattern.fullmatch(id_), id_
        assert id_.split(".")[0] in KINDS, id_


def test_every_rules_table_file_is_the_source_of_exactly_one_table():
    files = {p.relative_to(REPO).as_posix() for p in (REPO / "gameRules/tables").rglob("*.md")}
    catalogued = [t for t in CONTENT.catalogue.values() if t.id.startswith("table.")]
    sources = Counter(t.source for t in [*CONTENT.tables.values(), *catalogued])
    assert set(sources) == files
    assert [s for s, n in sources.items() if n > 1] == []


def test_no_page_reference_is_left():
    page = re.compile(r"\bp\.\s*\d+")
    texts = [t.text for t in CONTENT.tables.values()]
    texts += [note for t in CONTENT.tables.values() for note in t.notes.values()]
    texts += [e.text for e in all_entries()]
    assert [t for t in texts if t and page.search(t)] == []


# --- Events (catalogued until R6) -------------------------------------------


def test_the_42_numbered_events_are_catalogued():
    events = CONTENT.events()
    assert [event.id for event in events] == [f"event.{n}" for n in range(1, 43)]
    assert {event.source for event in events} == {"gameRules/6_unique_events.md"}


def test_each_catalogued_event_has_its_heading_name():
    headings = {}
    for line in (REPO / "gameRules/6_unique_events.md").read_text().splitlines():
        if match := re.match(r"###\s*(\d+)\s*[-.]\s*(.+?)\.?\s*$", line):
            headings[int(match[1])] = match[2]
    for event in CONTENT.events():
        assert event.name.lower() == headings[event.number].lower(), event.id


# --- Town Exploration -------------------------------------------------------

TOWN = CONTENT.table("table.town_exploration")


def test_town_exploration_is_rolled_on_2d6():
    assert TOWN.dice == "2d6"


@pytest.mark.parametrize(
    ("result", "refs"),
    [
        (2, ["table.random_encounter"]),
        (3, ["table.military_installation_or_lab", "table.clinic"]),
        (4, ["table.farm", "table.cemetery"]),
        (5, ["table.place_of_worship"]),
        (6, ["table.street"]),
        (7, ["table.house", "table.special_events"]),
        (8, ["table.store", "table.street"]),
        (9, ["table.sewers"]),
        (10, ["table.railways", "table.woods_or_park"]),
        (11, ["table.school", "table.woods_or_park"]),
        (12, ["table.woods_or_park"]),
    ],
)
def test_town_exploration_sends_you_to_the_place_tables(result, refs):
    assert list(TOWN.entry_for(result).refs) == refs


def test_town_exploration_7_rolls_d6_for_house_or_special_events():
    assert TOWN.entry_for(7).text == (
        "Roll d6. On a 1-5, roll on the House table. On a 6, roll on the Special Events table."
    )


def test_town_exploration_text_holds_the_search_rule():
    assert "You may Search an area ONLY after dealing with" in TOWN.text


# --- Random Encounter -------------------------------------------------------

RANDOM = CONTENT.table("table.random_encounter")


@pytest.mark.parametrize(
    ("first", "seconds", "ref"),
    [
        (1, range(1, 3), "table.slashers"),
        (1, range(3, 7), "table.witch_children"),
        (2, range(1, 4), "table.demonic_horrors"),
        (2, range(4, 7), "table.beasts"),
        (3, range(1, 3), "table.lab_horrors"),
        (3, range(3, 6), "table.undead"),
        (3, range(6, 7), "table.unique_vampires"),
        (4, range(1, 5), "table.possessed"),
        (4, range(5, 7), "table.living_dolls"),
        (5, range(1, 6), "table.ghosts"),
        (5, range(6, 7), "table.aliens"),
        (6, range(1, 4), "table.unique_vampires"),
        (6, range(4, 7), "table.unique_zombies"),
    ],
)
def test_random_encounter_is_d6_then_another_d6(first, seconds, ref):
    sub_table = RANDOM.entry_for(first).table
    assert sub_table.dice == "d6"
    for second in seconds:
        assert list(sub_table.entry_for(second).refs) == [ref]


def test_nested_entries_are_found_by_id():
    assert list(CONTENT.entry("table.random_encounter.3.3-5").refs) == ["table.undead"]


def test_the_unique_creatures_note_is_shown_with_every_unique_entry():
    with_note = sorted(e.id for e in RANDOM.walk() if "unique_creatures" in e.notes)
    assert with_note == [
        "table.random_encounter.3.6",
        "table.random_encounter.6.1-3",
        "table.random_encounter.6.4-6",
    ]
    assert RANDOM.notes["unique_creatures"].startswith(
        "When rolling on tables of Unique creatures, reroll any monster"
    )
    assert CONTENT.entry("table.random_encounter.6.4-6").text == (
        "Roll on the Unique Zombies table."
    )


def test_the_slashers_entry_keeps_its_own_reroll_rule():
    text = CONTENT.entry("table.random_encounter.1.1-2").text
    assert "Reroll any Slasher that you have already defeated in the campaign." in text


# --- Search -----------------------------------------------------------------

SEARCH = CONTENT.table("table.search")


def test_search_1_is_a_random_encounter():
    assert list(SEARCH.entry_for(1).refs) == ["table.random_encounter"]


@pytest.mark.parametrize("result", [2, 3, 4, 5])
def test_search_2_to_5_finds_nothing(result):
    entry = SEARCH.entry_for(result)
    assert entry.id == "table.search.2-5"
    assert entry.text == "Nothing found."
    assert entry.refs == ()


def test_search_6_offers_items_a_book_or_a_clue():
    assert list(SEARCH.entry_for(6).refs) == [
        "table.useful_stuff",
        "table.random_objects",
        "table.random_book",
    ]


def test_search_text_holds_the_investigator_bonus():
    assert "Roll at +1 if you have the Investigator Skill" in SEARCH.text
    assert "A roll of 1 remains a 1." in SEARCH.text


# --- Missions ---------------------------------------------------------------

MISSION = CONTENT.table("table.mission")


@pytest.mark.parametrize(
    ("result", "id_", "name"),
    [
        (1, "mission.medical_supplies", "Medical Supplies"),
        (2, "mission.predator_and_prey", "Predator and Prey"),
        (3, "mission.bring_home_the_bacon", "Bring Home the Bacon"),
        (4, "mission.we_need_weapons", "We Need Weapons"),
        (5, "mission.destroy_the_coven", "Destroy the Coven"),
        (6, "mission.close_a_hell_gate", "Close a Hell Gate"),
    ],
)
def test_each_mission_is_a_named_entry(result, id_, name):
    entry = MISSION.entry_for(result)
    assert (entry.id, entry.name) == (id_, name)
    assert CONTENT.entry(id_) is entry


def test_a_mission_text_starts_after_its_name():
    text = CONTENT.entry("mission.bring_home_the_bacon").text
    assert text.startswith("You must bring back to your starting location")


def test_mission_text_holds_the_reroll_rule():
    assert "If you roll the same Mission that you played last time" in MISSION.text
