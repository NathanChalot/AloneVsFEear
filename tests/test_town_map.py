"""E3: the town map, moves and time (design/town-map.md).

The town is one grid; a sheet is a 5-column, 6-row block of it. Boxes are neighbours across a
side or a corner, distance is the larger of the column and row gaps, every move numbers the box
entered, and every 5th box number costs 1 Food (or 1 Life without Food).
"""

import pytest

from alone_against_fear.content import load_content
from alone_against_fear.dice import ScriptedDice
from alone_against_fear.engine import Game, GameError, MoveKind, Position, Upkeep
from alone_against_fear.engine.town import distance, neighbours, sheet_of

FIRST = Position(0, 0)  # the first sheet, as a position in the grid of sheets
ALL_FIRST_SHEET = {FIRST}


@pytest.fixture(scope="module")
def content():
    return load_content()


@pytest.fixture
def game(content):
    game = Game(dice=ScriptedDice([]), content=content)
    game.create_character(life=7, sanity=6, food=3)
    return game


@pytest.fixture
def home(game):
    """A game whose character stands Home, in the middle of the first sheet."""
    game.choose_home(Position(2, 2))
    return game


def walk(game, *positions):
    for position in positions:
        game.move(position)


def fill_first_sheet(game):
    """Visit all 30 boxes of the first sheet (every box entered once at least)."""
    for row in range(6):
        for column in range(5):
            game.number_box(Position(column, row))


# --- Sheets and positions ----------------------------------------------------------------


@pytest.mark.parametrize(
    ("position", "sheet"),
    [
        (Position(0, 0), Position(0, 0)),
        (Position(4, 5), Position(0, 0)),
        (Position(5, 0), Position(1, 0)),
        (Position(0, 6), Position(0, 1)),
        (Position(-1, 0), Position(-1, 0)),
        (Position(-5, -6), Position(-1, -1)),
        (Position(-6, 0), Position(-2, 0)),
    ],
)
def test_a_sheet_is_a_5_by_6_block_of_the_grid(position, sheet):
    assert sheet_of(position) == sheet


# --- Neighbours --------------------------------------------------------------------------


def test_a_box_in_the_middle_has_eight_neighbours():
    assert len(neighbours(Position(2, 2), ALL_FIRST_SHEET)) == 8


def test_neighbours_include_diagonals():
    assert Position(3, 3) in neighbours(Position(2, 2), ALL_FIRST_SHEET)


def test_a_box_is_not_its_own_neighbour():
    assert Position(2, 2) not in neighbours(Position(2, 2), ALL_FIRST_SHEET)


def test_a_corner_of_the_first_sheet_has_three_neighbours():
    assert neighbours(Position(0, 0), ALL_FIRST_SHEET) == {
        Position(1, 0),
        Position(0, 1),
        Position(1, 1),
    }


def test_an_edge_box_has_five_neighbours():
    assert len(neighbours(Position(2, 0), ALL_FIRST_SHEET)) == 5


def test_boxes_across_a_seam_are_neighbours():
    # given two sheets side by side
    sheets = {Position(0, 0), Position(1, 0)}
    # then the last column of the first sheet touches the first column of the second
    assert Position(5, 2) in neighbours(Position(4, 2), sheets)
    assert Position(5, 3) in neighbours(Position(4, 2), sheets)
    assert Position(4, 2) in neighbours(Position(5, 3), sheets)


def test_open_edges_are_walls_where_there_is_no_sheet():
    assert Position(5, 2) not in neighbours(Position(4, 2), ALL_FIRST_SHEET)


# --- Distance ----------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("a", "b", "expected"),
    [
        (Position(0, 0), Position(0, 0), 0),
        (Position(0, 0), Position(1, 0), 1),
        (Position(0, 0), Position(1, 1), 1),
        (Position(0, 0), Position(3, 0), 3),
        (Position(0, 0), Position(2, 1), 2),
        (Position(0, 0), Position(3, 2), 3),
        (Position(4, 2), Position(5, 2), 1),  # across a seam
        (Position(-1, -1), Position(1, 1), 2),
    ],
)
def test_distance_is_the_larger_of_the_column_and_row_gaps(a, b, expected):
    assert distance(a, b) == expected
    assert distance(b, a) == expected


# --- Home --------------------------------------------------------------------------------


def test_home_is_box_1_anywhere_on_the_first_sheet(game):
    # when the player chooses Home
    number = game.choose_home(Position(3, 4))
    # then it is box 1, the character stands there, and the first sheet exists
    assert number == 1
    assert game.campaign.position == Position(3, 4)
    assert game.campaign.home == Position(3, 4)
    assert game.campaign.map.boxes[Position(3, 4)].numbers == [1]
    assert game.campaign.map.sheets == {FIRST}


@pytest.mark.parametrize("position", [Position(5, 0), Position(0, 6), Position(-1, 0)])
def test_home_must_be_on_the_first_sheet(game, position):
    with pytest.raises(GameError):
        game.choose_home(position)


