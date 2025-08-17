from typing import TYPE_CHECKING, List, Dict
from BaseClasses import ItemClassification, Item
from .Data import TFClass, TF2Item, weapon_to_class, weapon_kill_names, multiclass_weapons, weapon_list, class_names

if TYPE_CHECKING:
    from . import TF2World


def create_itempool(world: "TF2World") -> List[Item]:
    item_list: List[Item] = []
    weapon_itempool = []
    for class_name in world.options.AllowedClasses:
        # create the "class" item
        class_type: TFClass = TFClass[class_name.upper()]
        if class_type != world.starting_class:
            item_list.append(world.create_item(class_name))

        # Figure out what weapons we're allowed to add to the pool for this class
        for weapon_name in weapon_kill_names[int(class_type)].values():
            if weapon_name in world.available_weapons and weapon_name not in weapon_itempool:
                weapon_itempool.append(weapon_name)

    for weapon_name in weapon_itempool:
        item_list.append(world.create_item(weapon_name))
        if len(item_list) >= world.total_locations:
            # too many weapons vs available locations, stop adding them
            break

    # Filler
    while len(item_list) < world.total_locations:
        if world.options.TrapChance.value > 0 and world.random.randint(1, 100) <= world.options.TrapChance.value:
            trap_list: Dict[str, int] = {}
            trap_list["Killbind Trap"] = world.options.KillbindTrapWeight.value
            trap_list["Disconnect Trap"] = world.options.DisconnectTrapWeight.value
            trap_list["Paranoia Trap"] = world.options.ParanoiaTrapWeight.value
            trap_list["snd_restart Trap"] = world.options.SndRestartTrapWeight.value
            item_list.append(world.create_item(
                world.random.choices(list(trap_list.keys()), weights=list(trap_list.values()), k=1)[0]))
        else:
            item_list.append(world.create_item("Contract Hint"))

    return item_list

def create_item(world: "TF2World", name: str, code: int) -> Item:
    item_class: ItemClassification
    if name == "Contract Hint":
        item_class = ItemClassification.filler
    elif "Trap" in name:
        item_class = ItemClassification.trap
    else:
        item_class = ItemClassification.progression

    return TF2Item(name, item_class, code, world.player)

def get_item_id(name: str) -> int:
    if name == "Contract Hint":
        return 50
    elif name == "Killbind Trap":
        return 51
    elif name == "Disconnect Trap":
        return 52
    elif name == "Paranoia Trap":
        return 53
    elif name == "snd_restart Trap":
        return 54
    elif name == "Taunt Trap":
        return 55
    elif name == "Melee Only Trap":
        return 56

    if name in multiclass_weapons:
        weapon_id = 2000
        # just use ascii values for multiclass weapons
        ascii_values = list(name.encode('ascii'))
        for val in ascii_values:
            weapon_id += val

        return weapon_id

    try:
        class_type: TFClass = TFClass[name.upper()]
        if class_type != TFClass.UNKNOWN:
            return int(class_type)
    except KeyError:
        pass

    class_type = TFClass.UNKNOWN
    try:
        class_type = TFClass[weapon_to_class.get(name).upper()]
    except AttributeError:
        pass

    weapon_id: int
    if class_type != TFClass.UNKNOWN:
        weapon_id = int(class_type) * 100
    else:
        raise Exception(f"Can't generate item ID for '{name}'")

    count: int = 0
    for weapon_name in weapon_kill_names[int(class_type)].values():
        if weapon_name == name:
            weapon_id += count
            break

        count += 1

    return weapon_id

def get_item_ids() -> Dict[str, int]:
    item_ids = {}
    for weapon in weapon_list:
        item_ids.setdefault(weapon, get_item_id(weapon))

    for name in class_names:
        item_ids.setdefault(name, get_item_id(name))

    item_ids.setdefault("Contract Hint", get_item_id("Contract Hint"))
    item_ids.setdefault("Reflect", get_item_id("Reflect"))
    item_ids.setdefault("Killbind Trap", get_item_id("Killbind Trap"))
    item_ids.setdefault("Disconnect Trap", get_item_id("Disconnect Trap"))
    item_ids.setdefault("Paranoia Trap", get_item_id("Paranoia Trap"))
    item_ids.setdefault("snd_restart Trap", get_item_id("snd_restart Trap"))
    item_ids.setdefault("Taunt Trap", get_item_id("Taunt Trap"))
    item_ids.setdefault("Melee Only Trap", get_item_id("Melee Only Trap"))
    return item_ids
