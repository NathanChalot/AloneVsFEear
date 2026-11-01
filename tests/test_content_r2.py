"""R2: the Skills, the Arcane Skills and the Insanity and Injury tables copied into YAML.
Spot checks are written from the book (see docs/content.md)."""

import re

import pytest

from alone_against_fear.content import coverage_problems, load_content, reference_problems

CONTENT = load_content()
INSANITY = CONTENT.table("table.insanity")
INJURY = CONTENT.table("table.injury")

SKILLS = [
    ("Agile", 8),
    ("Bow", 3),
    ("Charisma", 3),
    ("Danger Sense", 4),
    ("Dodge", 4),
    ("Faith", 2),
    ("Fighter", 6),
    ("Good Shot", 8),
    ("Investigator", 6),
    ("Martial Arts", 3),
    ("Medic", 3),
    ("Occultist", 4),
    ("Resilient", 3),
    ("Resistant To Hunger", 2),
    ("Strong Grip On Reality", 6),
    ("Slippery", 3),
    ("Stealth", 4),
    ("Strong", 5),
    ("Tough", 8),
    ("Vampire Hunter", 3),
    ("Will", 6),
    ("Zombie Hunter", 2),
]

ARCANE_SKILLS = [
    ("Alien Fighter", 3),
    ("Curse", 2),
    ("Demon Slayer", 3),
    ("Energy of the Macrocosmos", 3),
    ("Exorcism", 2),
    ("Foretell", 2),
    ("Gate", 2),
    ("Healing", 4),
    ("Mutant Hunter", 2),
    ("Pentagram", 4),
    ("Summon Servitor", 2),
]

# --- The two tables ----------------------------------------------------------


@pytest.mark.parametrize("table", [INSANITY, INJURY], ids=lambda t: t.id)
def test_the_table_covers_its_dice_range(table):
    assert table.dice == "d6"
    assert coverage_problems(table) == []


def test_the_two_tables_are_no_longer_catalogued():
    for id_ in ("table.insanity", "table.injury"):
        assert id_ in CONTENT.tables
        assert id_ not in CONTENT.catalogue


def test_the_tables_have_their_names_and_sources_and_no_text_of_their_own():
    assert (INSANITY.name, INSANITY.source) == (
        "Insanity table",
        "gameRules/tables/3_1_insanity_table.md",
    )
    assert (INJURY.name, INJURY.source) == (
        "Injury table",
        "gameRules/tables/3_2_injury_table.md",
    )


def test_both_tables_carry_the_mental_scars_and_injuries_section():
    for table in (INSANITY, INJURY):
        assert table.text.startswith("When you lose Sanity points in any event or encounter")
        assert "rolling on the Insanity table. You may do so up to 3 times" in table.text
        assert "Likewise, you may do the same with Life points" in table.text
        assert table.text.endswith(
            "When you roll a Mental Scar or Injury that you already have, reroll until you "
            "select one you do not have."
        )
        assert len(table.text.split("\n\n")) == 3


def test_the_insanity_table_has_six_named_entries_in_order():
    assert [(e.roll.label, e.id, e.name) for e in INSANITY.entries] == [
        ("1", "mental_scar.paranoia", "Paranoia"),
        ("2", "mental_scar.eating_disorder", "Eating Disorder"),
        ("3", "mental_scar.absent_mindedness", "Absent Mindedness"),
        ("4", "mental_scar.phobic", "Phobic"),
        ("5", "mental_scar.overconfidence", "Overconfidence"),
        ("6", "mental_scar.shaky", "Shaky"),
    ]


def test_the_injury_table_has_six_named_entries_in_order():
    assert [(e.roll.label, e.id, e.name) for e in INJURY.entries] == [
        ("1", "injury.facial_scar", "Facial scar"),
        ("2", "injury.impaired_arm", "Impaired arm"),
        ("3", "injury.eye_damage", "Eye damage"),
        ("4", "injury.limping", "Limping"),
        ("5", "injury.brain_damage", "Brain damage"),
        ("6", "injury.crippled_arm", "Crippled arm"),
    ]


def test_the_two_merged_insanity_rows_are_split():
    assert INSANITY.entry_for(2).text == "You require 1 Food every 3 boxes."
    assert INSANITY.entry_for(3).text.startswith("Every time you need a material component")
    assert INSANITY.entry_for(3).text.endswith(
        "If you have no Safe House in play, the item is lost."
    )


