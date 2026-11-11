"""T1: drills, short scoped runs played in a break. A drill sets up a start through the engine
(a pregenerated character, a situation), then the game loop runs as usual until the drill's
natural end, told as `End.DRILL_OVER`. No rule changes.

Scenarios are played by a scripted interface that gives the answers in order.
"""

import pytest

from alone_against_fear.content import load_content
from alone_against_fear.dice import ScriptedDice
from alone_against_fear.engine import Game, Position, drills
from alone_against_fear.engine.creation import Points
from alone_against_fear.engine.game import Purchase
from alone_against_fear.engine.loop import play
from alone_against_fear.engine.protocol import (
    Action,
    Book,
    Choose,
    EffectEnded,
    End,
    Ended,
    FoodUpkeep,
    Topic,
)
from alone_against_fear.engine.state import SkillLevel, Upkeep
from alone_against_fear.interface.scripted import ScriptedInterface

ANNA = "pregenerated.anna_miller"
DOUGLAS = "pregenerated.douglas_harrison"
HOME = Position(2, 2)
# Ten moves from Home, all on the first sheet: down, then back up the next column.
WALK = [
    Position(2, 3),
    Position(2, 4),
    Position(2, 5),
    Position(3, 5),
    Position(3, 4),
    Position(3, 3),
    Position(3, 2),
    Position(3, 1),
    Position(3, 0),
    Position(2, 0),
]
EXPLORE = (3, 3, 4)
"""A new box: Town Exploration 6 (3 and 3) sends to the Street table, whose d6 shows 4."""


@pytest.fixture(scope="module")
def content():
    return load_content()


def new_game(content, *faces):
    return Game(dice=ScriptedDice(faces), content=content)


def moves(*positions):
    """A turn spent moving to a new box, for each position; the Street table is not copied
    yet, so the player says its text leads nowhere else."""
    answers = []
    for position in positions:
        answers += [Action.MOVE, position, Book.DONE]
    return answers


def asked_topics(interface):
    return [request.topic for request in interface.asked if isinstance(request, Choose)]


# --- The loop stops when told -----------------------------------------------------------------


def test_the_loop_stops_at_the_drills_end(content):
    # given a game whose character exists, and a stop at box 3
    game = new_game(content, *EXPLORE * 2)
    game.create_character(life=8, sanity=8, food=3)
    interface = ScriptedInterface([HOME, *moves(*WALK[:2])])

    # when it is played
    end = play(game, interface, stop=lambda g: g.campaign.box_counter >= 3)

    # then it stops before the next action, and says the drill is over
    assert end is End.DRILL_OVER
    assert interface.told[-1] == Ended(End.DRILL_OVER)
    assert interface.remaining == 0


def test_death_ends_a_drill_first(content):
    # given a character with no Food and 1 Life, and a stop at box 2
    game = new_game(content)
    game.create_character(life=1, sanity=8, food=0)
    game.campaign.last_meal = -4
    interface = ScriptedInterface([HOME, Action.MOVE, WALK[0]])

    # when the first move brings a meal they cannot eat
    end = play(game, interface, stop=lambda g: g.campaign.box_counter >= 2)

    # then they die, whatever the drill says
    assert end is End.DEAD


# --- The drills ---------------------------------------------------------------------------------


def test_the_drills_are_named():
    assert list(drills.DRILLS) == ["creation", "walk", "lasting", "xp"]
    assert all(drill.about for drill in drills.DRILLS.values())


def test_a_drill_with_a_pregenerated_character_asks_which(content):
    game = new_game(content)
    interface = ScriptedInterface([DOUGLAS, HOME, Action.QUIT])

    drills.run("walk", game, interface)

    assert interface.asked[0] == Choose(Topic.PREGENERATED, (ANNA, DOUGLAS))
    assert game.character.name == "Douglas Harrison"


