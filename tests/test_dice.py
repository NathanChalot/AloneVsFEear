"""E1: every dice code of the book, written from the Dice Codes section of the main rules.

Rule tests use scripted dice (the faces the dice show, in order); reproducibility tests use
seeded dice.
"""

import logging

import pytest

from alone_against_fear.dice import Chance, DiceCode, DiceError, RandomDice, ScriptedDice


def roll(code: str, *faces: int):
    dice = ScriptedDice(faces)
    result = DiceCode.parse(code).roll(dice)
    assert dice.remaining == 0, "the roll did not use every scripted face"
    return result


# d3: roll a six-sided die and halve it, counting 1-2 as 1, 3-4 as 2, and 5-6 as 3.


@pytest.mark.parametrize(("face", "total"), [(1, 1), (2, 1), (3, 2), (4, 2), (5, 3), (6, 3)])
def test_d3_halves_a_d6(face, total):
    result = roll("d3", face)
    assert result.total == total
    assert result.faces == (face,)


def test_d3_plus_1():
    assert roll("d3+1", 6).total == 4


# d6: roll a six-sided die.


@pytest.mark.parametrize("face", range(1, 7))
def test_d6_is_the_die(face):
    assert roll("d6", face).total == face


# d6 +1: roll a six-sided die and add 1 to the result.
# d6-1: subtract 1, generating a number from 0 to 5.


@pytest.mark.parametrize(
    ("code", "face", "total"),
    [("d6+1", 6, 7), ("d6 +1", 1, 2), ("d6+3", 4, 7), ("d6-1", 1, 0), ("d6-1", 6, 5)],
)
def test_d6_with_a_modifier(code, face, total):
    result = roll(code, face)
    assert result.total == total
    assert result.natural == face


def test_d6_minus_1_ranges_from_0_to_5():
    assert DiceCode.parse("d6-1").results() == (0, 1, 2, 3, 4, 5)


# 2d6: roll two six-sided dice and add them, generating a number 2 to 12.
# 2d6 +1: add 1 to the total, generating a number 3 to 13.


def test_2d6_adds_two_dice():
    result = roll("2d6", 3, 5)
    assert result.total == 8
    assert result.faces == (3, 5)


def test_2d6_ranges_from_2_to_12():
    assert DiceCode.parse("2d6").results() == tuple(range(2, 13))


def test_2d6_plus_1_ranges_from_3_to_13():
    assert roll("2d6 +1", 6, 6).total == 13
    assert DiceCode.parse("2d6+1").results() == tuple(range(3, 14))


@pytest.mark.parametrize(
    ("code", "faces", "total"),
    [("3d6", (1, 2, 3), 6), ("2d6+12", (1, 1), 14), ("12+d6", (4,), 16), ("2d6+3", (6, 5), 14)],
)
def test_other_sums_found_in_the_rules(code, faces, total):
    assert roll(code, *faces).total == total


# d6 x d6: multiply the result of one die by the other, generating a number from 1 to 36.


@pytest.mark.parametrize("code", ["d6 x d6", "d6xd6", "d6×d6"])
def test_d6_times_d6_multiplies(code):
    result = roll(code, 4, 5)
    assert result.total == 20
    assert result.faces == (4, 5)


def test_d6_times_d6_ranges_from_1_to_36():
    results = DiceCode.parse("d6xd6").results()
    assert min(results) == 1 and max(results) == 36
    assert 7 not in results


# d66: the first die as 'tens' and the second as 'units', generating a number from 11 to 66.


def test_d66_reads_tens_then_units():
    result = roll("d66", 3, 5)
    assert result.total == 35
    assert result.faces == (3, 5)


def test_d66_has_36_results_from_11_to_66():
    results = DiceCode.parse("d66").results()
    assert len(results) == 36
    assert results[0] == 11 and results[-1] == 66
    assert 17 not in results and 20 not in results


# A roll result keeps the natural die as well as the total.


def test_the_natural_die_ignores_the_modifier():
    result = roll("d6+3", 6)
    assert result.natural == 6
    assert result.total == 9


def test_the_natural_die_of_a_d3_is_the_d6_shown():
    assert roll("d3", 5).natural == 5


# "x in 6" chances: the chance succeeds on a die showing x or less (our convention: the odds
# are the same whichever faces count).


@pytest.mark.parametrize(
    ("code", "face", "success"),
    [("1 in 6", 1, True), ("1 in 6", 2, False), ("3 in 6", 3, True), ("3 in 6", 4, False)],
)
def test_x_in_6_chance(code, face, success):
    result = Chance.parse(code).roll(ScriptedDice([face]))
    assert result.success is success
    assert result.face == face


def test_a_chance_can_be_built_and_shown():
    assert Chance(2) == Chance.parse("2 in 6")
    assert str(Chance(2)) == "2 in 6"


@pytest.mark.parametrize("code", ["7 in 6", "-1 in 6", "2 in 8", "in 6"])
def test_a_bad_chance_is_refused(code):
    with pytest.raises(DiceError):
        Chance.parse(code)


# Dice codes are plain data: parsed from the printed code, shown back in a standard form.


@pytest.mark.parametrize(
    ("code", "shown"),
    [
        ("d6", "d6"),
        ("D6", "d6"),
        ("d6 +1", "d6+1"),
        ("12+d6", "d6+12"),
        ("d6 x d6", "d6xd6"),
        ("d66", "d66"),
        ("2d6+3", "2d6+3"),
        ("d3", "d3"),
    ],
)
def test_a_dice_code_is_shown_in_standard_form(code, shown):
    assert str(DiceCode.parse(code)) == shown


def test_equal_codes_compare_equal():
    assert DiceCode.parse("12+d6") == DiceCode.parse("d6+12")


@pytest.mark.parametrize("code", ["d7", "d", "2d", "d6+", "d6xd3", "0d6", "6d", "hello", ""])
def test_a_bad_dice_code_is_refused(code):
    with pytest.raises(DiceError):
        DiceCode.parse(code)


# Dice sources: seeded for reproducible runs, scripted for rule tests.


def test_seeded_dice_repeat_the_same_rolls():
    first, second = RandomDice(seed=42), RandomDice(seed=42)
    code = DiceCode.parse("2d6")
    assert [code.roll(first) for _ in range(20)] == [code.roll(second) for _ in range(20)]


def test_unseeded_dice_pick_a_seed_and_log_it(caplog):
    # so a game played with real dice can be played again with the same rolls
    caplog.set_level(logging.INFO, logger="alone_against_fear")
    dice = RandomDice()
    assert isinstance(dice.seed, int)
    assert f"dice seed {dice.seed}" in caplog.messages
    again = RandomDice(seed=dice.seed)
    assert [dice.d6() for _ in range(20)] == [again.d6() for _ in range(20)]


def test_seeded_dice_keep_their_seed():
    assert RandomDice(seed=42).seed == 42


def test_random_dice_only_show_faces_1_to_6():
    dice = RandomDice(seed=1)
    assert {dice.d6() for _ in range(600)} == {1, 2, 3, 4, 5, 6}


def test_scripted_dice_refuse_a_face_that_is_not_on_a_die():
    with pytest.raises(DiceError):
        ScriptedDice([7])


def test_scripted_dice_complain_when_they_run_out():
    dice = ScriptedDice([4])
    dice.d6()
    with pytest.raises(DiceError):
        dice.d6()


# Every roll is written to the log, for debugging.


def test_a_roll_is_logged(caplog):
    with caplog.at_level(logging.DEBUG, logger="alone_against_fear"):
        roll("2d6+1", 3, 4)
    assert "2d6+1" in caplog.text
    assert "8" in caplog.text
