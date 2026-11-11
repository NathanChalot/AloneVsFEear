"""E7: rolls and effects (design/effects.md, design/rolls.md).

A roll has a type and context tags; it collects the modifiers of every effect held that
matches, with stacking limits. Max values and the other parameters are a base plus the
effects held. Every Skill is written as effects: each one is tested here, from the rules text
(`gameRules/1_2_skills.md`) and the rulings (design/rulings.md, Character). What a Skill does
beyond a number waits for the task that has its moment (pending tests at the end).
"""

import pytest

from alone_against_fear.content import load_content
from alone_against_fear.dice import ScriptedDice
from alone_against_fear.effect_targets import Parameter, RollType, Tag
from alone_against_fear.engine import Game, GameError, Stat
from alone_against_fear.engine.effects import Modifier
from alone_against_fear.engine.game import Purchase
from alone_against_fear.engine.state import Position, SkillLevel


@pytest.fixture(scope="module")
def content():
    return load_content()


def character(content, *skills, expert=(), faces=(), life=10, sanity=9):
    """A character holding these Skills at Basic, the ones in `expert` at Expert."""
    game = Game(dice=ScriptedDice(list(faces)), content=content)
    game.create_character(life=life, sanity=sanity, food=3, skills=skills)
    for skill in expert:
        game.character.skills[skill] = SkillLevel.EXPERT
    return game


def total(game, roll, *tags):
    return sum(m.amount for m in game.roll_modifiers(roll, frozenset(tags)).applied)


# --- Every Skill's roll modifiers ----------------------------------------------------------


ROLL_MODIFIERS = [
    # Skill, the roll it changes, its tags, Basic, Expert
    ("skill.agile", RollType.DEFENSE, (), 1, 2),
    ("skill.agile", RollType.SAVE, (Tag.CLIMB,), 1, 2),
    ("skill.agile", RollType.SAVE, (Tag.JUMP,), 1, 2),
    ("skill.agile", RollType.SAVE, (Tag.AVOID_DANGER,), 1, 2),
    ("skill.bow", RollType.ATTACK, (Tag.BOW,), 1, 2),
    ("skill.charisma", RollType.CHARISMA, (), 1, 2),
    ("skill.dodge", RollType.DEFENSE, (), 1, 2),
    ("skill.fighter", RollType.ATTACK, (Tag.HAND_TO_HAND,), 1, 2),
    ("skill.good_shot", RollType.ATTACK, (Tag.RANGED,), 1, 2),
    ("skill.good_shot", RollType.ATTACK, (Tag.BOW,), 1, 2),
    ("skill.investigator", RollType.SEARCH, (), 1, 2),
    ("skill.martial_arts", RollType.ATTACK, (Tag.UNARMED,), 1, 2),
    ("skill.occultist", RollType.MAGIC, (), 1, 2),
    ("skill.resilient", RollType.SAVE, (Tag.POISON,), 1, 2),
    ("skill.resilient", RollType.SAVE, (Tag.INFECTION,), 1, 2),
    ("skill.resilient", RollType.SAVE, (Tag.DISEASE,), 1, 2),
    ("skill.slippery", RollType.ESCAPE, (), 1, 2),
    ("skill.stealth", RollType.STEALTH, (), 1, 2),
    ("skill.strong", RollType.STRENGTH, (), 1, 2),
    ("skill.vampire_hunter", RollType.ATTACK, (Tag.VAMPIRE,), 1, 2),
    ("skill.will", RollType.WILL, (), 1, 2),
    ("skill.will", RollType.SAVE, (Tag.FEAR,), 1, 2),
    ("skill.will", RollType.SAVE, (Tag.MAGIC,), 1, 2),
    ("skill.will", RollType.SAVE, (Tag.HYPNOTISM,), 1, 2),  # at Expert too (ruling)
    ("skill.will", RollType.SAVE, (Tag.PSIONICS,), 1, 2),
    ("skill.zombie_hunter", RollType.ATTACK, (Tag.ZOMBIE,), 1, 2),
]


