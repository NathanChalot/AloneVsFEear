"""E5b: book mode, manual actions (design/mvp-scope.md, Book mode).

After an entry the engine cannot read (a table not copied yet, a numbered event, a copied entry
whose behaviour is not written), the player applies its text with manual actions before saying
where it leads: gain or lose Life, Sanity, Food, XP or Clues; a roll vs L, the L and modifier
typed from the text; write or remove a note; mark the box as a Safe House. Each goes through
the engine, which offers only what the rules allow. The menu comes back after each action, so
the whole entry is applied before the player leaves it. When the character is at 0 Life or
Sanity, the entry offers only the manual actions and "nowhere else": the chain stops there and
the game ends, unless the entry brought the character back above 0 (death is checked once its
effects are applied).

Notes are plain text the engine stores and shows but never reads: the player's reminder of a
lasting effect or a modifier the engine cannot track yet (E7, E8 bring real effects). Each note
keeps the box number it was written at, so the player can tell when an effect "for N boxes"
ends. The free
action "apply an effect" opens the manual actions about the character (gain, lose, roll vs L,
write or remove a note) on any turn; marking a Safe House stays with the entry that gives it.

The Search roll is a free action, offered while the box has not been Searched and is not a
Safe House: d6, a natural 1 stays 1; when the character has notes, the player first types the
modifier they give. Its entry is then followed like any other.

Items (take, drop) wait for R3, which gives items their IDs. Scenarios are played by a scripted
interface; the dice show the faces given.
"""

import pytest

from alone_against_fear.content import load_content
from alone_against_fear.dice import ScriptedDice
from alone_against_fear.engine import Game, GameError, Happened, Level, Position, Stat
from alone_against_fear.engine.game import Rolled, RolledVsL, Searched
from alone_against_fear.engine.leads import LEADS, Auto, Nowhere
from alone_against_fear.engine.loop import play
from alone_against_fear.engine.manual import Manual
from alone_against_fear.engine.protocol import (
    Action,
    Book,
    Changed,
    Choose,
    End,
    Marked,
    NoteRemoved,
    NoteWritten,
    Number,
    Text,
    Topic,
    ask,
)
from alone_against_fear.engine.state import Mark, Note
from alone_against_fear.interface.scripted import ScriptedInterface

HOME = Position(2, 2)
EAST = Position(3, 2)
FOOD = 3
"""The placeholder character's Food die."""
STREET = (3, 3, 4)
"""A new box: Town Exploration 6 (3 and 3) rolls the Street, whose d6 shows 4. The Street is
not copied yet: its entry is book mode."""
MANUAL = (Manual.GAIN, Manual.LOSE, Manual.ROLL, Manual.WRITE_NOTE, Manual.SAFE_HOUSE)
"""The manual actions of an entry, for a character with no notes."""
EFFECTS = (Manual.GAIN, Manual.LOSE, Manual.ROLL, Manual.WRITE_NOTE, Manual.BACK)
"""The "apply an effect" menu, for a character with no notes."""


@pytest.fixture(scope="module")
def content():
    return load_content()


def new_game(content, *faces):
    return Game(dice=ScriptedDice([FOOD, *faces]), content=content)


def noted_game(content, *faces, note="+1 to Search"):
    """A game whose character has a note already: no Food die is rolled."""
    game = Game(dice=ScriptedDice(faces), content=content)
    game.create_character(life=8, sanity=8, food=3)
    game.add_note(note)
    return game


def asked(interface, topic):
    return [request for request in interface.asked if request.topic is topic]


def told(interface, kind):
    return [event for event in interface.told if isinstance(event, kind)]


def on_the_street(*answers):
    """Home, then a move to the new box east of it (the Street, book mode), the answers its
    entry needs, then quit if the game is still on."""
    return [HOME, Action.MOVE, EAST, *answers]


# --- Scenario: an entry the engine cannot read offers the manual actions ---------------------