def test_insanity_and_injury_texts_as_printed():
    assert INSANITY.entry_for(1).text == (
        "When you meet helpful people, you may not accept their Food or healing."
    )
    assert INSANITY.entry_for(4).text == (
        "You have -1 on all rolls made to avoid losing Sanity or to resist Fear effects "
        "of any kind."
    )
    assert INSANITY.entry_for(6).text == "Your maximum Sanity is permanently lowered by 1."
    assert INJURY.entry_for(3).text == "You have a permanent -1 to your ranged Attack rolls."
    assert INJURY.entry_for(6).text == (
        "You lose the use of one arm. You may no longer use weapons that require two hands. "
        "You may still use rifles and shotguns with a -1 penalty."
    )


def test_no_entry_text_repeats_its_name_or_has_ocr_spacing():
    for table in (INSANITY, INJURY):
        for entry in table.entries:
            assert not entry.text.startswith(entry.name)
            assert "  " not in entry.text and " ." not in entry.text and "\n" not in entry.text


# --- Checks over the lists ---------------------------------------------------


def test_every_reference_resolves():
    assert reference_problems(CONTENT) == []


def test_no_page_reference_is_left():
    for skill in [*CONTENT.skills.values(), *CONTENT.arcane_skills.values()]:
        for field in (skill.text, skill.expert, skill.components, skill.sacrifice):
            assert not re.search(r"\bp\.\s*\d+", field or ""), skill.id
        assert "see p" not in skill.text


def test_no_ocr_spacing_is_left():
    for skill in [*CONTENT.skills.values(), *CONTENT.arcane_skills.values()]:
        for field in (skill.text, skill.expert, skill.components, skill.sacrifice):
            assert "  " not in (field or ""), skill.id
            assert " ." not in (field or ""), skill.id
            assert "'" not in (field or ""), skill.id


# --- The Skills --------------------------------------------------------------


def test_there_are_22_skills_in_the_books_order_with_their_xp_costs():
    assert [(s.name, s.xp) for s in CONTENT.skills.values()] == SKILLS


def test_skill_ids_follow_the_names():
    assert list(CONTENT.skills)[:3] == ["skill.agile", "skill.bow", "skill.charisma"]
    assert "skill.good_shot" in CONTENT.skills
    assert "skill.strong_grip_on_reality" in CONTENT.skills
    assert "skill.resistant_to_hunger" in CONTENT.skills
    assert all(s.source == "gameRules/1_2_skills.md" for s in CONTENT.skills.values())


def test_every_skill_has_an_expert_line_and_no_ritual_fields():
    for skill in CONTENT.skills.values():
        assert skill.expert, skill.id
        assert skill.components is None and skill.sacrifice is None, skill.id


def test_a_note_printed_after_the_expert_line_ends_the_text():
    agile = CONTENT.skill("skill.agile")
    assert agile.expert == "Add +2 to the above."
    assert agile.text == (
        "Add +1 to your Defense rolls and rolls performed to climb, jump, or avoid danger.\n\n"
        "The bonus to Defense rolls does not stack with the bonus from the Dodge Skill. "
        "Use one or the other."
    )
    dodge = CONTENT.skill("skill.dodge")
    assert dodge.text.endswith(
        "The bonus from Dodge does not stack with the bonus from the Agile Skill. "
        "Use one or the other."
    )
    assert dodge.expert == (
        "You have +2 to Defense rolls, but you still lose your balance when you roll a 1 "
        "on a Defense roll."
    )


@pytest.mark.parametrize(
    ("id_", "text", "expert"),
    [
        (
            "skill.charisma",
            "You have +1 to Charisma rolls (rolls to persuade someone).",
            "+2 to Charisma rolls.",
        ),
        (
            "skill.martial_arts",
            "Reduce the unarmed combat modifier to -1.",
            "reduce it to no penalty.",
        ),
        ("skill.occultist", "You have +1 to any Magic roll.", "You have +2 to Magic rolls."),
        ("skill.zombie_hunter", "Add +1 to your Attack rolls against zombies.", "Add +2."),
    ],
)
def test_skill_text_and_expert_as_printed(id_, text, expert):
    skill = CONTENT.skill(id_)
    assert (skill.text, skill.expert) == (text, expert)


def test_the_faith_page_reference_is_removed():
    text = CONTENT.skill("skill.faith").text
    assert text.startswith(
        "You may attempt to turn vampires with a holy symbol. "
        "It works like the Exorcism Arcane Skill. You automatically begin"
    )


def test_danger_sense_quotes_are_the_books():
    assert (
        "“the ghost has a 3 in 6 chance of surprising you”"
        in CONTENT.skill("skill.danger_sense").text
    )


def test_the_will_expert_line_is_as_printed():
    assert CONTENT.skill("skill.will").expert == (
        "Add +2 to your Will rolls and saves vs. Fear, Magic or Psionics."
    )


# --- The Arcane Skills -------------------------------------------------------