@pytest.mark.parametrize(("skill", "roll", "tags", "basic", "expert"), ROLL_MODIFIERS)
def test_a_skill_modifies_its_rolls_at_basic_and_expert(content, skill, roll, tags, basic, expert):
    # given a character with the Skill; when a matching roll is made; then its bonus applies
    assert total(character(content, skill), roll, *tags) == basic
    assert total(character(content, skill, expert=[skill]), roll, *tags) == expert


@pytest.mark.parametrize(("skill", "roll", "tags", "basic", "expert"), ROLL_MODIFIERS)
def test_a_skill_names_itself_as_the_source(content, skill, roll, tags, basic, expert):
    applied = character(content, skill).roll_modifiers(roll, frozenset(tags)).applied
    assert applied == (Modifier(skill, basic),)


@pytest.mark.parametrize(
    ("skill", "roll", "tags"),
    [
        ("skill.fighter", RollType.ATTACK, (Tag.RANGED,)),
        ("skill.fighter", RollType.ATTACK, (Tag.UNARMED,)),  # "No bonus on unarmed attacks"
        ("skill.fighter", RollType.DEFENSE, ()),
        ("skill.good_shot", RollType.ATTACK, (Tag.HAND_TO_HAND,)),
        ("skill.bow", RollType.ATTACK, (Tag.RANGED,)),  # a gun is no bow
        ("skill.resilient", RollType.SAVE, (Tag.FEAR,)),
        ("skill.resilient", RollType.SAVE, ()),
        ("skill.agile", RollType.SAVE, (Tag.POISON,)),
        ("skill.will", RollType.SAVE, (Tag.POISON,)),
        ("skill.will", RollType.MAGIC, ()),  # casting is Occultist's, not a save vs magic
        ("skill.vampire_hunter", RollType.ATTACK, (Tag.ZOMBIE,)),
        ("skill.charisma", RollType.STEALTH, ()),
    ],
)
def test_a_skill_leaves_other_rolls_alone(content, skill, roll, tags):
    assert total(character(content, skill), roll, *tags) == 0


def test_a_character_without_skills_has_no_modifier(content):
    game = character(content)
    assert game.roll_modifiers(RollType.DEFENSE, frozenset()) == ((), ())


# --- Stacking --------------------------------------------------------------------------------


def test_modifiers_of_different_skills_stack(content):
    # Good Shot and Bow both count on a bow Attack (rulings: modifiers stack)
    game = character(content, "skill.good_shot", "skill.bow")
    assert total(game, RollType.ATTACK, Tag.BOW) == 2


def test_several_tags_can_match_one_roll(content):
    # a hand-to-hand Attack against a vampire: Fighter and Vampire Hunter
    game = character(content, "skill.fighter", "skill.vampire_hunter", expert=["skill.fighter"])
    assert total(game, RollType.ATTACK, Tag.HAND_TO_HAND, Tag.VAMPIRE) == 3


def test_agile_and_dodge_do_not_stack_the_higher_applies(content):
    # given Agile at Basic and Dodge at Expert ("Use one or the other", ruling: the higher)
    game = character(content, "skill.agile", "skill.dodge", expert=["skill.dodge"])
    # when a Defense roll collects its modifiers
    modifiers = game.roll_modifiers(RollType.DEFENSE, frozenset())
    # then Dodge's +2 applies and Agile's +1 is set aside, for the player to see
    assert modifiers.applied == (Modifier("skill.dodge", 2),)
    assert modifiers.set_aside == (Modifier("skill.agile", 1),)


def test_agile_and_dodge_at_the_same_level_give_one_bonus(content):
    game = character(content, "skill.agile", "skill.dodge")
    modifiers = game.roll_modifiers(RollType.DEFENSE, frozenset())
    assert [m.amount for m in modifiers.applied] == [1]
    assert len(modifiers.set_aside) == 1


def test_agile_still_counts_on_saves_with_dodge(content):
    # the group is only the Defense bonus
    game = character(content, "skill.agile", "skill.dodge")
    assert total(game, RollType.SAVE, Tag.CLIMB) == 1


# --- Every Skill's parameters ------------------------------------------------------------