def test_home_is_chosen_once_per_campaign(home):
    with pytest.raises(GameError):
        home.choose_home(Position(1, 1))


def test_a_move_needs_a_home_first(game):
    with pytest.raises(GameError):
        game.move(Position(1, 1))


def test_choosing_home_does_not_cost_food(home):
    assert home.character.food == 3


# --- Moves -------------------------------------------------------------------------------


def test_a_move_enters_a_neighbour_and_numbers_it(home):
    # when the character moves to a neighbouring box
    arrival = home.move(Position(3, 3))
    # then the box gets the next number and the character stands in it
    assert arrival.number == 2
    assert home.campaign.position == Position(3, 3)
    assert home.campaign.map.boxes[Position(3, 3)].numbers == [2]
    assert home.campaign.box_counter == 2


def test_a_move_to_a_box_that_is_not_a_neighbour_is_refused(home):
    with pytest.raises(GameError):
        home.move(Position(4, 4))
    assert home.campaign.position == Position(2, 2)
    assert home.campaign.box_counter == 1


def test_a_move_cannot_stay_in_place(home):
    with pytest.raises(GameError):
        home.move(Position(2, 2))


def test_a_move_off_the_sheet_is_refused(game):
    game.choose_home(Position(4, 2))
    with pytest.raises(GameError):
        game.move(Position(5, 2))


def test_coming_back_to_a_box_writes_a_new_number_in_it(home):
    # when the character leaves Home and comes back
    walk(home, Position(3, 2), Position(2, 2))
    # then Home keeps both numbers (the box number is the clock)
    assert home.campaign.map.boxes[Position(2, 2)].numbers == [1, 3]


def test_targets_of_a_normal_move_are_the_neighbours_on_the_map(home):
    assert home.targets() == neighbours(Position(2, 2), ALL_FIRST_SHEET)


def test_targets_without_a_home_are_an_error(game):
    with pytest.raises(GameError):
        game.targets()


def test_moves_are_logged(home, caplog):
    with caplog.at_level("INFO", logger="alone_against_fear"):
        home.move(Position(3, 3))
    assert "box 2" in caplog.text


# --- Escape ------------------------------------------------------------------------------


def test_escape_goes_to_a_visited_neighbour(home):
    # given a character who came from (3, 3) back to (3, 2)... and visited (2, 3) too
    walk(home, Position(3, 3), Position(3, 2))
    # then an Escape can only go back to boxes already visited
    assert home.targets(MoveKind.ESCAPE) == {Position(2, 2), Position(3, 3)}


def test_escape_with_no_visited_neighbour_goes_to_any_neighbour(home):
    # given the first box, the only one visited, which is where the character stands
    # (the character's own box is not a neighbour, so no neighbour is visited yet)
    assert home.targets(MoveKind.ESCAPE) == neighbours(Position(2, 2), ALL_FIRST_SHEET)


def test_escape_moves_like_any_move(home):
    walk(home, Position(3, 3))
    arrival = home.move(Position(2, 2), MoveKind.ESCAPE)
    assert arrival.number == 3
    assert home.campaign.position == Position(2, 2)


def test_escape_to_an_unvisited_box_is_refused_when_a_visited_one_exists(home):
    walk(home, Position(3, 3))
    with pytest.raises(GameError):
        home.move(Position(4, 4), MoveKind.ESCAPE)


# --- Food every 5 boxes ------------------------------------------------------------------


def test_the_character_eats_on_every_fifth_box_number(home):
    # given Home is box 1; boxes 2, 3 and 4 cost nothing
    walk(home, Position(3, 2), Position(3, 3), Position(2, 3))
    assert home.character.food == 3
    # when box 5 is entered
    arrival = home.move(Position(2, 2))
    # then 1 Food is eaten
    assert arrival.number == 5
    assert arrival.upkeep is Upkeep.ATE
    assert home.character.food == 2


def test_other_boxes_have_no_upkeep(home):
    assert home.move(Position(3, 3)).upkeep is None


def test_the_next_meal_is_five_boxes_later(home):
    box = [Position(3, 2), Position(3, 3)]
    for _ in range(9):  # boxes 2 to 10
        home.move(box[_ % 2])
    # Food was eaten at 5 and 10 only
    assert home.character.food == 1


def test_without_food_the_character_loses_1_life_instead(game):
    # given a character with no Food
    game.create_character(life=7, sanity=6, food=0)
    game.choose_home(Position(2, 2))
    walk(game, Position(3, 2), Position(3, 3), Position(2, 3))
    # when box 5 is entered
    arrival = game.move(Position(2, 2))
    # then 1 Life is lost and Food stays at 0
    assert arrival.upkeep is Upkeep.STARVED
    assert game.character.life == 6
    assert game.character.food == 0


