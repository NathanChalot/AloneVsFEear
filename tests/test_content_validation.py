"""The content checks catch broken tables: each check is tried on a small made-up
content, so a check that never fires cannot pass unnoticed."""

import textwrap

import pytest

from alone_against_fear.content import (
    ContentError,
    coverage_problems,
    load_content,
    note_problems,
    reference_problems,
)


def write(root, name, text):
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(text))


def d6_table(entries, id_="table.test", extra=""):
    return f"id: {id_}\nname: Test table\ndice: d6\nsource: test.md\n{extra}entries:\n{entries}"


@pytest.fixture
def root(tmp_path):
    write(tmp_path, "catalogue.yaml", "[]\n")
    return tmp_path


def load_one(root, yaml_text):
    write(root, "tables/test.yaml", yaml_text)
    return load_content(root)


# --- Dice coverage ----------------------------------------------------------


def test_a_table_covering_its_dice_has_no_problem(root):
    content = load_one(root, d6_table("  - {roll: 1-2, text: a}\n  - {roll: 3-6, text: b}\n"))
    assert coverage_problems(content.table("table.test")) == []


def test_a_gap_is_reported(root):
    content = load_one(root, d6_table("  - {roll: 1-2, text: a}\n  - {roll: 4-6, text: b}\n"))
    assert coverage_problems(content.table("table.test")) == ["table.test: no entry for 3"]


def test_an_overlap_is_reported(root):
    content = load_one(root, d6_table("  - {roll: 1-3, text: a}\n  - {roll: 3-6, text: b}\n"))
    assert coverage_problems(content.table("table.test")) == ["table.test: 2 entries for 3"]


def test_a_roll_out_of_range_is_reported(root):
    content = load_one(root, d6_table("  - {roll: 1-7, text: a}\n"))
    assert coverage_problems(content.table("table.test")) == ["table.test: 7 is not on d6"]


def test_a_gap_in_a_nested_table_is_reported(root):
    entries = """\
      - roll: 1-6
        table:
          dice: d6
          entries:
            - {roll: 1-5, text: a}
    """
    content = load_one(root, d6_table(textwrap.indent(textwrap.dedent(entries), "  ")))
    nested = content.entry("table.test.1-6").table
    assert coverage_problems(nested) == ["table.test.1-6: no entry for 6"]


def test_2d6_runs_from_2_to_12(root):
    entries = "  - {roll: 2-11, text: a}\n"
    content = load_one(root, d6_table(entries).replace("dice: d6", "dice: 2d6"))
    assert coverage_problems(content.table("table.test")) == ["table.test: no entry for 12"]


def test_d66_uses_two_digits_from_1_to_6(root):
    entries = "  - {roll: 11-65, text: a}\n"
    content = load_one(root, d6_table(entries).replace("dice: d6", "dice: d66"))
    assert coverage_problems(content.table("table.test")) == ["table.test: no entry for 66"]


def test_a_table_dice_code_is_kept_in_standard_form(root):
    entries = "  - {roll: 3-13, text: a}\n"
    content = load_one(root, d6_table(entries).replace("dice: d6", "dice: 2d6 +1"))
    assert content.table("table.test").dice == "2d6+1"
    assert coverage_problems(content.table("table.test")) == []


def test_an_unknown_dice_code_is_refused(root):
    with pytest.raises(ContentError, match="d7"):
        load_one(root, d6_table("  - {roll: 1-6, text: a}\n").replace("dice: d6", "dice: d7"))


# --- References and notes ---------------------------------------------------


def test_a_reference_to_nothing_is_reported(root):
    content = load_one(root, d6_table("  - {roll: 1-6, text: a, refs: [table.nowhere]}\n"))
    assert reference_problems(content) == ["table.test.1-6: no such ID table.nowhere"]


def test_references_to_a_catalogued_table_or_an_entry_are_valid(root):
    write(
        root,
        "catalogue.yaml",
        "- {id: table.later, name: Later table, dice: d6, source: later.md}\n",
    )
    entries = "  - {roll: 1-3, text: a, refs: [table.later]}\n"
    entries += "  - {roll: 4-6, text: b, refs: [table.test.1-3]}\n"
    content = load_one(root, d6_table(entries))
    assert reference_problems(content) == []


def test_a_note_missing_from_the_table_is_reported(root):
    extra = "notes:\n  known: Some rule.\n"
    entries = "  - {roll: 1-6, text: a, notes: [known, unknown]}\n"
    content = load_one(root, d6_table(entries, extra=extra))
    assert note_problems(content) == ["table.test.1-6: no note unknown in table.test"]


def test_nested_entries_point_to_the_notes_of_the_top_table(root):
    extra = "notes:\n  known: Some rule.\n"
    entries = """\
      - roll: 1-6
        table:
          dice: d6
          entries:
            - {roll: 1-6, text: a, notes: [known]}
    """
    content = load_one(root, d6_table(textwrap.indent(textwrap.dedent(entries), "  "), extra=extra))
    assert note_problems(content) == []


