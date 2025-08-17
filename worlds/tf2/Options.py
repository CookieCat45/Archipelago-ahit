from worlds.AutoWorld import PerGameCommonOptions
from dataclasses import dataclass
from typing import List
from Options import Range, Toggle, DeathLink, Choice, OptionDict, DefaultOnToggle, OptionGroup, OptionList

def ol_to_list(option_list: OptionList) -> List:
    real_list = []
    for val in option_list:
        real_list.append(val)

    return real_list

class AllowedClasses(OptionList):
    """The classes that will have their relevant items and locations added to the multiworld.
    If you don't want to be forced to play a certain class, you can remove them from this list."""
    default = (
        "Scout",
        "Soldier",
        "Pyro",
        "Demoman",
        "Heavy",
        "Engineer",
        "Medic",
        "Sniper",
        "Spy",
    )

class StartingClass(Choice):
    """The class unlock that you will start with. Any class can be played at any time, but you must have a class unlocked
    via their respective item before you can send out any location checks that involve them."""
    option_scout = 1
    option_soldier = 2
    option_pyro = 3
    option_demoman = 4
    option_heavy = 5
    option_engineer = 6
    option_medic = 7
    option_sniper = 8
    option_spy = 9
    option_random_class = 10
    default = 10

class BannedWeapons(OptionList):
    """List of weapons that will never be added to the item pool or have kill checks requiring them."""
    default = (
        "Flying Guillotine",
        "Wrap Assassin",
        "Fan O'War",
        "Atomizer",
        "Sun-on-a-Stick",
        "Candy Cane",
        "Boston Basher",

        "Mantreads",
        "Righteous Bison",
        "Market Gardener",
        "Escape Plan",
        "Pain Train",

        "Thermal Thruster",
        "Detonator",
        "Homewrecker",
        "Sharpened Volcano Fragment",

        "Chargin' Targe",
        "Splendid Screen",
        "Tide Turner",

        "Gloves of Running Urgently",
        "Eviction Notice",

        "Pomson 6000",
        "Rescue Ranger",
        "Short Circuit",
        "Jag",

        "Overdose",
        "Amputator",

        "Classic",
        "Cleaner's Carbine",
        "Tribalman's Shiv",
        "Shahanshah",

        "L'Etranger",
    )

class ContractPointRequirement(Range):
    """How many objectives, as a percentage of the total, need to be completed to finish your goal"""
    range_start = 10
    range_end = 90
    default = 75

class MinWeaponsInPool(Range):
    """The minimum number of weapon items that get shuffled into the pool."""
    range_start = 10
    range_end = 100
    default = 20

class MaxWeaponsInPool(Range):
    """The maximum number of weapon items that get shuffled into the pool."""
    range_start = 10
    range_end = 100
    default = 25

class EvenWeaponCounts(DefaultOnToggle):
    """Split the amount of weapon unlocks per class in the item pool as evenly as possible."""

class MeleeWeaponRules(Choice):
    """The rules that dictate how melee weapon unlocks should be added to the item pool."""
    option_allow_all = 0
    option_disallow_all = 1
    option_allow_knives_only = 2
    option_allow_swords_only = 3
    option_allow_knives_and_swords_only = 4
    default = 0

class TrapChance(Range):
    """The chance for a junk item in the pool to be replaced by a trap."""
    range_start = 0
    range_end = 100
    default = 0

class ParanoiaTrapWeight(Range):
    """The weight of Paranoia Traps in the trap pool.
    Paranoia Traps will play the Spy's decloaking sound."""
    range_start = 0
    range_end = 100
    default = 40

class KillbindTrapWeight(Range):
    """The weight of Killbind Traps in the trap pool.
    Killbind Traps cause you to die (or explode) immediately."""
    range_start = 0
    range_end = 100
    default = 0

class DisconnectTrapWeight(Range):
    """The weight of Disconnect Traps in the trap pool.
    Disconnect Traps immediately disconnect you from the game server (NOT the Archipelago server)."""
    range_start = 0
    range_end = 100
    default = 0

class SndRestartTrapWeight(Range):
    """The weight of snd_restart traps in the trap pool.
    snd_restart traps force the game to run the snd_restart command, which causes a lag spike."""
    range_start = 0
    range_end = 100
    default = 0

# TODO: Implement
class TauntTrapWeight(Range):
    """The weight of Taunt Traps in the trap pool.
    Taunt traps force you to taunt constantly for 15 seconds."""
    range_start = 0
    range_end = 100
    default = 40

# TODO: Implement
class MeleeOnlyTrapWeight(Range):
    """The weight of Melee-Only Traps in the trap pool.
    Melee-Only Traps force you to use your melee weapon for 30 seconds."""
    range_start = 0
    range_end = 100
    default = 40

class GeneralKillObjectiveCountMin(Range):
    """The minimum number of general kills performed as each class that will be location checks.
    For example, 10 kills as Scout would be 10 checks at one per kill."""
    range_start = 3
    range_end = 15
    default = 3

class GeneralKillObjectiveCountMax(Range):
    """The maximum number of general kills performed as each class that will be location checks.
    For example, 10 kills as Scout would be 10 checks at one per kill."""
    range_start = 3
    range_end = 15
    default = 4

class WeaponKillObjectiveCountMin(Range):
    """The minimum number of kills performed with each unique weapon in the multiworld that will be location checks.
    For example, 3 kills with the Direct Hit would be 3 checks at one per kill.
    Weapons and their respective classes need to be unlocked before being able to send out checks with them,
    but you are still allowed to use any weapon at any time."""
    range_start = 2
    range_end = 10
    default = 2

class WeaponKillObjectiveCountMax(Range):
    """The maximum number of kills performed with each unique weapon in the multiworld that will be location checks.
    For example, 3 kills with the Direct Hit would be 3 checks at one per kill.
    Weapons and their respective classes need to be unlocked before being able to send out checks with them,
    but you are still allowed to use any weapon at any time."""
    range_start = 2
    range_end = 10
    default = 3

class DeathLinkAmnesty(Range):
    """How many deaths that are required to send out a DeathLink."""
    range_start = 1
    range_end = 5
    default = 3

@dataclass
class TF2Options(PerGameCommonOptions):
    AllowedClasses: AllowedClasses
    StartingClass: StartingClass
    BannedWeapons: BannedWeapons
    ContractPointRequirement: ContractPointRequirement
    MinWeaponsInPool: MinWeaponsInPool
    MaxWeaponsInPool: MaxWeaponsInPool
    GeneralKillObjectiveCountMin: GeneralKillObjectiveCountMin
    GeneralKillObjectiveCountMax: GeneralKillObjectiveCountMax
    WeaponKillObjectiveCountMin: WeaponKillObjectiveCountMin
    WeaponKillObjectiveCountMax: WeaponKillObjectiveCountMax
    EvenWeaponCounts: EvenWeaponCounts
    MeleeWeaponRules: MeleeWeaponRules
    TrapChance: TrapChance
    #TauntTrapWeight: TauntTrapWeight
    #MeleeOnlyTrapWeight: MeleeOnlyTrapWeight
    SndRestartTrapWeight: SndRestartTrapWeight
    ParanoiaTrapWeight: ParanoiaTrapWeight
    KillbindTrapWeight: KillbindTrapWeight
    DisconnectTrapWeight: DisconnectTrapWeight
    DeathLink: DeathLink
    DeathLinkAmnesty: DeathLinkAmnesty