def test_the_meal_follows_the_campaign_clock_not_the_character(game):
    # given a campaign at box 3 whose character dies; a new one continues it
    game.choose_home(Position(2, 2))
    walk(game, Position(3, 2), Position(3, 3))
    game.create_character(life=7, sanity=6, food=2)
    # when the new character enters boxes 4 and 5
    game.move(Position(2, 3))
    arrival = game.move(Position(2, 2))
    # then the boxes do not reset: box 5 is a meal for the newcomer too
    assert arrival.number == 5
    assert game.character.food == 1


# --- Sheets ------------------------------------------------------------------------------


def test_a_sheet_is_full_when_all_30_boxes_are_visited(game):
    game.choose_home(Position(0, 0))
    assert not game.is_full(FIRST)
    fill_first_sheet(game)
    assert game.is_full(FIRST)


def test_a_sheet_with_29_boxes_is_not_full(game):
    game.choose_home(Position(0, 0))
    fill_first_sheet(game)
    del game.campaign.map.boxes[Position(4, 5)]
    assert not game.is_full(FIRST)


def test_a_new_sheet_attaches_against_a_full_sheet(game):
    game.choose_home(Position(0, 0))
    fill_first_sheet(game)
    game.add_sheet(Position(1, 0))
    assert game.campaign.map.sheets == {FIRST, Position(1, 0)}


def test_a_new_sheet_is_refused_while_the_sheet_it_touches_is_not_full(home):
    with pytest.raises(GameError):
        home.add_sheet(Position(1, 0))


def test_a_new_sheet_must_touch_a_sheet_by_a_side(game):
    game.choose_home(Position(0, 0))
    fill_first_sheet(game)
    with pytest.raises(GameError):
        game.add_sheet(Position(1, 1))  # touches only at a corner


def test_a_sheet_cannot_be_added_twice(game):
    game.choose_home(Position(0, 0))
    fill_first_sheet(game)
    with pytest.raises(GameError):
        game.add_sheet(FIRST)


def test_the_character_walks_onto_the_new_sheet(game):
    # given a full first sheet and the character standing on its right edge
    game.choose_home(Position(0, 0))
    fill_first_sheet(game)
    game.campaign.position = Position(4, 2)
    game.add_sheet(Position(1, 0))
    # when the character steps across the seam
    arrival = game.move(Position(5, 2))
    # then the move worked and the new box is numbered
    assert game.campaign.position == Position(5, 2)
    assert arrival.number == 32


def test_a_sheet_can_be_added_on_any_side_including_negative_columns(game):
    game.choose_home(Position(0, 0))
    fill_first_sheet(game)
    game.add_sheet(Position(-1, 0))
    game.add_sheet(Position(0, -1))
    assert Position(-1, 0) in game.campaign.map.sheets
    around = neighbours(Position(0, 0), game.campaign.map.sheets)
    assert {Position(-1, 0), Position(0, -1)} <= around
    # the corner sheet between them was not attached: a wall
    assert Position(-1, -1) not in around


# --- What a box remembers ----------------------------------------------------------------


def test_a_new_box_remembers_nothing(home):
    box = home.campaign.map.boxes[Position(2, 2)]
    assert box.places == []
    assert box.searched is False
    assert box.marks == set()


def test_a_box_remembers_every_place_rolled_in_it(home):
    # a haunted clinic is a Clinic and a Haunted House (rulings)
    home.add_place(Position(2, 2), "table.clinic")
    home.add_place(Position(2, 2), "table.haunted_house")
    assert home.campaign.map.boxes[Position(2, 2)].places == [
        "table.clinic",
        "table.haunted_house",
    ]


def test_a_box_can_be_searched(home):
    home.mark_searched(Position(2, 2))
    assert home.campaign.map.boxes[Position(2, 2)].searched is True


def test_a_box_keeps_its_marks(home):
    home.add_mark(Position(2, 2), "safe_house")
    home.add_mark(Position(2, 2), "safe_house")
    assert home.campaign.map.boxes[Position(2, 2)].marks == {"safe_house"}


def test_a_box_can_lose_a_mark(home):
    # Flauros deletes Safe Houses and churches
    home.add_mark(Position(2, 2), "safe_house")
    home.remove_mark(Position(2, 2), "safe_house")
    assert home.campaign.map.boxes[Position(2, 2)].marks == set()


def test_what_a_box_remembers_needs_a_visited_box(home):
    with pytest.raises(GameError):
        home.mark_searched(Position(0, 0))
    with pytest.raises(GameError):
        home.add_mark(Position(0, 0), "safe_house")
    with pytest.raises(GameError):
        home.add_place(Position(0, 0), "table.clinic")


def test_box_memory_survives_the_character(home):
    # the map is the campaign's: a new character finds the Searched box and the marks
    home.mark_searched(Position(2, 2))
    home.add_mark(Position(2, 2), "safe_house")
    home.create_character(life=7, sanity=6, food=2)
    box = home.campaign.map.boxes[Position(2, 2)]
    assert box.searched and "safe_house" in box.marks