@pytest.mark.parametrize(
    ("skill", "parameter", "base", "basic", "expert"),
    [
        ("skill.danger_sense", Parameter.SURPRISE_CHANCE, 3, 2, 1),
        ("skill.danger_sense", Parameter.SURPRISE_CHANCE, 1, 0, 0),  # "no chance to surprise"
        ("skill.investigator", Parameter.CLUE_COST, 3, 2, 1),
        ("skill.investigator", Parameter.CLUE_COST, 2, 1, 1),  # "to a minimum of 1"
        ("skill.resistant_to_hunger", Parameter.FOOD_INTERVAL, None, 6, 7),
        ("skill.strong", Parameter.CARRY_LIMIT, None, 13, 15),
        ("skill.tough", Parameter.MAX_LIFE, None, 12, 13),
        ("skill.strong_grip_on_reality", Parameter.MAX_SANITY, None, 10, 11),
    ],
)
def test_a_skill_changes_its_parameter(content, skill, parameter, base, basic, expert):
    assert character(content, skill).parameter(parameter, base) == basic
    assert character(content, skill, expert=[skill]).parameter(parameter, base) == expert


@pytest.mark.parametrize(
    ("parameter", "value"),
    [
        (Parameter.MAX_LIFE, 10),
        (Parameter.MAX_SANITY, 9),
        (Parameter.CARRY_LIMIT, 10),
        (Parameter.FOOD_INTERVAL, 5),
    ],
)
def test_a_parameter_without_effects_is_its_base(content, parameter, value):
    assert character(content).parameter(parameter) == value


@pytest.mark.parametrize("parameter", [Parameter.SURPRISE_CHANCE, Parameter.CLUE_COST])
def test_a_parameter_whose_base_comes_from_the_text_needs_it(content, parameter):
    with pytest.raises(GameError, match="needs a base"):
        character(content).parameter(parameter)


# --- Max values ------------------------------------------------------------------------------


def test_the_max_is_calculated_from_the_effects(content):
    game = character(content, "skill.tough", "skill.strong_grip_on_reality")
    assert (game.max(Stat.LIFE), game.max(Stat.SANITY)) == (12, 10)


def test_a_character_created_with_tough_starts_at_the_raised_max(content):
    # the starting Life is the base; Tough raises the max and the current Life
    game = character(content, "skill.tough", "skill.strong_grip_on_reality", life=9, sanity=10)
    assert (game.character.life, game.character.sanity) == (11, 11)
    assert (game.character.base_life, game.character.base_sanity) == (9, 10)


def test_buying_tough_raises_max_and_current_life_without_healing(content):
    # design/character.md: 6/10 becomes 8/12
    game = character(content)
    game.lose(Stat.LIFE, 4)
    game.character.xp = 8
    game.buy(Purchase("skill.tough", SkillLevel.BASIC, 8))
    assert (game.character.life, game.max(Stat.LIFE)) == (8, 12)


def test_raising_tough_to_expert_adds_the_difference(content):
    # an Expert amount replaces the Basic one (ruling): +3 in all, so 1 more
    game = character(content, "skill.tough")
    game.character.xp = 8
    game.buy(Purchase("skill.tough", SkillLevel.EXPERT, 8))
    assert (game.character.life, game.max(Stat.LIFE)) == (13, 13)


def test_buying_strong_grip_on_reality_raises_max_and_current_sanity(content):
    game = character(content)
    game.character.xp = 6
    game.buy(Purchase("skill.strong_grip_on_reality", SkillLevel.BASIC, 6))
    assert (game.character.sanity, game.max(Stat.SANITY)) == (10, 10)


def test_healing_stops_at_the_raised_max(content):
    game = character(content, "skill.tough")
    game.lose(Stat.LIFE, 5)
    assert game.gain(Stat.LIFE, 9) == 12


# --- Rolls collect their modifiers -------------------------------------------------------


def test_a_roll_vs_l_adds_the_skills_and_the_texts_modifier(content):
    # given Resilient; when a save vs poison is rolled at -1 from a note
    game = character(content, "skill.resilient", faces=[4])
    rolled = game.roll_vs(5, RollType.SAVE, frozenset({Tag.POISON}), modifier=-1)
    # then the total is 4 + 1 - 1, and each modifier says where it comes from
    assert rolled.modifiers == (Modifier("skill.resilient", 1), Modifier(None, -1))
    assert (rolled.face, rolled.modifier, rolled.total, rolled.success) == (4, 0, 4, False)


