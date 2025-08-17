import asyncio
import Utils
import os
from typing import Dict, Any
from rcon.source import Client
from rcon import WrongPassword
import socket
from random import randint
from copy import deepcopy
from NetUtils import JSONtoTextParser, JSONMessagePart, ClientStatus
from .Data import class_uses_weapon, TFClass, TFKillInfo, get_kill_info
from .Items import get_item_id
from .Regions import get_location_id
from CommonClient import CommonContext, gui_enabled, ClientCommandProcessor, logger, get_base_parser
from kvui import GameManager
from kivy.uix.layout import Layout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button

DEBUG = False

class TF2JSONToTextParser(JSONtoTextParser):
    def _handle_color(self, node: JSONMessagePart):
        return self._handle_text(node)  # No colors for the in-game text

class TF2Cmd:
    def __init__(self, cmd, args=""):
        self.cmd = cmd
        self.args = args

class TF2CommandProcessor(ClientCommandProcessor):
    def _cmd_tf2_connect(self, password: str):
        """Connect to TF2 RCON"""
        if isinstance(self.ctx, TF2Context):
            if self.ctx.game_folder_path == "":
                self.ctx.find_tf2_folder()

            if self.ctx.rcon is not None and self.ctx.rcon_password != "":
                logger.info("You're already connected!")
                return

            self.ctx.rcon_password = password

    def _cmd_tf2_contracthints(self):
        """Show any obtained contract hints"""
        if isinstance(self.ctx, TF2Context):
            if len(self.ctx.contract_hints) <= 0:
                logger.info("You have no contract hints.")
                return

            showed_hint = False
            for hint in self.ctx.contract_hints:
                if not self.ctx.has_item(hint):
                    logger.info(hint)
                    showed_hint = True

            if not showed_hint:
                logger.info("You don't have any contract hints (for unobtained contracts).")

    def _cmd_deathlink(self):
        """Toggle DeathLink"""
        if isinstance(self.ctx, TF2Context):
            Utils.async_start(self.ctx.update_death_link(False if "DeathLink" in self.ctx.tags else True))

    if DEBUG:
        def _cmd_tf2_sendcmd(self, text: str):
            if isinstance(self.ctx, TF2Context):
                if self.ctx.rcon is not None:
                    self.ctx.rcon.run(text)