def test_there_are_11_arcane_skills_in_the_books_order_with_their_xp_costs():
    assert [(s.name, s.xp) for s in CONTENT.arcane_skills.values()] == ARCANE_SKILLS
    assert list(CONTENT.arcane_skills)[:2] == [
        "arcane_skill.alien_fighter",
        "arcane_skill.curse",
    ]
    assert "arcane_skill.energy_of_the_macrocosmos" in CONTENT.arcane_skills
    assert all(s.source == "gameRules/1_3_arcane_skills.md" for s in CONTENT.arcane_skills.values())


def test_which_arcane_skills_have_an_expert_line():
    assert {s.name for s in CONTENT.arcane_skills.values() if s.expert} == {
        "Alien Fighter",
        "Demon Slayer",
        "Exorcism",
        "Mutant Hunter",
    }


def test_which_arcane_skills_have_components_and_sacrifices():
    have_components = {s.name for s in CONTENT.arcane_skills.values() if s.components}
    assert have_components == {
        "Curse",
        "Energy of the Macrocosmos",
        "Exorcism",
        "Foretell",
        "Gate",
        "Healing",
        "Pentagram",
        "Summon Servitor",
    }
    have_sacrifice = {s.name for s in CONTENT.arcane_skills.values() if s.sacrifice}
    assert have_sacrifice == {
        "Curse",
        "Energy of the Macrocosmos",
        "Foretell",
        "Healing",
        "Pentagram",
        "Summon Servitor",
    }


@pytest.mark.parametrize(
    ("id_", "components", "sacrifice"),
    [
        ("arcane_skill.curse", "lighter or box of matches.", "1 candle, 1 dose of bone powder."),
        ("arcane_skill.energy_of_the_macrocosmos", "incense", "1 candle or 2 Food"),
        ("arcane_skill.foretell", "Black mirror", "1 candle"),
        ("arcane_skill.gate", "none", None),
        ("arcane_skill.healing", "Food, Holy Book", "1 Food, 1 Candle"),
        ("arcane_skill.pentagram", "art materials, ritual dagger", "7 candles."),
        (
            "arcane_skill.summon_servitor",
            "bell, ritual dagger",
            "5 candles or 2 Life points (your choice).",
        ),
    ],
)
def test_components_and_sacrifice_as_printed(id_, components, sacrifice):
    skill = CONTENT.skill(id_)
    assert (skill.components, skill.sacrifice) == (components, sacrifice)


def test_exorcism_components_keep_the_printed_list():
    assert CONTENT.skill("arcane_skill.exorcism").components == (
        "1 of the following:\n- Holy water\n- Incense\n- Essential oils"
    )


def test_exorcism_text_and_expert():
    exorcism = CONTENT.skill("arcane_skill.exorcism")
    assert exorcism.text.startswith(
        "You may learn this Arcane Skill from one of the following books:\n\n"
        "- Holy Book\n- The Occult Guide\n- The Diabolical Deal\n\n"
        "You may expel a demon or spirit"
    )
    assert exorcism.expert == "add +1 to your roll."


def test_the_books_stay_in_the_text():
    assert "They Are Among Us" in CONTENT.skill("arcane_skill.alien_fighter").text
    assert "- The Necronomicon\n- The Diabolical Deal" in CONTENT.skill("arcane_skill.curse").text
    assert (
        "- The Diabolical Deal\n- The Necronomicon" in CONTENT.skill("arcane_skill.pentagram").text
    )


def test_demon_slayer_page_reference_is_removed():
    assert CONTENT.skill("arcane_skill.demon_slayer").text == (
        "You have +1 to saves and Defense rolls vs. any creature from the Demonic Horrors table."
    )


def test_summon_servitor_passage_is_restored_to_the_books_order():
    paragraphs = CONTENT.skill("arcane_skill.summon_servitor").text.split("\n\n")
    control = next(p for p in paragraphs if p.startswith("If you succeed"))
    assert control == (
        "If you succeed, you must now control the creature. Perform a Will roll at +1 if you "
        "have Will, +2 if you have Will (Expert) against the creature’s L. If you fail the "
        "roll, the creature will attack you! You must fight a creature with its L, as many "
        "Life points as its L and Damage 1. You may not escape from this fight."
    )
    assert paragraphs[-1] == (
        "You may attempt to summon another servitor, repeating the same procedure described "
        "above, only when the previous one dies. You may not have two servitors at the same "
        "time. You may at any moment dismiss a controlled Servitor. It will just disappear "
        "if you so wish."
    )
    assert paragraphs[-2].endswith("between yourself and the Servitor.")


def test_gate_lists_how_to_learn_it_as_printed():
    text = CONTENT.skill("arcane_skill.gate").text
    assert "- Read the Necronomicon;\n- Read the Holy Book;\n" in text
    assert text.count("\n- ") == 5
    assert "Roll at +1 if you have Will, and +2 if you have Will (Expert)." in text