def test_a_roll_vs_l_keeps_its_type_tags_and_what_was_set_aside(content):
    game = character(content, "skill.agile", "skill.dodge", faces=[3])
    rolled = game.roll_vs(4, RollType.DEFENSE)
    assert (rolled.roll, rolled.tags) == (RollType.DEFENSE, frozenset())
    assert rolled.set_aside == (Modifier("skill.dodge", 1),)
    assert rolled.success


def test_a_bow_attack_carries_the_ranged_tag(content):
    rolled = character(content, faces=[3]).roll_vs(3, RollType.ATTACK, frozenset({Tag.BOW}))
    assert rolled.tags == {Tag.BOW, Tag.RANGED}


def test_a_natural_1_fails_whatever_the_skills(content):
    game = character(content, "skill.charisma", expert=["skill.charisma"], faces=[1])
    rolled = game.roll_vs(2, RollType.CHARISMA)
    assert (rolled.total, rolled.success) == (3, False)


def test_investigator_adds_to_the_search_roll(content):
    game = character(content, "skill.investigator", faces=[4])
    game.choose_home(Position(0, 0))
    searched = game.search()
    assert searched.modifiers == (Modifier("skill.investigator", 1),)
    assert searched.rolled.results == (5,)


def test_a_search_roll_of_1_stays_1_with_investigator(content):
    game = character(content, "skill.investigator", expert=["skill.investigator"], faces=[1])
    game.choose_home(Position(0, 0))
    assert game.search(modifier=1).rolled.results == (1,)


# --- What waits for later tasks ---------------------------------------------------------


@pytest.mark.skip(reason="E12: Dodge, a natural 1 on Defense gives -1 to the next Attack")
def test_dodge_loses_balance_on_a_natural_1():
    pass


@pytest.mark.skip(reason="E12: Faith turns vampires like Exorcism, at +1 at Expert")
def test_faith_turns_vampires_with_a_holy_symbol():
    pass


@pytest.mark.skip(reason="E11: Medic heals up to 3 (Expert 4) Life from a first aid kit")
def test_medic_heals_after_an_encounter():
    pass


# --- Injuries and Mental Scars (E8) ------------------------------------------------------
# Held by ID; their effects are written in their table entries, with a single amount.


def test_eating_disorder_shortens_the_food_interval_to_3(content):
    game = character(content)

    game.gain_mental_scar("mental_scar.eating_disorder")

    assert game.character.mental_scars == ["mental_scar.eating_disorder"]
    assert game.parameter(Parameter.FOOD_INTERVAL) == 3


@pytest.mark.parametrize(("expert", "interval"), [((), 4), (("skill.resistant_to_hunger",), 5)])
def test_eating_disorder_stacks_with_resistant_to_hunger(content, expert, interval):
    # design/rulings.md, Character: Eating Disorder is -2, the Skill still adds
    game = character(content, "skill.resistant_to_hunger", expert=expert)

    game.gain_mental_scar("mental_scar.eating_disorder")

    assert game.parameter(Parameter.FOOD_INTERVAL) == interval


def test_the_food_interval_is_never_below_1(content):
    game = character(content)
    game.gain_mental_scar("mental_scar.eating_disorder")

    assert game.parameter(Parameter.FOOD_INTERVAL, base=2) == 1


def test_a_mental_scar_or_injury_is_held_once(content):
    game = character(content)
    game.gain_mental_scar("mental_scar.eating_disorder")
    game.gain_injury("injury.limping")

    with pytest.raises(GameError, match="already"):
        game.gain_mental_scar("mental_scar.eating_disorder")
    with pytest.raises(GameError, match="already"):
        game.gain_injury("injury.limping")
    assert game.character.injuries == ["injury.limping"]


@pytest.mark.parametrize(
    ("method", "id_"),
    [
        ("gain_mental_scar", "injury.limping"),
        ("gain_injury", "mental_scar.eating_disorder"),
        ("gain_injury", "injury.no_such_thing"),
    ],
)
def test_only_an_entry_of_its_table_can_be_gained(content, method, id_):
    with pytest.raises(GameError):
        getattr(character(content), method)(id_)