class TF2Context(CommonContext):
    game = "Team Fortress 2"
    command_processor = TF2CommandProcessor

    def __init__(self, server_address, password):
        super().__init__(server_address, password)
        self.gamejsontotext = TF2JSONToTextParser(self)
        self.autoreconnect_task = None
        self.endpoint = None
        self.rcon = None
        self.rcon_task = None
        self.steam_name = ""
        self.items_handling = 0b111
        self.cmd_queue = []
        self.slot_data = None
        self.death_count = 0
        self.death_req = 3
        self.weapon_kill_reqs = {}
        self.class_kill_reqs = {}
        self.weapon_kill_counts = {}
        self.class_kill_counts = {}
        self.contract_hints = []
        self.points = 0
        self.required_points = 0
        self.game_folder_path = ""
        self.condump_io = None
        self.rcon_password = ""
        self.current_class = TFClass.UNKNOWN

    async def server_auth(self, password_requested: bool = False):
        if password_requested and not self.password:
            await super(TF2Context, self).server_auth(password_requested)

        await self.get_username()
        await self.send_connect()

    async def disconnect(self, allow_autoreconnect: bool = False):
        await super().disconnect(allow_autoreconnect)

    def on_deathlink(self, data: Dict[str, Any]) -> None:
        self.killbind()
        super().on_deathlink(data)

    def find_tf2_folder(self):
        saved_path = Utils.local_path('data', 'tf2_dir.txt')
        if os.path.isfile(saved_path):
            with open(saved_path) as file:
                self.game_folder_path = file.read()
                print(f"Found saved path: {self.game_folder_path}")

        if self.game_folder_path == "" or not os.path.isdir(self.game_folder_path):
            # try some common paths
            common_paths = [
                "C:/Program Files (x86)/Steam/steamapps/common/Team Fortress 2",
                "D:/Program Files (x86)/Steam/steamapps/common/Team Fortress 2",
                "/home/user/.steam/steam/steamapps/common/Team Fortress 2",
                "/home/deck/.steam/steam/steamapps/common/Team Fortress 2",
            ]

            for p in common_paths:
                if os.path.isdir(p):
                    self.game_folder_path = p
                    break

            while not self.game_folder_path.endswith("common/Team Fortress 2") or not os.path.isdir(self.game_folder_path):
                self.game_folder_path = Utils.open_directory("Where is your Team Fortress 2 game directory?")

            if not os.path.isfile(saved_path):
                with open(saved_path, mode='x') as file:
                    file.write(self.game_folder_path)
                    print(f"Saving path: {self.game_folder_path}")

    def is_connected(self) -> bool:
        return self.server and self.server.socket.open

    def get_condump_file(self) -> str:
        return self.game_folder_path + "/tf/ap_dump.txt"

    def has_item(self, item_name: str) -> bool:
        item_id = get_item_id(item_name)
        for i in self.items_received:
            if i.item == item_id:
                return True

        return False

    def on_console_line(self, line: str):
        # if DEBUG:
            # logger.info(f"Console output: {line}")

        if line.find("ap_say") == 0:
            message: str = line.replace("ap_say ", "", 1)
            message = message.strip("\n")
            Utils.async_start(self.send_msgs([{"cmd": "Say", "text": message}]))
        elif line.find("ap_classmissing") == 0:
            if self.current_class == TFClass.UNKNOWN:
                self.echo("Your class is unknown by the client, type 'record 1' and then 'stop' in the console to fix this, or change classes.")
                return

            message = ""
            class_name = self.current_class.tostr()
            class_count = self.class_kill_counts.get(class_name, 0)
            class_req = self.class_kill_reqs.get(class_name, 0)
            if class_count < class_req:
                message += f"{class_name} Kills: {class_count}/{class_req}\necho "

            for weapon in self.weapon_kill_reqs.keys():
                if not self.has_item(weapon) or not class_uses_weapon(class_name, weapon):
                    continue

                count = self.weapon_kill_counts.get(weapon, 0)
                req = self.weapon_kill_reqs.get(weapon, 0)
                if count >= req:
                    continue

                message += f"{weapon}: {count}/{req}\necho "

            if message == "":
                self.echo(f"You have no pending objectives for the {class_name} class.")
            else:
                self.echo(message)

        elif line.find("not executing.") != -1 or line.find("execing") != -1:
            # Class change
            if line.find("scout.cfg") != -1:
                self.current_class = TFClass.SCOUT
            elif line.find("soldier.cfg") != -1:
                self.current_class = TFClass.SOLDIER
            elif line.find("pyro.cfg") != -1:
                self.current_class = TFClass.PYRO
            elif line.find("demoman.cfg") != -1:
                self.current_class = TFClass.DEMOMAN
            elif line.find("heavyweapons.cfg") != -1 or line.find("heavy.cfg") != -1:
                self.current_class = TFClass.HEAVY
            elif line.find("engineer.cfg") != -1:
                self.current_class = TFClass.ENGINEER
            elif line.find("medic.cfg") != -1:
                self.current_class = TFClass.MEDIC
            elif line.find("sniper.cfg") != -1:
                self.current_class = TFClass.SNIPER
            elif line.find("spy.cfg") != -1:
                self.current_class = TFClass.SPY
        elif line.find(self.steam_name) == 0:
            if not self.is_connected():
                return

            if line.find("killed") != -1 and line.find("with") != -1:
                info: TFKillInfo = get_kill_info(line)
                sound_played_novice = False
                sound_played_expert = False
                if self.current_class != TFClass.UNKNOWN:
                    class_name = self.current_class.tostr()
                    if class_name in self.class_kill_reqs.keys() and self.has_item(class_name):
                        # Class general kill
                        val = self.class_kill_counts.get(class_name, 0)
                        req = self.class_kill_reqs.get(class_name, 0)
                        if val < req:
                            location_id = get_location_id(class_name) + val
                            Utils.async_start(self.send_msgs([{"cmd": "LocationChecks", "locations": [location_id]}]))
                            val += 1
                            self.class_kill_counts[class_name] = val
                            key = format(f"ClassCount_{self.slot}_{class_name}")
                            Utils.async_start(self.send_msgs([{"cmd": "Set", "key": key,
                                                               "operations": [
                                                                   {"operation": "replace", "value": val}]}]))

                            if val >= req:
                                self.echo(f"[ARCHIPELAGO] COMPLETED CONTRACT: Kills as {class_name} ({val}/{req})")
                                self.play_sound("ui/quest_status_tick_expert.wav")
                                self.add_contract_points(1)
                                sound_played_expert = True
                            else:
                                self.play_sound("ui/quest_status_tick_novice.wav")
                                sound_played_novice = True

                            self.update_ui()
                else:
                    for i in range(6):
                        self.echo(
                            "!!!!! Your class is unknown by the client. Switch classes or type  'record 1' and then 'stop'  "
                            "in the console to fix this. !!!!!")

                if info.weapon_internal == "loose_cannon_impact":
                    # Loose Cannon has two different kill names
                    info.weapon = "Loose Cannon"
                    info.weapon_internal = "loose_cannon"
                elif info.weapon_internal == "bleed_kill":
                    if self.current_class == TFClass.ENGINEER:
                        info.weapon = "Southern Hospitality"
                        info.weapon_internal = "southern_hospitality"
                    elif self.current_class == TFClass.SNIPER:
                        info.weapon = "Tribalman's Shiv"
                        info.weapon_internal = "tribalkukri"
                    elif self.current_class == TFClass.SCOUT:
                        # Scout has two different weapons that cause bleeding, so just pick one
                        guillotine_kills = self.weapon_kill_counts.get("Flying Guillotine", 0)
                        guillotine_req = self.weapon_kill_reqs.get("Flying Guillotine", 0)
                        basher_kills = self.weapon_kill_counts.get("Boston Basher", 0)
                        basher_req = self.weapon_kill_reqs.get("Boston Basher", 0)
                        if self.has_item("Flying Guillotine") and guillotine_kills < guillotine_req:
                            info.weapon = "Flying Guillotine"
                            info.weapon_internal = "guillotine"
                        elif self.has_item("Boston Basher") and basher_kills < basher_req:
                            info.weapon = "Boston Basher"
                            info.weapon_internal = "boston_basher"

                weapon = info.weapon
                if weapon in self.weapon_kill_reqs.keys() and self.has_item(weapon):
                    # Weapon kill
                    val = self.weapon_kill_counts.get(weapon, 0)
                    req = self.weapon_kill_reqs.get(weapon, 0)
                    if val < req:
                        location_id = get_location_id(weapon) + val
                        Utils.async_start(self.send_msgs([{"cmd": "LocationChecks", "locations": [location_id]}]))
                        val += 1
                        self.weapon_kill_counts[weapon] = val
                        key = format(f"WeaponCount_{self.slot}_{weapon}")
                        Utils.async_start(self.send_msgs([{"cmd": "Set","key": key,
                                                           "operations":[{"operation": "replace", "value": val}]}]))

                        if val >= req:
                            self.echo(f"[ARCHIPELAGO] COMPLETED CONTRACT: Kills with {weapon} ({val}/{req})")
                            self.add_contract_points(1)
                            if not sound_played_expert:
                                self.play_sound("ui/quest_status_tick_expert.wav")
                        else:
                            if not sound_played_novice:
                                self.play_sound("ui/quest_status_tick_novice.wav")

                        self.update_ui()
        elif line.find(self.steam_name) != -1:
            if line.find("killed") != -1 and line.find("with") != -1:
                if "DeathLink" in self.tags:
                    info: TFKillInfo = get_kill_info(line)
                    if info.victim == self.steam_name:
                        self.death_count += 1
                        if self.death_count >= self.death_req:
                            self.death_count = 0
                            if info.weapon != "":
                                line = line.replace(info.weapon_internal, info.weapon)
                            Utils.async_start(self.send_death(line))

    def play_sound(self, sound: str):
        self.cmd_queue.append(TF2Cmd(cmd='play', args=sound))

    def update_ui(self):
        if self.current_class != TFClass.UNKNOWN:
            self.ui.show_weapon_grid(self.current_class.tostr())
        else:
            self.ui.update_tf2_tab()

    def add_contract_points(self, amount: int):
        if self.points >= self.required_points:
            return

        self.points += amount
        self.echo(f"[ARCHIPELAGO] Contract Points: {self.points}/{self.required_points}")
        Utils.async_start(self.send_msgs([{"cmd": "Set", "key": f"ContractPoints_{self.slot}",
                                           "operations": [{"operation": "replace", "value": self.points}]}]))

        if self.points >= self.required_points:
            Utils.async_start(self.send_msgs([{"cmd": "StatusUpdate", "status": ClientStatus.CLIENT_GOAL}]))
            self.echo("[ARCHIPELAGO] ********* CONGRATULATIONS! You're finished! ********")
            self.play_sound("misc/happy_birthday_tf_14.wav")
            self.play_sound("misc/happy_birthday.wav")

    def cleanup(self):
        self.rcon_password = ""
        self.rcon = None
        self.current_class = TFClass.UNKNOWN

    def class_has_pending_objectives(self, class_name: str) -> bool:
        class_kills = self.class_kill_counts.get(class_name, 0)
        class_count = self.class_kill_reqs.get(class_name)
        if class_kills < class_count:
            return True

        for weapon, count in self.weapon_kill_reqs.items():
            if class_uses_weapon(class_name, weapon) and self.has_item(weapon):
                weapon_kills = self.weapon_kill_counts.get(weapon, 0)
                if weapon_kills < count:
                    return True

        return False

    def on_print_json(self, args: dict):
        text = self.gamejsontotext(deepcopy(args["data"]))
        self.echo(text, 10)

        if self.ui:
            self.ui.print_json(args["data"])
        else:
            text = self.jsontotextparser(args["data"])
            logger.info(text)

    def echo(self, text: str, delay=1):
        self.cmd_queue.append(TF2Cmd(f"wait {delay}; con_filter_enable", "0"))
        self.cmd_queue.append(TF2Cmd(f"wait {delay}; echo", text))
        self.cmd_queue.append(TF2Cmd(f"wait {delay+1}; con_filter_enable", "1"))

    def on_package(self, cmd: str, args: dict):
        if cmd == "Connected":
            self.slot_data = args["slot_data"]
            self.weapon_kill_reqs = self.slot_data["WeaponKillCounts"]
            self.class_kill_reqs = self.slot_data["ClassKillCounts"]
            self.required_points = self.slot_data["RequiredContractPoints"]
            self.death_req = self.slot_data["DeathLinkAmnesty"]
            if self.slot_data["DeathLink"] is True and "DeathLink" not in self.tags:
                Utils.async_start(self.update_death_link(True))

            get_list = []
            for key in self.class_kill_reqs.keys():
                get_list.append(f"ClassCount_{self.slot}_{key}")

            for key in self.weapon_kill_reqs.keys():
                get_list.append(f"WeaponCount_{self.slot}_{key}")

            get_list.append(f"ContractPoints_{self.slot}")
            get_list.append(f"ContractHints_{self.slot}")
            if DEBUG:
                logger.info(f"Get: {get_list}")
            Utils.async_start(self.send_msgs([{"cmd": "Get","keys": get_list}]))
            self.update_ui()
            logger.info("\n********************************************************************"
                        "\nTo connect to TF2 RCON: "
                        "\n\n1. In the in-game console, enter the command: exec archipelago/start"
                        "\n2. In-game, make sure that the rcon_password convar in the console is set to something"
                        "\n3. Enter /tf2_connect <password> in this client. The password should be whatever rcon_password is."
                        "\n\nIf connecting to the RCON fails, you may not be running the game with the -usercon launch option."
                        "\n********************************************************************\n")
        elif cmd == "Retrieved":
            for key, val in args["keys"].items():
                if DEBUG:
                    logger.info(f"Retrieved: {key} = {val}")

                if key.startswith("WeaponCount_"):
                    if val is None:
                        continue

                    key = key.replace(f"WeaponCount_{self.slot}_", "")
                    self.weapon_kill_counts[key] = val
                elif key.startswith("ClassCount_"):
                    if val is None:
                        continue

                    key = key.replace(f"ClassCount_{self.slot}_", "")
                    self.class_kill_counts[key] = val
                elif key.startswith("ContractPoints") and val is not None:
                    self.points = val
                elif key.startswith("ContractHints") and val is not None:
                    self.contract_hints = val

            self.update_ui()
        elif cmd == "ReceivedItems":
            start_index = args["index"]
            if start_index == 0:
                return

            if start_index <= len(self.items_received):
                for i in args['items']:
                    if i.item == 50: # Contract Hint
                        self.give_contract_hint()
                    elif i.item == 51: # Killbind Trap
                        self.killbind()
                    elif i.item == 52: # Disconnect Trap
                        self.cmd_queue.append(TF2Cmd(cmd='disconnect'))
                    elif i.item == 53: # Paranoia Trap
                        self.play_sound("player/spy_uncloak.wav")
                    elif i.item == 54: # snd_restart Trap
                        self.cmd_queue.append(TF2Cmd(cmd='snd_restart'))

            self.update_ui()

    def give_contract_hint(self):
        possible_hints = []
        for weapon in self.weapon_kill_reqs.keys():
            if weapon in self.contract_hints or self.has_item(weapon):
                continue

            possible_hints.append(weapon)

        if len(possible_hints) <= 0:
            return

        hint = possible_hints[randint(0, len(possible_hints)-1)]
        self.contract_hints.append(hint)
        Utils.async_start(self.send_msgs([{"cmd": "Set", "key": f"ContractHints_{self.slot}", "default": [],
                                           "operations": [{"operation": "add", "value": [hint]}]}]))

        logger.info(f"Contract revealed: {hint}")
        self.echo(f"Contract revealed: {hint}")

    def killbind(self):
        cmd: str
        if randint(1, 2) == 1:
            cmd = "kill"
        else:
            cmd = "explode"
        self.cmd_queue.append(TF2Cmd(cmd=cmd))

    def run_gui(self):
        self.ui = TF2Manager(self)
        self.ui_task = asyncio.create_task(self.ui.async_run(), name="UI")


