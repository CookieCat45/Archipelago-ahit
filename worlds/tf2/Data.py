from enum import IntEnum
from typing import NamedTuple, Optional, TYPE_CHECKING
from BaseClasses import Item, ItemClassification, Location

if TYPE_CHECKING:
    from . import TF2World

class_names = [
    "Scout",
    "Soldier",
    "Pyro",
    "Demoman",
    "Heavy",
    "Engineer",
    "Medic",
    "Sniper",
    "Spy"
]

class TFClass(IntEnum):
    UNKNOWN = 0
    SCOUT = 1,
    SOLDIER = 2,
    PYRO = 3,
    DEMOMAN = 4,
    HEAVY = 5,
    ENGINEER = 6,
    MEDIC = 7,
    SNIPER = 8,
    SPY = 9

    def tostr(self):
        return self.name.lower().capitalize()

class TF2Item(Item):
    game = "Team Fortress 2"

class TF2Location(Location):
    game = "Team Fortress 2"

class ItemData(NamedTuple):
    code: Optional[int]
    classification: ItemClassification
    tf_class: Optional[TFClass] = TFClass.UNKNOWN

class TFKillInfo:
    tf_class: TFClass = TFClass.UNKNOWN
    crit: bool = False
    weapon: str = ""
    weapon_internal: str = ""
    attacker: str = ""
    victim: str = ""

def get_kill_info(kill_string: str) -> TFKillInfo:
    kill_info = TFKillInfo()
    # to get the weapon name, find the text between the last period and the whitespace before it
    crit: bool = kill_string.endswith("(crit)")
    if crit:
        # remove this whitespace
        kill_string = "(crit)".join(kill_string.rsplit(" (crit)", 1))

    start_index: int = kill_string.rfind("with ")
    end_index: int = kill_string.rfind(".")
    weapon_name = kill_string[start_index+5:end_index]

    # to find the attacker name, find the text " killed"
    start_index = 0
    end_index = kill_string.find(" killed")
    attacker_name = kill_string[start_index:end_index]

    # victim name is a little more tricky, find the text between "killed " and " with"
    start_index = kill_string.find("killed ", end_index)+7
    end_index = kill_string.rfind(" with")
    victim_name = kill_string[start_index:end_index]

    kill_info.weapon_internal = weapon_name
    for class_dict in weapon_kill_names:
        w = class_dict.get(weapon_name)
        if w != "" and w is not None:
            kill_info.weapon = w
            break

    kill_info.attacker = attacker_name
    kill_info.victim = victim_name
    kill_info.crit = crit

    print("Weapon:", kill_info.weapon,
          " | Weapon (Internal):", kill_info.weapon_internal,
          " | Attacker:", kill_info.attacker,
          " | Victim:", kill_info.victim,
          " | Crit:", kill_info.crit)

    return kill_info