def test_book_mode_offers_the_manual_actions_with_where_the_text_leads(content):
    game = new_game(content, *STREET)
    interface = ScriptedInterface(on_the_street(Book.DONE, Action.QUIT))

    play(game, interface)

    assert asked(interface, Topic.BOOK) == [
        Choose(Topic.BOOK, (Book.TABLE, Book.EVENT, *MANUAL, Book.DONE))
    ]


def test_a_player_loses_the_sanity_the_text_takes(content):
    # given the Street's entry says to lose 2 Sanity
    game = new_game(content, *STREET)
    interface = ScriptedInterface(
        on_the_street(Manual.LOSE, Stat.SANITY, 2, Book.DONE, Action.QUIT)
    )

    # when the player loses 2 Sanity, then says the text leads nowhere else
    play(game, interface)

    # then the character has 6 Sanity, the interface was told, and the menu came back
    assert game.character.sanity == 6
    assert told(interface, Changed) == [Changed(Stat.SANITY, -2, 6)]
    assert len(asked(interface, Topic.BOOK)) == 2
    assert asked(interface, Topic.AMOUNT) == [Number(Topic.AMOUNT, minimum=1)]


def test_a_player_gains_what_the_text_gives(content):
    game = new_game(content, *STREET)
    interface = ScriptedInterface(
        on_the_street(Manual.GAIN, Stat.CLUES, 1, Manual.GAIN, Stat.XP, 2, Book.DONE, Action.QUIT)
    )

    play(game, interface)

    assert (game.character.clues, game.character.xp) == (1, 2)
    # every number can be gained
    assert asked(interface, Topic.STAT)[0] == Choose(Topic.STAT, tuple(Stat))


def test_life_has_no_max_until_character_creation(content):
    # E6 gives Life and Sanity a max; healing stops there (see the pending tests)
    game = new_game(content, *STREET)
    interface = ScriptedInterface(on_the_street(Manual.GAIN, Stat.LIFE, 3, Book.DONE, Action.QUIT))

    play(game, interface)

    assert game.character.life == 11


def test_only_what_the_character_has_can_be_lost(content):
    # given a character with no XP and no Clues
    game = new_game(content, *STREET)
    interface = ScriptedInterface(on_the_street(Manual.LOSE, Stat.FOOD, 5, Book.DONE, Action.QUIT))

    # when the text takes 5 Food and the character has 3
    play(game, interface)

    # then only the numbers above 0 were offered, and the Food goes down to 0, not below
    assert asked(interface, Topic.STAT) == [Choose(Topic.STAT, (Stat.LIFE, Stat.SANITY, Stat.FOOD))]
    assert game.character.food == 0
    assert told(interface, Changed) == [Changed(Stat.FOOD, -3, 0)]


def test_the_player_rolls_vs_the_l_the_text_gives(content):
    # given the Street's entry asks for an L4 Save at +1; the die shows 3
    game = new_game(content, *STREET, 3)
    interface = ScriptedInterface(on_the_street(Manual.ROLL, 4, 1, Book.DONE, Action.QUIT))

    play(game, interface)

    # then 3 + 1 makes the L4
    assert told(interface, RolledVsL) == [
        RolledVsL(level=4, modifier=1, face=3, total=4, success=True)
    ]
    assert asked(interface, Topic.LEVEL) == [Number(Topic.LEVEL, minimum=1)]
    assert asked(interface, Topic.MODIFIER) == [Number(Topic.MODIFIER)]


def test_the_player_marks_the_box_as_a_safe_house(content):
    game = new_game(content, *STREET)
    interface = ScriptedInterface(on_the_street(Manual.SAFE_HOUSE, Book.DONE, Action.QUIT))

    play(game, interface)

    assert Mark.SAFE_HOUSE in game.campaign.map.boxes[EAST].marks
    assert told(interface, Marked) == [Marked(EAST, Mark.SAFE_HOUSE)]
    # it is a Safe House already: the menu no longer offers it
    assert Manual.SAFE_HOUSE not in asked(interface, Topic.BOOK)[-1].options