async def rcon_loop(ctx: TF2Context):
    while not ctx.exit_event.is_set():
        if ctx.rcon_password != "":
            try:
                with Client(socket.gethostbyname(socket.gethostname()), 27015, passwd=ctx.rcon_password) as ctx.rcon:
                    logger.info("Connected to TF2 RCON!")
                    # clean up the old file if it exists
                    condump = ctx.get_condump_file()
                    if os.path.isfile(condump):
                        with open(condump, 'r+') as file:
                            file.truncate(0)

                    while True:
                        if ctx.steam_name == "":
                            name = ctx.rcon.run("name")
                            name = name.replace("\"name\" = ", "")
                            index = name.find(" ( def. \"unnamed\" )")
                            name = name[1:index-1]
                            ctx.steam_name = name
                            logger.info(f"Your name is: {ctx.steam_name}")

                        if ctx.current_class == TFClass.UNKNOWN:
                            # this forces class configs to execute, so we can see what class the player is playing
                            # after a reconnect
                            ctx.rcon.run("record ap_dummy; stop")

                        if len(ctx.cmd_queue) > 0:
                            for c in ctx.cmd_queue:
                                ctx.rcon.run(c.cmd, c.args)
                            ctx.cmd_queue.clear()

                        condump = ctx.get_condump_file()
                        if ctx.condump_io is not None or os.path.isfile(condump):
                            if ctx.condump_io is None:
                                ctx.condump_io = open(condump)

                            for line in ctx.condump_io:
                                ctx.on_console_line(line)

                        await asyncio.sleep(0.1)
            except WrongPassword:
                logger.info("TF2 RCON Connection failed (Wrong RCON Password - "
                            "Check the password in-game using the rcon_password console command, "
                            "and set it to something if it's blank)")
                ctx.cleanup()
            except ConnectionRefusedError:
                logger.info("TF2 RCON connection was refused."
                            "Make sure that the game is running with the -usercon launch option.")
                ctx.cleanup()
            except Exception as e:
                logger.info(f"TF2 RCON Connection failed or aborted ({e})")
                ctx.cleanup()

        await asyncio.sleep(0.1)


