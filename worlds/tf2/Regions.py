from BaseClasses import Region, ItemClassification
from typing import TYPE_CHECKING, Dict
from .Data import (TF2Location, TF2Item, weapon_to_class, TFClass, multiclass_weapons, weapon_kill_names, weapon_list,
                   class_names)
from .Options import WeaponKillObjectiveCountMax, GeneralKillObjectiveCountMax
from worlds.generic.Rules import set_rule

if TYPE_CHECKING:
    from . import TF2World


def create_tf2_objectives(world: "TF2World") -> int:
    menu = Region("Menu", world.player, world.multiworld)
    location_count = 0
    added_weapons = []
    for class_name in world.options.AllowedClasses:
        class_name = class_name.lower().capitalize()
        class_region = Region(f"{class_name} Objectives", world.player, world.multiworld)
        menu.connect(class_region, f"-> {class_name} Objectives",
                     lambda state, c=class_name: state.has(c, world.player))

        # create general kill objectives (per class)
        min_objectives = min(world.options.GeneralKillObjectiveCountMin.value,
                             world.options.GeneralKillObjectiveCountMax.value)
        max_objectives = max(world.options.GeneralKillObjectiveCountMax.value,
                             world.options.GeneralKillObjectiveCountMin.value)

        contract_point_loc = TF2Location(world.player, f"Contract Point - {class_name} Kills", None)
        contract_point_loc.place_locked_item(
            TF2Item("Contract Point", ItemClassification.progression, None, world.player))
        contract_point_loc.show_in_spoiler = False
        contract_point_loc.parent_region = class_region
        class_region.locations.append(contract_point_loc)
        world.total_objectives += 1

        count = world.random.randint(min_objectives, max_objectives)
        world.class_kill_counts.setdefault(class_name, count)
        for i in range(count):
            loc_name = f"{class_name} General Kill #{i + 1}"
            loc = TF2Location(world.player, loc_name, get_location_id(class_name) + i)
            loc.parent_region = class_region
            class_region.locations.append(loc)
            location_count += 1

        # create weapon objectives
        min_objectives = min(world.options.WeaponKillObjectiveCountMin.value, world.options.WeaponKillObjectiveCountMax.value)
        max_objectives = max(world.options.WeaponKillObjectiveCountMax.value, world.options.WeaponKillObjectiveCountMin.value)
        for weapon in world.available_weapons:
            class_type = TFClass[class_name.upper()]
            weapon_dict = weapon_kill_names[class_type]
            if weapon not in weapon_dict.values() or weapon in added_weapons:
                continue

            added_weapons.append(weapon)
            count = world.random.randint(min_objectives, max_objectives)
            world.weapon_kill_counts.setdefault(weapon, count)
            for i in range(count):
                loc_name = f"{weapon} Kill #{i+1}"
                loc = TF2Location(world.player, loc_name, get_location_id(weapon)+i)
                loc.parent_region = class_region
                set_rule(loc, lambda state, w=weapon: state.has(w, world.player))
                class_region.locations.append(loc)
                location_count += 1

            contract_point_loc = TF2Location(world.player, f"Contract Point - {weapon} Kills", None)
            contract_point_loc.place_locked_item(
                TF2Item("Contract Point", ItemClassification.progression, None, world.player))
            contract_point_loc.show_in_spoiler = False
            contract_point_loc.parent_region = class_region
            set_rule(contract_point_loc, lambda state, w=weapon: state.has(w, world.player))
            class_region.locations.append(contract_point_loc)
            world.total_objectives += 1

        world.multiworld.regions.append(class_region)

    world.multiworld.regions.append(menu)
    print(f"Total Locations = {location_count}")
    return location_count


def get_location_id(name: str) -> int:
    # fix conflicts
    if name == "Hot Hand":
        return 30725
    elif name == "Manmelter":
        return 30960
    elif name == "Equalizer":
        return 20900
    elif name == "Gunslinger":
        return 61000
    elif name == "Direct Hit":
        return 62000

    try:
        class_type: TFClass = TFClass[name.upper()]
        if class_type != TFClass.UNKNOWN:
            return int(class_type) * 100
    except KeyError:
        pass

    class_type = TFClass.UNKNOWN
    try:
        class_type = TFClass[weapon_to_class.get(name).upper()]
    except AttributeError:
        pass

    weapon_id: int
    if name in multiclass_weapons:
        weapon_id = 20000
    elif class_type != TFClass.UNKNOWN:
        weapon_id = int(class_type) * 10000
    else:
        raise Exception(f"Can't generate location ID for '{name}'")

    ascii_values = list(name.encode('ascii'))
    for val in ascii_values:
        weapon_id += val

    return weapon_id


def get_location_ids() -> Dict[str, int]:
    location_ids = {}
    for class_name in class_names:
        for i in range(GeneralKillObjectiveCountMax.range_end):
            loc_name = f"{class_name} - General Kill #{i+1}"
            location_ids.setdefault(loc_name, get_location_id(class_name)+i)

    for weapon in weapon_list:
        for i in range(WeaponKillObjectiveCountMax.range_end):
            loc_name = f"{weapon} - Kill #{i+1}"
            location_ids.setdefault(loc_name, get_location_id(weapon)+i)

    return location_ids