def test_a_numbered_event_offers_the_manual_actions_too(content):
    game = new_game(content, *STREET)
    interface = ScriptedInterface(
        on_the_street(Book.EVENT, "event.12", Manual.LOSE, Stat.LIFE, 1, Book.DONE, Action.QUIT)
    )

    play(game, interface)

    assert game.character.life == 7
    assert asked(interface, Topic.BOOK)[-1].options == (Book.TABLE, Book.EVENT, *MANUAL, Book.DONE)


# --- Scenario: notes keep track of what the engine cannot -------------------------------------


def test_the_player_writes_a_note_of_a_lasting_effect(content):
    # given the Street's entry gives an effect that lasts several boxes
    game = new_game(content, *STREET)
    interface = ScriptedInterface(
        on_the_street(Manual.WRITE_NOTE, "lose 1 Life each box, 3 boxes", Book.DONE, Action.QUIT)
    )

    play(game, interface)

    # then the note keeps the box it was written at: box 2, east of Home
    note = Note("lose 1 Life each box, 3 boxes", box=2)
    assert game.character.notes == [note]
    assert asked(interface, Topic.NOTE) == [Text(Topic.NOTE)]
    assert told(interface, NoteWritten) == [NoteWritten(note)]
    # and once there is a note, it can be removed
    assert Manual.REMOVE_NOTE in asked(interface, Topic.BOOK)[-1].options


def test_a_note_is_stored_without_the_spaces_around_it(content):
    game = new_game(content, *STREET)
    interface = ScriptedInterface(
        on_the_street(Manual.WRITE_NOTE, "  cursed  ", Book.DONE, Action.QUIT)
    )

    play(game, interface)

    assert game.character.notes == [Note("cursed", box=2)]


def test_the_player_removes_a_note_picked_among_the_notes(content):
    game = noted_game(content, *STREET, note="cursed")
    game.add_note("lose 1 Life each box")
    cursed, lose = game.character.notes  # written before Home: box 0
    interface = ScriptedInterface(on_the_street(Manual.REMOVE_NOTE, cursed, Book.DONE, Action.QUIT))

    play(game, interface)

    assert asked(interface, Topic.NOTES) == [Choose(Topic.NOTES, (cursed, lose))]
    assert game.character.notes == [Note("lose 1 Life each box", box=0)]
    assert told(interface, NoteRemoved) == [NoteRemoved(cursed)]


def test_removing_a_note_the_character_does_not_have_is_refused(content):
    game = noted_game(content)

    with pytest.raises(GameError):
        game.remove_note(Note("blessed", box=0))


def test_notes_belong_to_the_character(content):
    # a new character starts with none
    game = noted_game(content)

    game.create_character(life=8, sanity=8, food=3)

    assert game.character.notes == []


# --- Scenario: "apply an effect" on any turn ---------------------------------------------------


def test_apply_an_effect_is_a_free_action(content):
    game = new_game(content)
    interface = ScriptedInterface([HOME, Action.QUIT])

    play(game, interface)

    assert asked(interface, Topic.ACTION)[0].options == (
        Action.MOVE,
        Action.SEARCH,
        Action.APPLY,
        Action.QUIT,
    )


def test_apply_an_effect_opens_the_manual_actions_about_the_character(content):
    # given a quiet turn: a note says to lose 1 Life each box
    game = noted_game(content, note="lose 1 Life each box")
    interface = ScriptedInterface(
        [HOME, Action.APPLY, Manual.LOSE, Stat.LIFE, 1, Manual.BACK, Action.QUIT]
    )

    # when the player applies it as a free action
    play(game, interface)

    # then the menu has no Safe House (an entry gives it) and comes back until "back"
    first, second = asked(interface, Topic.APPLY)
    assert first.options == (
        Manual.GAIN,
        Manual.LOSE,
        Manual.ROLL,
        Manual.WRITE_NOTE,
        Manual.REMOVE_NOTE,
        Manual.BACK,
    )
    assert second == first
    assert game.character.life == 7