class TF2Manager(GameManager):
    ctx: TF2Context
    def __init__(self, ctx):
        super().__init__(ctx)
        self.tf2_tab = None

    logging_pairs = [
        ("Client", "Archipelago")
    ]
    base_title = "Archipelago Team Fortress 2 Client"

    def build(self) -> Layout:
        super().build()
        self.tf2_tab = self.add_client_tab(title="TF2 Contracts", content=GridLayout(cols=3))
        self.update_tf2_tab()
        return self.container

    def update_tf2_tab(self):
        self.tf2_tab.content.clear_widgets()
        self.tf2_tab.content.cols = len(self.ctx.class_kill_reqs)
        if not self.ctx.is_connected():
            return

        for class_name in self.ctx.class_kill_reqs.keys():
            has_class = self.ctx.has_item(class_name)
            clr = (1, 1, 1, 1)
            if not has_class:
                clr = (1, 1, 1, 0.4)
            elif self.ctx.class_has_pending_objectives(class_name):
                clr = (0.3, 1, 1, 1)

            button = Button(text=class_name, size_hint_y=None, height=50, width=100, color=clr)
            if has_class:
                button.bind(on_release=lambda press, cls=class_name: self.show_weapon_grid(cls))

            self.tf2_tab.content.add_widget(button)

    def show_weapon_grid(self, class_name: str):
        self.update_tf2_tab()
        grid = GridLayout(cols=5, size_hint_y=None, col_default_width=150, col_force_default=True,
                          row_default_height=80, row_force_default=True)

        grid.add_widget(Label(text=f"Contract Points: {self.ctx.points}/{self.ctx.required_points}", size_hint_y=None,
                              color=(0.5, 0.5, 1, 1)))

        class_type = TFClass[class_name.upper()]
        class_kills = self.ctx.class_kill_counts.get(class_name, 0)
        class_count = self.ctx.class_kill_reqs.get(class_name)
        if class_count > 0:
            text = format(f"  Kills as {class_name}\n  {class_kills}/{class_count}")
            clr = (0.2, 1, 0.2, 1) if class_kills >= class_count else (1, 1, 0, 1) if class_kills > 0 else (1, 1, 1, 1)
            grid.add_widget(Label(text=text, size_hint_y=None, color=clr))

        for weapon, count in self.ctx.weapon_kill_reqs.items():
            if class_uses_weapon(class_type.tostr(), weapon):
                if self.ctx.has_item(weapon) or weapon in self.ctx.contract_hints:
                    weapon_kills = self.ctx.weapon_kill_counts.get(weapon, 0)
                    text = format(f"  {weapon}\n  {weapon_kills}/{count}")
                    clr = (0.2, 1, 0.2, 1) if weapon_kills >= count else (1, 1, 0.5, 1) if weapon_kills > 0 else (
                    1, 1, 1, 0.4) if not self.ctx.has_item(weapon) else (1, 1, 1, 1)
                    grid.add_widget(Label(text=text, size_hint_y=None, color=clr))
                else:
                    grid.add_widget(Label(text="?????", size_hint_y=None, color=(1, 1, 1, 0.4)))

        self.tf2_tab.content.add_widget(grid)

def launch():
    async def main():
        parser = get_base_parser()
        args = parser.parse_args()
        ctx = TF2Context(args.connect, args.password)
        if gui_enabled:
            ctx.run_gui()
        ctx.run_cli()

        logger.info("Starting Team Fortress 2 RCON")
        ctx.rcon_task = asyncio.create_task(rcon_loop(ctx), name="RCONLoop")
        await ctx.rcon_task
        await ctx.exit_event.wait()

    Utils.init_logging("TF2Client")
    # options = Utils.get_options()

    import colorama
    colorama.init()
    asyncio.run(main())
    colorama.deinit()