def test_the_creation_drill_ends_once_the_character_is_made(content):
    # given a new campaign: a pistol (5, then 3 and 4 bullets), a rope (1, 1), a small bell
    # (1, 3), 4 Food
    game = new_game(content, 5, 3, 4, 1, 1, 1, 3, 4)
    creating = ["Ann", Points.STATS, 2, "skill.agile", "skill.tough", "weapon.knife"]
    interface = ScriptedInterface(creating)

    # when the creation drill is played
    end = drills.run("creation", game, interface)

    # then the character is made and the drill ends before Home is asked
    assert end is End.DRILL_OVER
    assert game.character.name == "Ann"
    assert Topic.HOME not in asked_topics(interface)
    assert game.campaign.home is None


def test_the_walk_drill_ends_after_ten_boxes(content):
    # given Anna Miller at Home
    game = new_game(content, *EXPLORE * len(WALK))
    interface = ScriptedInterface([ANNA, HOME, *moves(*WALK)])

    # when she walks ten boxes
    end = drills.run("walk", game, interface)

    # then the drill ends in box 11, with her two meals eaten (boxes 5 and 10)
    assert end is End.DRILL_OVER
    assert game.campaign.box_counter == 11
    assert interface.remaining == 0
    assert game.character.food == 2


def test_the_walk_drill_can_be_quit(content):
    game = new_game(content, *EXPLORE)
    interface = ScriptedInterface([ANNA, HOME, *moves(WALK[0]), Action.QUIT])

    assert drills.run("walk", game, interface) is End.QUIT


def test_the_lasting_drill_runs_meals_and_an_effect_that_ends(content):
    # given the lasting drill with Douglas Harrison
    game = new_game(content, *EXPLORE * 6)
    interface = ScriptedInterface([DOUGLAS, HOME, *moves(*WALK[:6])])

    # when it is played: Home, then six boxes
    end = drills.run("lasting", game, interface)

    # then he starts with Eating Disorder (a meal every 3 boxes) and a lasting effect for
    # the next 3 boxes, set once Home is chosen
    assert game.character.mental_scars == ["mental_scar.eating_disorder"]
    # meals at boxes 3 and 6
    assert interface.told.count(FoodUpkeep(Upkeep.ATE)) == 2
    assert game.character.food == 2
    # the effect ends as box 5 starts, and nothing else lasts
    assert [e for e in interface.told if isinstance(e, EffectEnded)] != []
    assert game.character.lasting == []
    # the drill ends in box 7
    assert end is End.DRILL_OVER
    assert game.campaign.box_counter == 7


def test_the_lasting_drills_effect_ends_on_entering_box_5(content):
    game = new_game(content, *EXPLORE * 4)
    interface = ScriptedInterface([ANNA, HOME, *moves(*WALK[:3]), Action.QUIT])

    drills.run("lasting", game, interface)

    (lasting,) = game.character.lasting
    assert game.ends_at(lasting) == 5


def test_the_xp_drill_buys_a_skill_and_an_expert_level(content):
    # given the xp drill with Anna Miller (Will 6 XP, Occultist 4 XP)
    game = new_game(content)
    will = Purchase("skill.will", SkillLevel.EXPERT, 6)
    agile = Purchase("skill.agile", SkillLevel.BASIC, 8)
    interface = ScriptedInterface([ANNA, HOME, Action.SPEND_XP, will, Action.SPEND_XP, agile])

    # when she raises her dearest Skill to Expert and buys the dearest new one
    end = drills.run("xp", game, interface)

    # then her XP was just enough, and the drill ends once nothing more can be bought
    assert game.character.skills["skill.will"] is SkillLevel.EXPERT
    assert game.character.skills["skill.agile"] is SkillLevel.BASIC
    assert game.character.xp == 0
    assert end is End.DRILL_OVER


def test_an_unknown_drill_is_refused(content):
    with pytest.raises(KeyError):
        drills.run("nothing", new_game(content), ScriptedInterface([]))