def test_apply_an_effect_writes_and_removes_notes(content):
    game = new_game(content)
    interface = ScriptedInterface(
        [
            HOME,
            Action.APPLY,
            Manual.WRITE_NOTE,
            "cursed",
            Manual.BACK,
            Action.APPLY,
            Manual.REMOVE_NOTE,
            Note("cursed", box=1),
            Manual.BACK,
            Action.QUIT,
        ]
    )

    play(game, interface)

    assert asked(interface, Topic.APPLY)[0].options == EFFECTS
    assert game.character.notes == []


def test_a_loss_to_0_in_apply_an_effect_ends_the_game_once_back(content):
    # death is checked once the effects are applied: the player may heal before going back
    game = new_game(content)
    interface = ScriptedInterface([HOME, Action.APPLY, Manual.LOSE, Stat.LIFE, 8, Manual.BACK])

    assert play(game, interface) is End.DEAD
    assert len(asked(interface, Topic.APPLY)) == 2


# --- Scenario: death at 0, once the entry is applied -----------------------------------------


def test_at_0_life_the_entry_offers_only_the_manual_actions_and_nowhere_else(content):
    # given the Street's entry takes all 8 Life
    game = new_game(content, *STREET)
    interface = ScriptedInterface(on_the_street(Manual.LOSE, Stat.LIFE, 8, Book.DONE))

    # when the player applies it and leaves the entry
    end = play(game, interface)

    # then the menu offered no table or event any more, and the game ends with no free action
    assert asked(interface, Topic.BOOK)[-1].options == (*MANUAL, Book.DONE)
    assert end is End.DEAD
    assert len(asked(interface, Topic.ACTION)) == 1  # the move only


def test_an_entry_that_heals_after_the_loss_keeps_the_character_alive(content):
    # given an entry that takes 8 Life, then gives 1 back
    game = new_game(content, *STREET)
    interface = ScriptedInterface(
        on_the_street(Manual.LOSE, Stat.LIFE, 8, Manual.GAIN, Stat.LIFE, 1, Book.DONE, Action.QUIT)
    )

    # then death is checked once the entry is applied: the character lives on
    assert play(game, interface) is End.QUIT
    assert game.character.life == 1


def test_at_0_sanity_the_character_goes_insane(content):
    game = new_game(content, *STREET)
    interface = ScriptedInterface(on_the_street(Manual.LOSE, Stat.SANITY, 8, Book.DONE))

    assert play(game, interface) is End.INSANE


def test_a_chain_stops_at_the_entry_that_kills(content):
    # given a copied entry whose lead is not written (Search 6) reached at 0 Life: its own
    # tables are not offered either
    game = new_game(content, 6)
    interface = ScriptedInterface([HOME, Action.SEARCH, Manual.LOSE, Stat.LIFE, 8, Book.DONE])

    assert play(game, interface) is End.DEAD
    assert asked(interface, Topic.BOOK)[-1].options == (*MANUAL, Book.DONE)


# --- Scenario: the Search roll ---------------------------------------------------------------


def test_search_is_a_free_action_until_the_box_is_searched(content):
    # given Home, not Searched yet; the Search die shows 3 (Nothing found)
    game = new_game(content, 3)
    interface = ScriptedInterface([HOME, Action.SEARCH, Action.QUIT])

    play(game, interface)

    first, second = asked(interface, Topic.ACTION)
    assert Action.SEARCH in first.options
    assert Action.SEARCH not in second.options
    # with no notes, no modifier is asked
    assert asked(interface, Topic.MODIFIER) == []
    assert game.campaign.map.boxes[HOME].searched
    # and nothing found leads nowhere: no book mode
    assert told(interface, Searched) == [
        Searched(face=3, modifier=0, rolled=Rolled("table.search", (3,), "table.search.2-5"))
    ]
    assert asked(interface, Topic.BOOK) == []


def test_with_notes_the_player_types_the_search_modifier_they_give(content):
    # given a note of a +1 to Search; the die shows 5: 6, Success
    game = noted_game(content, 5)
    interface = ScriptedInterface([HOME, Action.SEARCH, 1, Book.DONE, Action.QUIT])

    play(game, interface)

    assert asked(interface, Topic.MODIFIER) == [Number(Topic.MODIFIER)]
    assert told(interface, Searched)[0].rolled == Rolled("table.search", (6,), "table.search.6")


