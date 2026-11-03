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
from alone_against_fear.effect_targets import Parameter, RollType, Tag


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


# --- Weapon variants (E6) -------------------------------------------------------
# A summary heading that names two weapons keeps its text once; each weapon it names is a
# variant with its own ID and name, so the character holds the exact one.

VARIANTS = """\
name: Weapon summary table
source: summary.md
weapons:
  - id: weapon.baseball_bat_or_hammer
    name: Baseball bat or hammer
    text: Damage 1.
    variants:
      - {id: weapon.baseball_bat, name: Baseball bat}
      - {id: weapon.hammer, name: Hammer}
"""


def test_a_variant_is_a_weapon_with_the_headings_text(root):
    write(root, "weapons/weapon_summary.yaml", VARIANTS)

    content = load_content(root)

    hammer = content.weapon("weapon.hammer")
    assert (hammer.name, hammer.text, hammer.source) == ("Hammer", "Damage 1.", "summary.md")
    assert hammer.heading == "weapon.baseball_bat_or_hammer"
    heading = content.weapon("weapon.baseball_bat_or_hammer")
    assert heading.variants == ("weapon.baseball_bat", "weapon.hammer")
    assert list(content.weapons) == ["weapon.baseball_bat_or_hammer"]  # the summary as printed
    assert "weapon.hammer" in content


def test_a_reference_to_a_variant_is_valid(root):
    write(root, "weapons/weapon_summary.yaml", VARIANTS)
    write(root, "tables/test.yaml", d6_table("  - {roll: 1-6, text: x, refs: [weapon.hammer]}\n"))

    assert reference_problems(load_content(root)) == []


def test_a_variant_needs_the_weapon_kind(root):
    write(root, "weapons/weapon_summary.yaml", VARIANTS.replace("weapon.hammer", "item.hammer"))

    with pytest.raises(ContentError, match=r"item\.hammer: a weapon ID starts with weapon\."):
        load_content(root)


def test_a_variant_defined_twice_is_refused(root):
    write(
        root,
        "weapons/weapon_summary.yaml",
        VARIANTS + "  - {id: weapon.hammer, name: Hammer, text: x}\n",
    )

    with pytest.raises(ContentError, match="weapon.hammer is defined twice"):
        load_content(root)


def test_a_variant_with_an_unknown_key_is_refused(root):
    write(
        root,
        "weapons/weapon_summary.yaml",
        VARIANTS.replace("name: Hammer}", "name: Hammer, damage: 2}"),
    )

    with pytest.raises(ContentError, match=r"weapon\.hammer: unknown keys \['damage'\]"):
        load_content(root)


def test_a_variant_may_add_a_sentence_of_its_own(root):
    # the hammer's uses, which the baseball bat does not share (E6, with the user)
    write(
        root,
        "weapons/weapon_summary.yaml",
        VARIANTS.replace("name: Hammer}", "name: Hammer, extra: Drives stakes.}"),
    )

    content = load_content(root)

    assert content.weapon("weapon.hammer").text == "Damage 1. Drives stakes."
    assert content.weapon("weapon.hammer").extra == "Drives stakes."
    assert content.weapon("weapon.baseball_bat").text == "Damage 1."


# --- Items and counts (E6) ------------------------------------------------------
# An entry that gives a thing names it: `item` for an item (two tables may give the same
# one), `refs` for a weapon. `count` is how many the entry gives: a dice code or a number,
# or one per ID when the entry gives a choice of things.


def test_two_entries_may_give_the_same_item(root):
    content = load_one(
        root,
        d6_table(
            "  - {roll: 1-3, text: Backpack., item: item.backpack}\n"
            "  - {roll: 4-6, text: A backpack., item: item.backpack}\n"
        ),
    )

    assert content.entry("table.test.1-3").item == "item.backpack"
    assert content.items["item.backpack"] == ("table.test.1-3", "table.test.4-6")
    assert "item.backpack" in content


