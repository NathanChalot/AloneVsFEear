"""T2: the terminal's own wording, kept in YAML (`interface/screens/`).

A key is the file name, then the nested keys, joined by dots; a text names the fields to fill
in. The rules text the engine relies on stays in `content/`.
"""

import pytest

from alone_against_fear.interface.screen_text import (
    ScreenText,
    ScreenTextError,
    load_screen_text,
)


def write(folder, name, text):
    (folder / name).write_text(text, encoding="utf-8")
    return folder


def test_a_key_is_the_file_name_then_the_nested_keys(tmp_path):
    folder = write(tmp_path, "creation.yaml", "intro: Hello\npoints:\n  heading: Step 2\n")

    text = load_screen_text(folder)

    assert text.keys == {"creation.intro", "creation.points.heading"}
    assert text("creation.points.heading") == "Step 2"


def test_a_text_fills_in_its_fields():
    text = ScreenText({"creation.skills.prompt": "Skill {n} of {count}? "})

    assert text("creation.skills.prompt", n=1, count=2) == "Skill 1 of 2? "


def test_a_missing_key_or_field_is_an_error():
    text = ScreenText({"creation.skills.prompt": "Skill {n} of {count}? "})

    with pytest.raises(ScreenTextError, match="no screen text 'creation.nope'"):
        text("creation.nope")
    with pytest.raises(ScreenTextError, match="needs the field 'count'"):
        text("creation.skills.prompt", n=1)


def test_a_value_that_is_not_a_text_is_an_error(tmp_path):
    folder = write(tmp_path, "town.yaml", "status: 3\n")

    with pytest.raises(ScreenTextError, match="town.status is not a text"):
        load_screen_text(folder)


def test_the_keys_used_are_remembered():
    text = ScreenText({"a.b": "B", "a.c": "C"})

    text("a.b")

    assert text.used == {"a.b"}


def test_the_screens_load():
    assert "creation.intro" in load_screen_text().keys