def test_a_search_result_stays_on_the_table(content):
    # 5 + 2 is 7: the Search table stops at 6; 2 - 3 is -1: it starts at 1 (its 1 rolls on the
    # Random Encounter table, whose dice show 2 and 5, then the Beasts' d6 shows 1)
    high = noted_game(content, 5)
    play(high, ScriptedInterface([HOME, Action.SEARCH, 2, Book.DONE, Action.QUIT]))
    low = noted_game(content, 2, 2, 5, 1)
    low_interface = ScriptedInterface([HOME, Action.SEARCH, -3, Book.DONE, Action.QUIT])
    play(low, low_interface)

    assert high.history(Level.CAMPAIGN).has(Happened.PLAYED, "table.search.6")
    assert told(low_interface, Searched)[0].rolled.results == (1,)


def test_a_natural_1_on_the_search_stays_1(content):
    # given +2 to Search and a natural 1: Search 1, "Roll on the random encounter table"; its
    # dice show 3 and 6 (the Unique Vampires), whose d6 shows 2
    game = noted_game(content, 1, 3, 6, 2)
    interface = ScriptedInterface([HOME, Action.SEARCH, 2, Book.DONE, Action.QUIT])

    play(game, interface)

    assert [event.table_id for event in told(interface, Rolled)] == [
        "table.search",
        "table.random_encounter",
        "table.unique_vampires",
    ]
    assert told(interface, Searched)[0] == Searched(
        face=1, modifier=2, rolled=Rolled("table.search", (1,), "table.search.1")
    )


def test_search_6_is_applied_in_book_mode(content):
    # "Roll 4 times on the Useful Items table or on the Random Object table, and pick a single
    # result, or Roll on the Random Book table if you are in a Library; OR gain 1 Clue."
    game = new_game(content, 6)
    interface = ScriptedInterface(
        [HOME, Action.SEARCH, Manual.GAIN, Stat.CLUES, 1, Book.DONE, Action.QUIT]
    )

    play(game, interface)

    assert asked(interface, Topic.BOOK)[0].options == (
        "table.useful_stuff",
        "table.random_objects",
        "table.random_book",
        *MANUAL,
        Book.DONE,
    )
    assert game.character.clues == 1


def test_a_safe_house_cannot_be_searched(content):
    # "you may NOT Search a Safe House"
    game = new_game(content, *STREET)
    interface = ScriptedInterface(on_the_street(Manual.SAFE_HOUSE, Book.DONE, Action.QUIT))

    play(game, interface)

    assert Action.SEARCH not in asked(interface, Topic.ACTION)[-1].options


def test_searching_twice_is_refused(content):
    game = new_game(content, 3, 3)
    play(game, ScriptedInterface([HOME, Action.SEARCH, Action.QUIT]))

    with pytest.raises(GameError):
        game.search(0)


def test_searching_a_safe_house_is_refused(content):
    game = new_game(content)
    play(game, ScriptedInterface([HOME, Action.QUIT]))
    game.add_mark(HOME, Mark.SAFE_HOUSE)

    assert not game.may_search()
    with pytest.raises(GameError):
        game.search(0)


def test_the_search_table_leads_as_its_text_says():
    assert LEADS["table.search.1"] == Auto("table.random_encounter")
    assert LEADS["table.search.2-5"] == Nowhere()
    assert "table.search.6" not in LEADS  # book mode until E10


# --- Rolls vs L: the engine API --------------------------------------------------------------


@pytest.mark.parametrize(
    ("face", "level", "modifier", "success"),
    [
        (3, 4, 1, True),  # 3 + 1 makes the L4
        (3, 4, 0, False),
        (5, 4, -2, False),
        (1, 2, 5, False),  # "Rolling a 1 is always a failure"
        (6, 9, -3, True),  # "and rolling a 6 is always a success"
    ],
)
def test_a_roll_vs_l(content, face, level, modifier, success):
    game = Game(dice=ScriptedDice([face]), content=content)

    rolled = game.roll_vs(level, modifier)

    assert rolled == RolledVsL(level, modifier, face, face + modifier, success)


