import worlds.tf2.Options
from worlds.AutoWorld import World
from typing import List, Mapping, Any, Dict, TextIO
from BaseClasses import Item, MultiWorld
from .Options import TF2Options, ol_to_list, MeleeWeaponRules
from .Items import get_item_id, create_item, create_itempool, get_item_ids
from .Regions import create_tf2_objectives, get_location_ids
from .Data import weapon_kill_names, TFClass, weapon_to_class, knives, swords, melee_weapons
from worlds.LauncherComponents import Component, components, icon_paths, launch_subprocess, Type
from Utils import local_path
from math import floor

def launch_client():
    from .Client import launch
    launch_subprocess(launch, name="Client")

components.append(Component("Team Fortress 2 Client", "TF2Client", func=launch_client,
                            component_type=Type.CLIENT))

icon_paths['tf2'] = local_path('data', 'tf2.png')

class TF2World(World):
    """
    One of the most popular online action games of all time,
    Team Fortress 2 delivers constant free updates—new game modes, maps, equipment and, most importantly, hats.
    Nine distinct classes provide a broad range of tactical abilities and personalities,
    and lend themselves to a variety of player skills.
    """

    game = "Team Fortress 2"
    options_dataclass = TF2Options
    options: TF2Options
    item_name_to_id = get_item_ids()
    location_name_to_id = get_location_ids()

    def __init__(self, multiworld: "MultiWorld", player: int):
        super().__init__(multiworld, player)
        self.available_weapons: List[str] = []
        self.total_locations: int = 0
        self.total_objectives: int = 0
        self.starting_class = TFClass.UNKNOWN
        self.weapon_kill_counts: Dict[str, int] = {}
        self.class_kill_counts: Dict[str, int] = {}

    def create_item(self, name: str) -> Item:
        return create_item(self, name, get_item_id(name))

    def generate_early(self):
        for weapon in self.options.BannedWeapons:
            valid = False
            for weapon_dict in weapon_kill_names:
                for weapon_name in weapon_dict.values():
                    if weapon == weapon_name:
                        valid = True
                        break

            if not valid:
                raise Exception(f"Invalid weapon name: {weapon}")

        starting_class: TFClass
        try:
            starting_class = TFClass(self.options.StartingClass)
        except ValueError:
            class_list = ol_to_list(self.options.AllowedClasses)
            starting_class = TFClass[class_list[self.random.randint(0, len(class_list) - 1)].upper()]

        self.starting_class = starting_class
        self.multiworld.push_precollected(self.create_item(starting_class.tostr()))
        self.init_available_weapons()

    def create_regions(self):
        self.total_locations = create_tf2_objectives(self)

    def create_items(self):
        self.multiworld.itempool += create_itempool(self)

    def set_rules(self):
        self.multiworld.completion_condition[self.player] = \
            lambda state: state.has("Contract Point", self.player, self.get_required_contract_points())

    def get_filler_item_name(self) -> str:
        return "Contract Hint"

    def fill_slot_data(self) -> Mapping[str, Any]:
        slot_data = {}
        slot_data["WeaponKillCounts"] = self.weapon_kill_counts
        slot_data["ClassKillCounts"] = self.class_kill_counts
        slot_data["RequiredContractPoints"] = self.get_required_contract_points()
        slot_data["DeathLinkAmnesty"] = self.options.DeathLinkAmnesty.value
        slot_data["DeathLink"] = bool(self.options.DeathLink.value)
        return slot_data

    def write_spoiler(self, spoiler_handle: TextIO):
        spoiler_handle.write(f"Total Weapons: {len(self.available_weapons)}\n")
        spoiler_handle.write(f"Total Objectives: {self.total_objectives}\n")
        spoiler_handle.write(f"Contract Points Required: {self.get_required_contract_points()}")

    def get_required_contract_points(self) -> int:
        return floor(self.total_objectives * (self.options.ContractPointRequirement/100))

    def init_available_weapons(self):
        weapon_count = self.random.randint(
            min(self.options.MinWeaponsInPool.value, self.options.MaxWeaponsInPool.value),
            max(self.options.MaxWeaponsInPool.value, self.options.MinWeaponsInPool.value))

        class_list = ol_to_list(self.options.AllowedClasses)
        max_per_class = weapon_count
        per_class_counts = {}
        if self.options.EvenWeaponCounts:
            max_per_class = weapon_count / len(class_list)

        banned_weps = ol_to_list(self.options.BannedWeapons)
        for class_name in self.options.AllowedClasses:
            class_type = TFClass[class_name.upper()]
            if class_type == TFClass.UNKNOWN:
                raise Exception(f"Unknown class name \"{class_name}\" in AllowedClasses list")

            count = 0
            allow_all_melee = (self.options.MeleeWeaponRules == MeleeWeaponRules.option_allow_all)
            allow_knives = (self.options.MeleeWeaponRules == MeleeWeaponRules.option_allow_knives_only
                            or self.options.MeleeWeaponRules == MeleeWeaponRules.option_allow_knives_and_swords_only)
            allow_swords = (self.options.MeleeWeaponRules == MeleeWeaponRules.option_allow_swords_only
                            or self.options.MeleeWeaponRules == MeleeWeaponRules.option_allow_knives_and_swords_only)

            weapon_list = list(weapon_kill_names[class_type].values())
            self.random.shuffle(weapon_list)
            for weapon in weapon_list:
                if weapon in self.available_weapons or weapon in banned_weps:
                    continue

                if not allow_all_melee:
                    if self.options.MeleeWeaponRules == MeleeWeaponRules.option_disallow_all and weapon in melee_weapons:
                        continue

                    if weapon in knives and not allow_knives or weapon in swords and not allow_swords:
                        continue

                self.available_weapons.append(weapon)
                count += 1
                per_class_counts[class_type] = count
                if count >= max_per_class:
                    break

        # shuffle and truncate
        self.random.shuffle(self.available_weapons)
        if self.options.EvenWeaponCounts:
            index = 0
            values_list = list(per_class_counts.values())
            average = sum(values_list) / len(values_list)
            self.random.shuffle(class_list)
            while len(per_class_counts) > 0:
                current_class = TFClass[class_list[index].upper()]
                if current_class not in per_class_counts.keys():
                    index += 1
                    if index >= len(class_list):
                        index = 0
                    continue
                elif per_class_counts[current_class] <= average:
                    del per_class_counts[current_class]
                    continue

                for wep in self.available_weapons:
                    if weapon_to_class.get(wep) == current_class:
                        self.available_weapons.remove(wep)
                        per_class_counts[current_class] -= 1
                        index += 1
                        if index >= len(class_list):
                            index = 0
                        break
        elif len(self.available_weapons) > weapon_count:
            del self.available_weapons[weapon_count:]