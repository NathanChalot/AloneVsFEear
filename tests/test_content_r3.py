"""R3: the Random Weapon, Random Objects and Useful Stuff tables and the weapon summary
copied into YAML. Spot checks are written from the book (see docs/content.md)."""

import re

import pytest

from alone_against_fear.content import coverage_problems, load_content, reference_problems

CONTENT = load_content()
WEAPON = CONTENT.table("table.random_weapon")
OBJECTS = CONTENT.table("table.random_objects")
STUFF = CONTENT.table("table.useful_stuff")
D66 = [a * 10 + b for a in range(1, 7) for b in range(1, 7)]

# --- Checks ------------------------------------------------------------------


@pytest.mark.parametrize("table", [WEAPON, OBJECTS, STUFF], ids=lambda t: t.id)
def test_the_table_covers_its_dice_range(table):
    assert coverage_problems(table) == []


def test_the_three_tables_are_no_longer_catalogued():
    for id_ in ("table.random_weapon", "table.random_objects", "table.useful_stuff"):
        assert id_ in CONTENT.tables
        assert id_ not in CONTENT.catalogue


def test_dice_and_entry_count():
    assert WEAPON.dice == "d6"
    assert (OBJECTS.dice, STUFF.dice) == ("d66", "d66")
    assert [e.roll.label for e in OBJECTS.entries] == [str(n) for n in D66]
    assert [e.roll.label for e in STUFF.entries] == [str(n) for n in D66]


def test_every_reference_resolves():
    assert reference_problems(CONTENT) == []


def test_no_page_reference_is_left_in_the_items():
    for table in (WEAPON, OBJECTS, STUFF):
        assert all(not re.search(r"\bp\.\s*\d+", e.text) for e in table.entries), table.id


def test_no_row_is_split_across_lines():
    for table in (OBJECTS, STUFF):
        assert all(e.text and e.text[0].isalnum() for e in table.entries), table.id
        assert all("  " not in e.text and " ." not in e.text for e in table.entries)


# --- The weapon summary ------------------------------------------------------


def test_the_weapon_summary_has_the_22_weapons_in_the_books_order():
    assert [w.name for w in CONTENT.weapons.values()] == [
        "Antique flail weapon",
        "Axe",
        "Baseball bat or hammer",
        "Bow",
        "Chainsaw",
        "Chair",
        "Crossbow",
        "Flashlight",
        "Grenade",
        "Hockey Stick/golf club",
        "Kitchen knife/ritual dagger",
        "Knife or stick",
        "Molotov cocktail",
        "Nunchaku",
        "Pistol",
        "Pitchfork",
        "Rifle",
        "Scythe/shovel",
        "Shotgun",
        "Samurai sword (authentic)",
        "Samurai sword (cheap replica)",
        "Unarmed attack",
    ]


@pytest.mark.parametrize(
    ("id_", "text"),
    [
        (
            "weapon.axe",
            "Two-handed. Damage 2. If you are Strong (Expert), you may use it one-handed.",
        ),
        ("weapon.baseball_bat_or_hammer", "+1 to hit zombies and flaming skeletons. Damage 1."),
        ("weapon.crossbow", "2 handed. No bonus. Damage 1. Comes with 2d6 bolts."),
        ("weapon.pistol", "+1 to Attack rolls, Damage 1. Comes with 2d6 bullets."),
        ("weapon.shotgun", "+2 to Attack rolls. Damage 2. Comes with 2d6 shells."),
    ],
)
def test_weapon_text_as_printed(id_, text):
    assert CONTENT.weapon(id_).text == text


def test_two_names_in_a_heading_keep_one_id():
    assert CONTENT.weapon("weapon.hockey_stick_or_golf_club").name == "Hockey Stick/golf club"
    assert CONTENT.weapon("weapon.samurai_sword_authentic").text.endswith("Damage 1.")
    assert (
        "Breaks on an Attack roll of 1."
        in CONTENT.weapon("weapon.samurai_sword_cheap_replica").text
    )


