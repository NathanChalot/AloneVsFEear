"""E9: the inventory data in the rules text (design/inventory.md, rulings Inventory). Spot
checks written from the book: what "Negligible weight", "counts as 2 carried items", "if
worn" and "two handed" say, and the ammo types of `3_combat.md` (Keep Track of Ammo)."""

import re

import pytest

from alone_against_fear.content import load_content
from alone_against_fear.content.model import AMMO_TYPES
from alone_against_fear.effect_targets import Parameter

CONTENT = load_content()


def item_entry(item_id):
    return CONTENT.entry(CONTENT.items[item_id][0])


def text(item_id):
    return " ".join(item_entry(item_id).text.split())


LIGHT = [
    "item.religious_symbol",
    "item.salt",
    "item.garlic_heads",
    "item.lighter",
    "item.silver_necklace",
    "item.rubber_mask",
    "item.train_ticket",
    "item.small_bell",
    "item.cheap_holy_symbol_or_beads",
    "item.egyptian_scarab",
    "item.protein_bars",
    "item.cell_phone",
    "item.silver_ring",
    "item.backpack",
]


@pytest.mark.parametrize("item_id", LIGHT)
def test_negligible_weight_takes_no_slot(item_id):
    assert item_entry(item_id).slots == 0


def test_every_text_saying_negligible_weight_is_light():
    said = {
        item_id
        for item_id in CONTENT.items
        if re.search(r"(^|\. |, )[Nn]egligible weight\.", text(item_id))
    }
    assert said == set(LIGHT) - {"item.backpack"}


def test_every_other_item_takes_one_slot_but_smelting_equipment_and_body_armor():
    two = {"item.smelting_equipment", "item.body_armor"}
    for item_id in CONTENT.items:
        expected = 0 if item_id in LIGHT else 2 if item_id in two else 1
        assert item_entry(item_id).slots == expected, item_id


WORN = {
    "item.body_armor": 2,
    "item.helmet": 0,
    "item.dark_clothes": 0,
    "item.stylish_clothes": 0,
    "item.sport_clothes": 0,
    "item.gas_mask": 0,
    "item.leather_jacket": 0,
    "item.crescent_shaped_silver_amulet": 0,
}


def test_only_items_whose_text_says_worn_can_be_worn():
    wearable = {item_id: item_entry(item_id).worn for item_id in CONTENT.items}
    assert {k: v for k, v in wearable.items() if v is not None} == WORN


@pytest.mark.parametrize(
    ("item_id", "unit"),
    [
        ("item.first_aid_kit", "points"),
        ("item.salt", "doses"),
        ("item.holy_water", "vials"),
        ("item.dog_food", "cans"),
        ("item.cat_food", "jars"),
        ("item.liquor", "bottles"),
        ("item.strong_coffee", "drinks"),
    ],
)
def test_a_count_whose_name_does_not_say_what_it_counts_has_a_unit(item_id, unit):
    assert item_entry(item_id).unit == unit


def test_shotgun_shells_are_ammo_not_an_item():
    entry = CONTENT.table("table.random_objects").entry_for(46)
    assert (entry.ammo, entry.item, entry.count) == ("shells", None, "d6")
    assert "item.shotgun_shells" not in CONTENT.items


TWO_HANDED = [
    "weapon.axe",
    "weapon.bow",
    "weapon.chainsaw",
    "weapon.chair",
    "weapon.crossbow",
    "weapon.hockey_stick",
    "weapon.golf_club",
    "weapon.pitchfork",
    "weapon.rifle",
    "weapon.scythe",
    "weapon.shovel",
]


def test_two_handed_weapons_need_two_hands_and_the_others_one():
    for weapon in [*CONTENT.weapons.values(), *CONTENT.variants.values()]:
        expected = 2 if weapon.id in TWO_HANDED else 1
        if weapon.variants:
            continue
        assert weapon.hands == expected, weapon.id


@pytest.mark.parametrize(
    ("weapon_id", "ammo"),
    [
        ("weapon.pistol", "bullets"),
        ("weapon.rifle", "rifle_bullets"),
        ("weapon.crossbow", "bolts"),
        ("weapon.bow", "arrows"),
        ("weapon.shotgun", "shells"),
    ],
)
def test_ranged_weapons_name_their_ammo_type(weapon_id, ammo):
    assert CONTENT.weapon(weapon_id).ammo == ammo
    assert ammo in AMMO_TYPES


def test_the_backpack_raises_the_carry_and_food_limits_by_5_in_one_group():
    for entry_id in CONTENT.items["item.backpack"]:
        effects = {(e.parameter, e.basic, e.group) for e in CONTENT.entry(entry_id).effects}
        assert effects == {
            (Parameter.CARRY_LIMIT, 5, "backpack"),
            (Parameter.FOOD_LIMIT, 5, "backpack"),
        }


def test_strong_raises_the_carry_limit_by_3_or_5():
    effects = CONTENT.skill("skill.strong").effects
    carry = [e for e in effects if e.parameter is Parameter.CARRY_LIMIT]
    assert [(e.basic, e.expert) for e in carry] == [(3, 5)]