weapon_kill_names = [
    {
      # dummy entry so the class index matches the list index
    },

    # Scout
    {
        "back_scatter": "Back Scatter",
        "force_a_nature": "Force-a-Nature",
        "pep_brawlerblaster": "Baby Face's Blaster",
        "shortstop": "Shortstop",
        "soda_popper": "Soda Popper",

        "pep_pistol": "Pretty Boy's Pocket Pistol",
        "the_winger": "Winger",
        "guillotine": "Flying Guillotine",

        "bat_wood": "Sandman",
        "atomizer": "Atomizer",
        "boston_basher": "Boston Basher",
        "scout_sword": "Boston Basher",
        "warfan": "Fan O'War",
        "holymackerel": "Holy Mackerel",
        "unarmed_combat": "Holy Mackerel",
        "wrap_assassin": "Wrap Assassin",
        "lava_bat": "Sun-on-a-Stick",
        "candy_cane": "Candy Cane",
    },

    # Soldier
    {
        "cow_mangler": "Cow Mangler 5000",
        "airstrike": "Air Strike",
        "blackbox": "Black Box",
        "dumpster_device": "Beggar's Bazooka",
        "rocketlauncher_directhit": "Direct Hit",
        "liberty_launcher": "Liberty Launcher",

        "reserve_shooter": "Reserve Shooter",
        "panic_attack": "Panic Attack",
        "righteous_bison": "Righteous Bison",
        "mantreads": "Mantreads",

        "unique_pickaxe_escape": "Escape Plan",
        "paintrain": "Pain Train",
        "unique_pickaxe": "Equalizer",
        "disciplinary_action": "Disciplinary Action",
        "demokatana": "Half-Zatoichi",
        "market_gardener": "Market Gardener",
    },

    # Pyro
    {
        "deflect_rocket": "Reflect",
        "deflect_promode": "Reflect",
        "deflect_ball": "Reflect",
        "deflect_arrow": "Reflect",
        "deflect_flare": "Reflect",
        "deflect_sticky": "Reflect",
        "rescue_ranger_reflect": "Reflect",
        "deflect_huntsman_headshot": "Reflect",
        "deflect_huntsman_flyingburn": "Reflect",
        "deflect_huntsman_flyingburn_headshot": "Reflect",

        "phlogistinator": "Phlogistinator",
        "dragons_fury": "Dragon's Fury",
        "backburner": "Backburner",
        "degreaser": "Degreaser",

        "reserve_shooter": "Reserve Shooter",
        "panic_attack": "Panic Attack",
        "flaregun": "Flare Gun",
        "scorch_shot": "Scorch Shot",
        "detonator": "Detonator",
        "manmelter": "Manmelter",
        "rocketpack_stomp": "Thermal Thruster",

        "axtinguisher": "Axtinguisher",
        "mailbox": "Axtinguisher",
        "sledgehammer": "Homewrecker",
        "the_maul": "Homewrecker",
        "powerjack": "Powerjack",
        "thirddegree": "Third Degree",
        "back_scratcher": "Back Scratcher",
        "lava_axe": "Sharpened Volcano Fragment",
        "annihilator": "Neon Annihilator",
        "hot_hand": "Hot Hand",
    },

    # Demoman
    {
        "iron_bomber": "Iron Bomber",
        "loose_cannon": "Loose Cannon",
        "loch_n_load": "Loch-n-Load",

        "sticky_resistance": "Scottish Resistance",
        "quickiebomb_launcher": "Quickiebomb Launcher",
        "demoshield": "Chargin' Targe",
        "splendid_screen": "Splendid Screen",
        "tide_turner": "Tide Turner",

        "ullapool_caber": "Ullapool Caber",
        "ullapool_caber_explosion": "Ullapool Caber",
        "battleaxe": "Scotsman's Skullcutter",
        "paintrain": "Pain Train",
        "claidheamohmor": "Claidheamh Mor",
        "demokatana": "Half-Zatoichi",
        "sword": "Eyelander",
        "headtaker": "Eyelander",
        "nessieclub": "Eyelander",
        "persian_persuader": "Persian Persuader",
    },

    # Heavy
    {
        "natascha": "Natascha",
        "tomislav": "Tomislav",
        "brass_beast": "Brass Beast",
        "long_heatmaker": "Huo-Long Heater",

        "panic_attack": "Panic Attack",
        "family_business": "Family Business",

        "holiday_punch": "Holiday Punch",
        "warrior_spirit": "Warrior's Spirit",
        "steel_fists": "Fists of Steel",
        "gloves": "Killing Gloves of Boxing",
        "gloves_running_urgently": "Gloves of Running Urgently",
        "eviction_notice": "Eviction Notice",
    },

    # Engineer
    {
        "rescue_ranger": "Rescue Ranger",
        "widowmaker": "Widowmaker",
        "pomson": "Pomson 6000",
        "frontier_justice": "Frontier Justice",
        "panic_attack": "Panic Attack",

        "short_circuit": "Short Circuit",
        "tf_projectile_mechanicalarmorb": "Short Circuit",

        "eureka_effect": "Eureka Effect",
        "wrench_jag": "Jag",
        "robot_arm_kill": "Gunslinger",
        "robot_arm_combo_kill": "Gunslinger",
        "robot_arm_blender_kill": "Gunslinger",
        "southern_hospitality": "Southern Hospitality",
    },

    # Medic
    {
        "blutsauger": "Blutsauger",
        "proto_syringe": "Overdose",
        "crusaders_crossbow": "Crusader's Crossbow",

        "ubersaw": "Ubersaw",
        "solemn_vow": "Solemn Vow",
        "amputator": "Amputator",
        "battleneedle": "Vita-Saw",

    },

    # Sniper
    {
        "pro_rifle": "Hitman's Heatmaker",
        "machina": "Machina",
        "player_penetration": "Machina",
        "sydney_sleeper": "Sydney Sleeper",
        "tf_projectile_arrow": "Huntsman",
        "bazaar_bargain": "Bazaar Bargain",
        "the_classic": "Classic",

        "pro_smg": "Cleaner's Carbine",

        "bushwacka": "Bushwacka",

        "tribalkukri": "Tribalman's Shiv",
        "shahanshah": "Shahanshah",
    },

    # Spy
    {
        "diamondback": "Diamondback",
        "ambassador": "Ambassador",
        "enforcer": "Enforcer",
        "letranger": "L'Etranger",

        "kunai": "Conniver's Kunai",
        "big_earner": "Big Earner",
        "spy_cicle": "Spy-cicle",
        "eternal_reward": "Your Eternal Reward",
    },
]

