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