def test_the_molotov_text_is_repaired_from_the_ocr():
    assert "1 zombie or scarecrow or perform" in CONTENT.weapon("weapon.molotov_cocktail").text


# --- Random Weapon -----------------------------------------------------------


@pytest.mark.parametrize(
    ("result", "text", "refs"),
    [
        (1, "Baseball bat or hammer.", ["weapon.baseball_bat_or_hammer"]),
        (
            2,
            "Chainsaw or authentic samurai sword (choose)",
            ["weapon.chainsaw", "weapon.samurai_sword_authentic"],
        ),
        (3, "1 Grenade or bow with 2d6+3 arrows (choose).", ["weapon.grenade", "weapon.bow"]),
        (4, "Shotgun with 2d6 shells.", ["weapon.shotgun"]),
        (5, "Pistol with 2d6 bullets.", ["weapon.pistol"]),
        (6, "Rifle with 2d6 bullets.", ["weapon.rifle"]),
    ],
)
def test_random_weapon(result, text, refs):
    entry = WEAPON.entry_for(result)
    assert entry.text == text
    assert list(entry.refs) == refs


# --- Random Objects and Useful Stuff -----------------------------------------


def test_random_objects_spot_checks():
    assert OBJECTS.entry_for(11).text.startswith("Rope. May be used to climb down")
    assert list(OBJECTS.entry_for(14).refs) == ["weapon.axe"]
    assert OBJECTS.entry_for(14).text == "Axe. See weapon summary table for rules."
    assert (
        OBJECTS.entry_for(26).text
        == "Backpack. Increases by 5 your limit of carried items and Food points."
    )
    assert list(OBJECTS.entry_for(54).refs) == [
        "weapon.samurai_sword_authentic",
        "weapon.samurai_sword_cheap_replica",
    ]
    assert "(not werewolves)." in OBJECTS.entry_for(55).text
    assert OBJECTS.entry_for(56).text == "Creepy looking doll."


def test_random_objects_book_entries_point_to_the_random_book_table():
    assert list(OBJECTS.entry_for(45).refs) == ["table.random_book"]
    entry = OBJECTS.entry_for(61)
    assert entry.text == (
        "Computer print-out. Somebody printed out a whole book. Roll on the Random Book "
        "table, rerolling any result of 2 or 12."
    )
    assert list(entry.refs) == ["table.random_book"]


def test_the_backpack_is_in_both_tables_as_printed():
    assert "Increases by 5" in OBJECTS.entry_for(26).text
    assert STUFF.entry_for(14).text == "Backpack. You may carry 15 objects instead of 10."


def test_useful_stuff_rows_split_across_lines_are_whole():
    assert STUFF.entry_for(15).text.startswith("Body armor. The body armor has 4 Life points.")
    assert "On a 4 or 5, you take the Damage off the body armor." in STUFF.entry_for(15).text
    assert STUFF.entry_for(22).text.endswith("Attack roll of 5 or 6.")
    assert "When the helmet loses its last Life" in STUFF.entry_for(34).text
    assert "you also lose 2 Life." in STUFF.entry_for(55).text
    assert "so it can destroy vampires permanently." in STUFF.entry_for(64).text


def test_useful_stuff_entries_that_give_a_weapon_point_to_it():
    assert list(STUFF.entry_for(22).refs) == ["weapon.antique_flail_weapon"]
    assert list(STUFF.entry_for(53).refs) == ["weapon.kitchen_knife_or_ritual_dagger"]
    assert list(STUFF.entry_for(63).refs) == ["weapon.hockey_stick_or_golf_club"]
    assert list(STUFF.entry_for(64).refs) == ["weapon.molotov_cocktail"]


def test_the_flail_in_useful_stuff_adds_its_expert_rule():
    assert "become a Flail (Expert)" in STUFF.entry_for(22).text
    assert "Expert" not in CONTENT.weapon("weapon.antique_flail_weapon").text