# --- IDs --------------------------------------------------------------------


def test_a_named_entry_is_found_by_its_own_id(root):
    entries = "  - {roll: 1-6, id: mission.test, name: Test, text: a}\n"
    content = load_one(root, d6_table(entries))
    assert content.entry("mission.test").name == "Test"
    assert content.table("table.test").entry_for(4).id == "mission.test"


def test_the_same_id_twice_is_refused(root):
    write(root, "tables/other.yaml", d6_table("  - {roll: 1-6, text: a}\n"))
    with pytest.raises(ContentError, match="table.test"):
        load_one(root, d6_table("  - {roll: 1-6, text: b}\n"))


def test_a_table_both_copied_and_catalogued_is_refused(root):
    write(
        root,
        "catalogue.yaml",
        "- {id: table.test, name: Test table, dice: d6, source: test.md}\n",
    )
    with pytest.raises(ContentError, match="table.test"):
        load_one(root, d6_table("  - {roll: 1-6, text: a}\n"))


# --- Catalogued events ------------------------------------------------------


def test_a_catalogued_event_has_a_number_a_name_and_a_source(root):
    write(
        root,
        "catalogue.yaml",
        "- {id: event.7, name: Some event, source: events.md}\n",
    )
    content = load_content(root)
    event = content.catalogue["event.7"]
    assert (event.number, event.name, event.source) == (7, "Some event", "events.md")
    assert "event.7" in content
    assert content.events() == [event]


def test_references_to_a_catalogued_event_are_valid(root):
    write(root, "catalogue.yaml", "- {id: event.1, name: An event, source: events.md}\n")
    content = load_one(root, d6_table("  - {roll: 1-6, text: a, refs: [event.1]}\n"))
    assert reference_problems(content) == []


def test_a_catalogued_event_with_dice_is_refused(root):
    write(root, "catalogue.yaml", "- {id: event.1, name: E, dice: d6, source: events.md}\n")
    with pytest.raises(ContentError, match="event.1"):
        load_content(root)


def test_a_catalogued_event_needs_a_number_as_its_id(root):
    write(root, "catalogue.yaml", "- {id: event.first, name: E, source: events.md}\n")
    with pytest.raises(ContentError, match="event.first"):
        load_content(root)


# --- A list of weapons (prepared for R3) -------------------------------------
# The weapon summary has no dice: a list of weapons, each with its ID, name and rules text.

WEAPONS = """\
name: Weapon summary table
source: summary.md
weapons:
  - id: weapon.axe
    name: Axe
    text: Two-handed. Damage 2.
  - id: weapon.baseball_bat_or_hammer
    name: Baseball bat or hammer
    text: Damage 1.
"""


def test_a_list_of_weapons_is_loaded_by_id(root):
    write(root, "weapons/weapon_summary.yaml", WEAPONS)

    content = load_content(root)

    axe = content.weapon("weapon.axe")
    assert (axe.name, axe.text, axe.source) == ("Axe", "Two-handed. Damage 2.", "summary.md")
    assert list(content.weapons) == ["weapon.axe", "weapon.baseball_bat_or_hammer"]
    assert "weapon.axe" in content


def test_a_reference_to_a_weapon_is_valid(root):
    write(root, "weapons/weapon_summary.yaml", WEAPONS)
    write(
        root, "tables/test.yaml", d6_table("  - {roll: 1-6, text: An axe., refs: [weapon.axe]}\n")
    )

    assert reference_problems(load_content(root)) == []


def test_a_weapon_defined_twice_is_refused(root):
    write(root, "weapons/weapon_summary.yaml", WEAPONS)
    write(
        root,
        "weapons/more.yaml",
        "name: More\nsource: more.md\nweapons:\n  - {id: weapon.axe, name: Axe, text: x}\n",
    )

    with pytest.raises(ContentError, match="weapon.axe is defined twice"):
        load_content(root)


def test_a_weapon_needs_the_weapon_kind(root):
    write(
        root,
        "weapons/weapon_summary.yaml",
        "name: W\nsource: w.md\nweapons:\n  - {id: item.axe, name: Axe, text: x}\n",
    )

    with pytest.raises(ContentError, match=r"item\.axe: a weapon ID starts with weapon\."):
        load_content(root)


def test_a_weapon_with_an_unknown_key_is_refused(root):
    write(
        root,
        "weapons/weapon_summary.yaml",
        "name: W\nsource: w.md\nweapons:\n  - {id: weapon.axe, name: Axe, text: x, damage: 2}\n",
    )

    with pytest.raises(ContentError, match=r"weapon\.axe: unknown keys \['damage'\]"):
        load_content(root)