# --- Typed answers ---------------------------------------------------------------------------


@pytest.mark.parametrize("answer", [0, -1, 1.5, True, "2", None])
def test_a_number_out_of_its_bounds_or_not_a_whole_number_is_refused(answer):
    with pytest.raises(GameError):
        ask(ScriptedInterface([answer]), Number(Topic.AMOUNT, minimum=1))


def test_a_number_above_its_maximum_is_refused():
    with pytest.raises(GameError):
        ask(ScriptedInterface([7]), Number(Topic.LEVEL, minimum=1, maximum=6))


def test_a_number_with_no_bounds_takes_any_whole_number(caplog):
    caplog.set_level("INFO", logger="alone_against_fear")

    assert ask(ScriptedInterface([-3]), Number(Topic.MODIFIER)) == -3
    assert "answer modifier: -3" in caplog.text


@pytest.mark.parametrize("answer", ["", "   ", 3, None])
def test_an_empty_text_is_refused(answer):
    with pytest.raises(GameError):
        ask(ScriptedInterface([answer]), Text(Topic.NOTE))


# --- Pending: edge cases of death and manual actions, for the tasks that bring them ----------
# Skipped until their task: pytest lists them on every run as a reminder. Written as
# given/when/then; the task that brings the rule writes the test body.


@pytest.mark.skip(reason="E6: Life and Sanity get a max")
def test_pending_healing_stops_at_max():
    # given a character at max Life
    # when a book-mode entry gives Life
    # then Life stays at max
    ...


@pytest.mark.skip(reason="E13: losses go through armor, Luck and the Injury offer")
def test_pending_a_manual_life_loss_offers_an_injury_before_death():
    # given a character with 2 Life and fewer than 3 Injuries
    # when a book-mode entry takes 3 Life
    # then the player is offered an Injury instead of the loss, before death is checked
    ...


@pytest.mark.skip(reason="E13 (open question): can a reaction after a loss save the character?")
def test_pending_a_reaction_after_a_loss_brings_the_character_back_above_0():
    # given something that heals after a loss (written content, not a manual action)
    # when a loss takes the character to 0 Life
    # then the reaction fires before death is checked, and the character lives on
    ...


@pytest.mark.skip(reason="E13: what a written entry does at 0, halfway through its effects")
def test_pending_a_written_entry_stops_at_0_once_its_effects_are_applied():
    # given a written entry that takes Life, then sends the player to another table
    # when the loss takes the character to 0 Life
    # then the entry's other effects are applied, the next table is not rolled, the game ends
    ...


@pytest.mark.skip(reason="E11: ignoring an encounter or moving along blocks the Search")
def test_pending_an_ignored_encounter_blocks_the_search():
    # given a box whose encounter was ignored (design/rulings.md, Encounters)
    # then Search is not offered there
    ...


@pytest.mark.skip(reason="E11: a library can be Searched again, for 1 book or 1 Clue")
def test_pending_a_library_can_be_searched_again(): ...


@pytest.mark.skip(reason="E15: Home is a Safe House (design/rulings.md): no Search there")
def test_pending_home_cannot_be_searched(): ...


@pytest.mark.skip(reason="E8: consider manual effects the engine applies, replacing notes")
def test_pending_a_lasting_effect_typed_by_the_player_is_applied_by_the_engine():
    # given the player adds "-1 to Search for the next 3 boxes" as an effect, not a note
    # when they Search within those 3 boxes
    # then the engine applies the -1 by itself, and the effect ends after 3 boxes
    ...


@pytest.mark.skip(reason="After R3: take and drop items as manual actions, picked by ID")
def test_pending_the_player_takes_the_item_the_text_gives():
    # given an entry that gives an item
    # when the player takes it, picked from the copied items
    # then it is in the inventory, and can be dropped
    ...