def test_an_item_needs_the_item_kind(root):
    with pytest.raises(ContentError, match=r"an item ID starts with item\."):
        load_one(root, d6_table("  - {roll: 1-6, text: x, item: weapon.backpack}\n"))


def test_a_count_is_a_dice_code_or_a_number(root):
    content = load_one(
        root,
        d6_table(
            "  - {roll: 1-2, text: d6 garlic., item: item.garlic, count: d6}\n"
            "  - {roll: 3-4, text: Salt (6 doses)., item: item.salt, count: 6}\n"
            "  - {roll: 5-6, text: 2d6 candles., item: item.candles, count: 2D6}\n"
        ),
    )

    assert content.entry("table.test.1-2").count_of("item.garlic") == "d6"
    assert content.entry("table.test.3-4").count_of("item.salt") == 6
    assert content.entry("table.test.5-6").count_of("item.candles") == "2d6"  # standard form


def test_a_count_may_be_given_per_thing(root):
    content = load_one(
        root,
        d6_table(
            "  - roll: 1-6\n"
            "    text: 1 Grenade or bow with 2d6+3 arrows (choose).\n"
            "    refs: [weapon.grenade, weapon.bow]\n"
            "    count: {weapon.bow: 2d6+3}\n"
        ),
    )

    entry = content.entry("table.test.1-6")
    assert entry.count_of("weapon.bow") == "2d6+3"
    assert entry.count_of("weapon.grenade") is None


def test_a_count_that_is_not_dice_is_refused(root):
    with pytest.raises(ContentError, match="a few"):
        load_one(root, d6_table("  - {roll: 1-6, text: x, item: item.x, count: a few}\n"))


def test_a_count_for_a_thing_the_entry_does_not_give_is_refused(root):
    with pytest.raises(ContentError, match=r"count for weapon\.axe"):
        load_one(
            root,
            d6_table("  - {roll: 1-6, text: x, refs: [weapon.bow], count: {weapon.axe: d6}}\n"),
        )


def test_items_are_a_kind_of_their_own():
    from alone_against_fear.content import KINDS

    assert "item" in KINDS


def test_uses_are_how_many_times_one_item_can_be_used(root):
    # count: how many objects; uses: how many times a single object serves (E6, the user)
    content = load_one(
        root,
        d6_table(
            "  - {roll: 1-3, text: First Aid Kit., item: item.first_aid_kit, uses: d6+2}\n"
            "  - {roll: 4-6, text: Strong coffee., item: item.strong_coffee, uses: 6}\n"
        ),
    )

    kit = content.entry("table.test.1-3")
    assert (kit.uses, kit.count_of("item.first_aid_kit")) == ("d6+2", None)
    assert content.entry("table.test.4-6").uses == 6


def test_uses_that_are_not_dice_are_refused(root):
    with pytest.raises(ContentError, match="uses are a dice code or a number"):
        load_one(root, d6_table("  - {roll: 1-6, text: x, item: item.x, uses: often}\n"))


def test_uses_need_an_item(root):
    with pytest.raises(ContentError, match="uses need an item"):
        load_one(root, d6_table("  - {roll: 1-6, text: x, refs: [weapon.bow], uses: 3}\n"))


def test_a_skill_may_give_starting_gear(root):
    # Bow and Faith give gear when taken at creation (E6, the user)
    write(
        root,
        "skills/skills.yaml",
        SKILLS.replace(
            "    text: Ignore the -1 to hit with a bow.\n",
            "    text: Ignore the -1 to hit with a bow.\n"
            "    starting_gear:\n      - {id: weapon.bow, count: d6+3}\n",
        ),
    )

    gear = load_content(root).skill("skill.bow").starting_gear

    assert [(g.id, g.count, g.uses) for g in gear] == [("weapon.bow", "d6+3", None)]