# --- Lists of Skills and Arcane Skills (prepared for R2) ---------------------
# No dice: a list of Skills, each with its ID, name, XP cost and rules text; the Expert
# line apart. Arcane Skills may have components and a sacrifice.

SKILLS = """\
name: Skills
source: skills.md
skills:
  - id: skill.agile
    name: Agile
    xp: 8
    text: Add +1 to your Defense rolls.
    expert: Add +2 to the above.
  - id: skill.bow
    name: Bow
    xp: 3
    text: Ignore the -1 to hit with a bow.
"""

ARCANE_SKILLS = """\
name: Arcane Skills
source: arcane.md
arcane_skills:
  - id: arcane_skill.curse
    name: Curse
    xp: 2
    components: lighter or box of matches.
    sacrifice: 1 candle, 1 dose of bone powder.
    text: You can perform this ritual to prepare a curse.
  - id: arcane_skill.alien_fighter
    name: Alien Fighter
    xp: 3
    text: You gain +1 to Attack and Defense rolls against Aliens.
    expert: the bonus becomes +2.
"""


def test_a_list_of_skills_is_loaded_by_id(root):
    write(root, "skills/skills.yaml", SKILLS)

    content = load_content(root)

    agile = content.skill("skill.agile")
    assert (agile.name, agile.xp, agile.source) == ("Agile", 8, "skills.md")
    assert (agile.text, agile.expert) == ("Add +1 to your Defense rolls.", "Add +2 to the above.")
    assert content.skill("skill.bow").expert is None
    assert list(content.skills) == ["skill.agile", "skill.bow"]
    assert "skill.agile" in content


def test_a_list_of_arcane_skills_is_loaded_by_id(root):
    write(root, "skills/arcane_skills.yaml", ARCANE_SKILLS)

    content = load_content(root)

    curse = content.skill("arcane_skill.curse")
    assert curse.components == "lighter or box of matches."
    assert curse.sacrifice == "1 candle, 1 dose of bone powder."
    assert curse.expert is None
    fighter = content.skill("arcane_skill.alien_fighter")
    assert (fighter.components, fighter.sacrifice) == (None, None)
    assert list(content.arcane_skills) == ["arcane_skill.curse", "arcane_skill.alien_fighter"]
    assert list(content.skills) == []
    assert "arcane_skill.curse" in content


def test_a_reference_to_a_skill_is_valid(root):
    write(root, "skills/skills.yaml", SKILLS)
    write(root, "skills/arcane_skills.yaml", ARCANE_SKILLS)
    write(
        root,
        "tables/test.yaml",
        d6_table("  - {roll: 1-6, text: Learn., refs: [skill.agile, arcane_skill.curse]}\n"),
    )

    assert reference_problems(load_content(root)) == []


def test_a_skill_defined_twice_is_refused(root):
    write(root, "skills/skills.yaml", SKILLS)
    write(
        root,
        "skills/more.yaml",
        "name: More\nsource: m.md\nskills:\n  - {id: skill.agile, name: A, xp: 1, text: x}\n",
    )

    with pytest.raises(ContentError, match="skill.agile is defined twice"):
        load_content(root)


@pytest.mark.parametrize(
    ("key", "id_", "message"),
    [
        ("skills", "arcane_skill.curse", r"a Skill ID starts with skill\."),
        ("arcane_skills", "skill.curse", r"an Arcane Skill ID starts with arcane_skill\."),
    ],
)
def test_a_skill_needs_the_kind_of_its_list(root, key, id_, message):
    write(
        root,
        "skills/test.yaml",
        f"name: S\nsource: s.md\n{key}:\n  - {{id: {id_}, name: C, xp: 2, text: x}}\n",
    )

    with pytest.raises(ContentError, match=message):
        load_content(root)


@pytest.mark.parametrize("xp", ["8 XP", "true", "0"])
def test_a_skills_xp_cost_is_a_positive_whole_number(root, xp):
    write(
        root,
        "skills/skills.yaml",
        f"name: S\nsource: s.md\nskills:\n  - {{id: skill.agile, name: A, xp: {xp}, text: x}}\n",
    )

    with pytest.raises(ContentError, match=r"skill\.agile: the XP cost"):
        load_content(root)


def test_only_an_arcane_skill_has_components(root):
    write(
        root,
        "skills/skills.yaml",
        "name: S\nsource: s.md\nskills:\n"
        "  - {id: skill.agile, name: A, xp: 8, text: x, components: incense}\n",
    )

    with pytest.raises(ContentError, match=r"skill\.agile: unknown keys \['components'\]"):
        load_content(root)


# --- Named entries of the harm tables (prepared for R2) ----------------------


def test_injuries_and_mental_scars_are_kinds_of_their_own():
    from alone_against_fear.content import KINDS

    assert {"skill", "arcane_skill", "injury", "mental_scar"} <= KINDS