multiclass_weapons = [
    "Half-Zatoichi",
    "Reserve Shooter",
    "Panic Attack",
]

knives = [
    "Conniver's Kunai",
    "Big Earner",
    "Spy-cicle",
    "Your Eternal Reward",
]

swords = [
    "Half-Zatoichi",
    "Eyelander",
    "Scotsman's Skullcutter",
    "Claidheamh Mor",
    "Persian Persuader",
]

melee_weapons = [
    *knives,
    *swords,

    "Sandman",
    "Atomizer",
    "Boston Basher",
    "Fan O'War",
    "Holy Mackerel",
    "Wrap Assassin",
    "Sun-on-a-Stick",

    "Escape Plan",
    "Pain Train",
    "Equalizer",
    "Disciplinary Action",
    "Market Gardener",

    "Axtinguisher",
    "Homewrecker",
    "Powerjack",
    "Third Degree",
    "Back Scratcher",
    "Sharpened Volcano Fragment",
    "Neon Annihilator",
    "Hot Hand",
]

trap_ids = {
    "Taunt Trap": 10,
    "Melee-Only Trap": 11,
    "Disconnect Trap": 12
}

weapon_list = []
def _init_weapon_list():
    for weapon_dict in weapon_kill_names:
        for val in weapon_dict.values():
            if val in weapon_list:
                continue

            weapon_list.append(val)

_init_weapon_list()

weapon_to_class = {}
multi_class_weapon_lists = {}
def _init_weapon_to_class():
    i = 0
    for weapon_dict in weapon_kill_names:
        class_type = TFClass(i)
        class_name = class_type.tostr()
        if class_name not in multi_class_weapon_lists.keys():
            multi_class_weapon_lists[class_name] = []
        if class_type == TFClass.UNKNOWN:
            i += 1
            continue

        for weapon in weapon_dict.values():
            if weapon in multiclass_weapons:
                multi_class_weapon_lists[class_name].append(weapon)
            else:
                weapon_to_class.setdefault(weapon, class_name)

        i += 1

_init_weapon_to_class()

def class_uses_weapon(class_name: str, weapon: str) -> bool:
    return weapon_to_class.get(weapon) == class_name or weapon in multi_class_weapon_lists[class_name]