def test_starting_gear_that_does_not_exist_is_reported(root):
    write(
        root,
        "skills/skills.yaml",
        SKILLS.replace(
            "    text: Ignore the -1 to hit with a bow.\n",
            "    text: Ignore the -1 to hit with a bow.\n"
            "    starting_gear:\n      - {id: weapon.bow}\n",
        ),
    )

    assert reference_problems(load_content(root)) == ["skill.bow: no such ID weapon.bow"]


# --- Skill effects (E7) --------------------------------------------------------


def skill_with(effects, expert="Add +2 to the above."):
    expert_line = f"    expert: {expert}\n" if expert else ""
    return (
        "name: S\nsource: s.md\nskills:\n"
        "  - id: skill.agile\n    name: Agile\n    xp: 8\n    text: x\n"
        f"{expert_line}    effects:\n{effects}"
    )


def test_a_skill_effect_on_a_roll_is_loaded(root):
    write(
        root,
        "skills/skills.yaml",
        skill_with(
            "      - {roll: defense, basic: 1, expert: 2, group: agile_or_dodge}\n"
            "      - {roll: save, tags: [climb, jump, avoid_danger], basic: 1, expert: 2}\n"
        ),
    )

    defense, save = load_content(root).skill("skill.agile").effects

    assert (defense.roll, defense.tags, defense.group) == (
        RollType.DEFENSE,
        frozenset(),
        "agile_or_dodge",
    )
    assert (defense.amount(expert=False), defense.amount(expert=True)) == (1, 2)
    assert save.roll is RollType.SAVE
    assert save.tags == {Tag.CLIMB, Tag.JUMP, Tag.AVOID_DANGER}
    assert (save.parameter, save.group) == (None, None)


def test_a_skill_effect_on_a_parameter_is_loaded(root):
    write(
        root,
        "skills/skills.yaml",
        skill_with("      - {parameter: max_life, basic: 2, expert: 3}\n"),
    )

    (effect,) = load_content(root).skill("skill.agile").effects

    assert (effect.parameter, effect.roll, effect.basic, effect.expert) == (
        Parameter.MAX_LIFE,
        None,
        2,
        3,
    )


def test_a_skill_without_effects_has_none(root):
    write(root, "skills/skills.yaml", SKILLS)

    assert load_content(root).skill("skill.agile").effects == ()


@pytest.mark.parametrize(
    ("effect", "message"),
    [
        ("{roll: dance, basic: 1, expert: 2}", "unknown roll type 'dance'"),
        ("{roll: save, tags: [posion], basic: 1, expert: 2}", "unknown tag 'posion'"),
        ("{parameter: max_luck, basic: 1, expert: 2}", "unknown parameter 'max_luck'"),
        ("{basic: 1, expert: 2}", "an effect changes a roll or a parameter"),
        (
            "{roll: save, parameter: max_life, basic: 1, expert: 2}",
            "an effect changes a roll or a parameter",
        ),
        ("{parameter: max_life, tags: [fear], basic: 1, expert: 2}", "tags need a roll"),
        ("{parameter: max_life, group: x, basic: 1, expert: 2}", "a group needs a roll"),
        ("{roll: save, basic: one, expert: 2}", "an amount is a whole number"),
        ("{roll: save, expert: 2}", r"missing keys \['basic'\]"),
        ("{roll: save, basic: 1}", "the Skill has an Expert line: its effects need an expert"),
        ("{roll: save, basic: 1, expert: 2, when: always}", r"unknown keys \['when'\]"),
    ],
)
def test_a_malformed_skill_effect_is_refused(root, effect, message):
    write(root, "skills/skills.yaml", skill_with(f"      - {effect}\n"))

    with pytest.raises(ContentError, match=message):
        load_content(root)


def test_an_effect_of_a_skill_without_expert_line_has_no_expert_amount(root):
    write(
        root,
        "skills/skills.yaml",
        skill_with("      - {roll: save, basic: 1, expert: 2}\n", expert=None),
    )

    with pytest.raises(ContentError, match="no Expert line: its effects have no expert"):
        load_content(root)
