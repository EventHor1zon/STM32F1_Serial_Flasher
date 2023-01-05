##
#   Attempt to applify STM flasher with textual's tutorial
#   Going pretty well, impressed with the appearance now
#
#   Let's think state machines...
#
#       IDLE (disconnected)  -> config port
#                            -> config baud
#                            -> connect (state = IDLE_CONNECTED)
#       IDLE (connected)     -> config option bytes (state = CONFIG_OPT_BYTES)
#                            -> read memory (state = READ_MEM)
#                            -> upload application (state = WRITE_MEM)
#                            -> erase flash (state = ERASE_MEM)
#

import sys

sys.path.append("../SerialFlasher")
from StmDevice import STMInterface
from constants import STM_BOOTLOADER_MAX_BAUD, STM_BOOTLOADER_MIN_BAUD

import asyncio
from asyncio.queues import Queue, QueueEmpty, QueueFull
from time import sleep

from rich.panel import Panel
from rich.table import Table, Column, Row
from rich.style import StyleType, Style
from rich.box import HEAVY, HEAVY_EDGE, SQUARE
from rich.console import RenderableType, Group
from rich.text import Text
from rich import print as rprint

from textual.app import App, ComposeResult
from textual.events import Event, Key
from textual.message import Message
from textual.reactive import reactive
from textual.containers import Container
from textual.widgets import (
    Header,
    Static,
    TextLog,
    Input,
)

from chip_image import ChipImage, generateFlashImage
import app_config as config

APPLICATION_NAME = "StmF1 Flasher Tool"
APPLICATION_VERSION = "0.0.1"
APPLICATION_BANNER = """
░█▀▀░▀█▀░█▄█░░░█▀▀░█░░░█▀█░█▀▀░█░█░█▀▀░█▀▄
░▀▀█░░█░░█░█░░░█▀▀░█░░░█▀█░▀▀█░█▀█░█▀▀░█▀▄
░▀▀▀░░▀░░▀░▀░░░▀░░░▀▀▀░▀░▀░▀▀▀░▀░▀░▀▀▀░▀░▀
"""


def SuccessMessage(msg):
    return Text.from_markup(
        f"[bold][[green]+[/green]][/bold] {msg}",
    )


def InfoMessage(msg):
    return Text.from_markup(f"[bold][[yellow]@[/yellow]][/bold] {msg}")


def FailMessage(msg):
    return Text.from_markup(f"[bold][[magenta]-[/magenta]][/bold] {msg}")


def ErrorMessage(msg):
    return Text.from_markup(f"[bold][[red]![/red]][/bold] {msg}")


def MARKUP(msg):
    return Text.from_markup(msg)


def binary_colour(
    condition: bool,
    true_str: str = None,
    false_str=None,
    true_fmt: str = "green",
    false_fmt: str = "red",
):
    true_msg = str(condition) if true_str is None else true_str
    false_msg = str(condition) if false_str is None else false_str
    return Text.from_markup(
        f"[{true_fmt if condition else false_fmt}]{true_msg if condition else false_msg}[/{true_fmt if condition else false_fmt}]"
    )


STATE_IDLE_DISCONNECTED = 0
STATE_IDLE_CONNECTED = 1
STATE_AWAITING_INPUT = 2
STATE_ERASE_MEM = 3
STATE_READ_MEM = 4
STATE_WRITE_MEM = 5
STATE_UPLOAD_APP = 6
STATE_ANY = 255

menu_template = f"""
[green]Actions[/green]
        
"""

panel_format = {
    "box": SQUARE,
    "expand": True,
    "title_align": "left",
    "border_style": Style(color="yellow"),
}


clear_table_format = {
    "show_edge": False,
    "show_header": False,
    "expand": True,
    "box": None,
    "padding": (0, 1),
}

connected = False
accept_input = False


class TextBox(Static):
    def __init__(
        self,
        renderable: RenderableType = "",
        *,
        expand: bool = False,
        shrink: bool = False,
        markup: bool = True,
        name=None,
        id=None,
        classes=None,
    ) -> None:
        super().__init__(
            renderable,
            expand=expand,
            shrink=shrink,
            markup=markup,
            name=name,
            id=id,
            classes=classes,
        )


class OptBytesDisplay(Static):
    def __init__(
        self,
        renderable: RenderableType = "",
        *,
        expand: bool = False,
        shrink: bool = False,
        markup: bool = True,
        name=None,
        id=None,
        classes=None,
    ) -> None:
        super().__init__(
            renderable,
            expand=expand,
            shrink=shrink,
            markup=markup,
            name=name,
            id=id,
            classes=classes,
        )
        self.styles.background = "black"


class StringGetter(Input):
    def __init__(
        self,
        value=None,
        placeholder: str = "",
        highlighter=None,
        password: bool = False,
        name=None,
        id=None,
        classes=None,
    ) -> None:
        super().__init__(
            value=value,
            placeholder=placeholder,
            highlighter=highlighter,
            password=password,
            name=name,
            id=id,
            classes=classes,
        )
        self.styles.background = "black"

    async def action_submit(self) -> None:
        await super().action_submit()
        self.reset_focus()
        self.value = ""


class StringPutter(TextLog):
    def __init__(
        self,
        *,
        max_lines=None,
        min_width: int = 78,
        wrap: bool = False,
        highlight: bool = False,
        markup: bool = False,
        name=None,
        id=None,
        classes=None,
    ) -> None:
        super().__init__(
            max_lines=max_lines,
            min_width=min_width,
            wrap=wrap,
            highlight=highlight,
            markup=markup,
            name=name,
            id=id,
            classes=classes,
        )

    def on_mount(self):
        self.write(f"Application Initialising....")
        self.write(f"{APPLICATION_NAME} v{APPLICATION_VERSION}")
        return super().on_mount()


class InfoDisplays(Static):
    """class to display the top three columns of the app
    display and update information about the device
    and commands
    added extra init args so we can populate the widgets
    as we yield them
    """

    def __init__(
        self,
        menu: RenderableType = "",
        info: RenderableType = "",
        opts: RenderableType = "",
        renderable: RenderableType = "",
        *,
        expand: bool = False,
        shrink: bool = False,
        markup: bool = True,
        name=None,
        id=None,
        classes=None,
    ) -> None:
        self.menu = menu
        self.info = info
        self.opts = opts
        super().__init__(
            renderable,
            expand=expand,
            shrink=shrink,
            markup=markup,
            name=name,
            id=id,
            classes=classes,
        )

    def compose(self) -> ComposeResult:
        yield TextBox(self.menu, id="menu")
        yield TextBox(self.info, id="info")
        yield OptBytesDisplay(self.opts, id="opts")


class StmApp(App):

    ## Path to CSS - used mostly for layout
    ## Try to use config variables for easier styling
    CSS_PATH = "./css/stmapp_css.css"

    ## keep track of expected input so we know
    ## when to pay attention to the input box
    state = STATE_IDLE_DISCONNECTED

    ## Device model
    stm_device = STMInterface()

    ## internal state variables
    ## TODO: use less of these
    #   Need - connect-opts
    #        - io opts

    connected = False
    conn_port = ""
    conn_baud = 9600
    address = None
    read_len = 0
    offset = 0
    filepath = None

    ## Default tables & widget definitions
    conn_table = None
    dev_table = None
    chip_image = """"""
    chip = None
    default_conn_info = Table("", "", **clear_table_format)

    default_device_info = Panel(
        Text.from_markup(
            "No Device",
            style=Style(color="red", bold=True, italic=True, blink=True),
        ),
        title="[bold orange]Device[/bold orange]",
        **panel_format,
    )

    banner = Static(APPLICATION_BANNER, expand=True, id="banner")
    msg_log = StringPutter(max_lines=8, name="msg_log", id="msg_log")
    input = StringGetter(placeholder=">>>")

    ### initialise page info
    def build_items(self):

        self.default_conn_info.add_row("", "")
        self.default_conn_info.add_row(
            "Connected    ",
            binary_colour(self.connected),
        )
        self.default_conn_info.add_row("Port         ", f"{self.conn_port}")
        self.default_conn_info.add_row("Baud         ", f"{self.conn_baud}")

        ## build the keypress menu items
        self.dc_menu_items = [
            {
                "key": config.KEY_PORT,
                "description": "Set Port",
                "state": STATE_IDLE_DISCONNECTED,
                "action": self.handle_port_keypress,
            },
            {
                "key": config.KEY_BAUD,
                "description": "Set Baud",
                "state": STATE_IDLE_DISCONNECTED,
                "action": self.handle_baud_keypress,
            },
            {
                "key": config.KEY_CONN,
                "description": "Connect",
                "state": STATE_IDLE_DISCONNECTED,
                "action": self.handle_connect_keypress,
            },
        ]

        self.any_menu_items = [
            {
                "key": config.KEY_EXIT,
                "description": "Exit",
                "state": STATE_ANY,
                "action": self.handle_exit_keypress,
            },
            {
                "key": config.KEY_VERS,
                "description": "Print Version",
                "state": STATE_ANY,
                "action": self.handle_vers_keypress,
            },
        ]

        self.read_menu = [
            {
                "key": config.KEY_FILE,
                "description": "set file path",
                "action": self.handle_filepath_keypress,
            },
            {
                "key": "o",
                "description": "Configure offset",
                "action": self.handle_offset_keypress,
            },
            {
                "key": "l",
                "description": "Read length",
                "action": None,
            },
            {
                "key": config.KEY_RDFS,
                "description": "Read memory",
                "action": None,
            },
        ]

        self.upload_menu_items = [
            {
                "key": config.KEY_FILE,
                "description": "set file path",
                "action": None,
            },
            {
                "key": "o",
                "description": "Configure offset",
                "action": None,
            },
            {
                "key": "w",
                "description": "Write file contents to flash",
                "action": None,
            },
        ]

        self.con_menu_items = [
            {
                "key": config.KEY_RDRM,
                "description": "Read RAM to file",
                "state": STATE_IDLE_CONNECTED,
                "action": None,
            },
            {
                "key": config.KEY_WRRM,
                "description": "Write file data to ram",
                "state": STATE_IDLE_CONNECTED,
                "action": None,
            },
            {
                "key": config.KEY_UPLD,
                "description": "Upload application to flash",
                "state": STATE_IDLE_CONNECTED,
                "action": None,
            },
            {
                "key": config.KEY_ERFS,
                "description": "Erase all flash",
                "state": STATE_IDLE_CONNECTED,
                "action": self.handle_erase_keypress,
            },
            {
                "key": config.KEY_RDFS,
                "description": "Read flash memory",
                "state": STATE_IDLE_CONNECTED,
                "action": self.handle_readflash_keypress,
            },
            {
                "key": config.KEY_DCON,
                "description": "Disconnect from device",
                "state": STATE_IDLE_CONNECTED,
                "action": None,
            },
            {
                "key": config.KEY_RDPAGES,
                "description": "Read flash pages",
                "state": STATE_IDLE_CONNECTED,
                "action": self.handle_readpages_keypress,
            },
        ]

        self.active_menu = self.dc_menu_items

        ## there's probably a more elegent way of doing this but it works
        self.main_display = InfoDisplays(
            menu=self.build_menu(),
            info=Panel(
                Group(
                    Panel(
                        self.default_conn_info,
                        title="[bold yellow]Connection[/bold yellow]",
                        **panel_format,
                    ),
                    self.default_device_info,
                    fit=True,
                ),
                **panel_format,
            ),
            opts="",
        )

    def __init__(self, driver_class=None, css_path=None, watch_css: bool = False):

        self.build_items()
        self.msg_queue = Queue(10)
        super().__init__(driver_class, css_path, watch_css)

    ### Widgets & tables updates

    def compose(self) -> ComposeResult:
        yield Header()
        yield self.banner
        yield self.main_display
        yield self.msg_log
        yield self.input

    def dev_content_from_state(self):
        if self.state == STATE_READ_MEM or self.state == STATE_WRITE_MEM:
            return Group(
                self.build_readwrite_table(),
                self.build_device_table(),
                self.chip.chip_image,
            )
        elif self.state == STATE_IDLE_DISCONNECTED:
            return Group(self.build_conn_table(), self.default_device_info, "")
        else:
            return Group(
                self.build_conn_table(), self.build_device_table(), self.chip.chip_image
            )

    def update_tables(self):
        dev_info = self.get_widget_by_id("info")
        menu = self.get_widget_by_id("menu")
        opts = self.get_widget_by_id("opts")

        dev_content = self.dev_content_from_state()
        opts_content = "" if self.connected == False else self.build_opts_table()

        dev_info.update(
            Panel(
                dev_content,
                **panel_format,
            )
        )

        opts.update(
            Panel(
                opts_content,
                **panel_format,
            )
        )

        menu.update(self.build_menu())

    def build_menu(self):
        menu = menu_template

        for opt in self.active_menu:
            menu += f"[bold]{opt['key']}[/bold]: {opt['description']}\n"

        menu += "\n"
        for opt in self.any_menu_items:
            menu += f"[bold]{opt['key']}[/bold]: {opt['description']}\n"

        return Panel(
            Text.from_markup(menu),
            title="[bold red]Menu[/bold red]",
            **panel_format,
        )

    def build_opts_table(self) -> Table:
        opts_table = Table(
            "Option Byte", "Value", padding=(0, 1), expand=True, show_edge=False
        )
        opts_table.add_row("", "")
        opts_table.add_row(
            "Read Protect",
            binary_colour(
                self.stm_device.device.opt_bytes.readProtect,
                true_str="enabled",
                false_str="disabled",
                false_fmt="blue",
            ),
        )
        opts_table.add_row(
            "Watchdog Type",
            binary_colour(
                self.stm_device.device.opt_bytes.watchdogType,
                false_str="Hardware",
                true_str="Software",
                false_fmt="blue",
            ),
        )
        opts_table.add_row(
            "Rst on Standby",
            binary_colour(
                self.stm_device.device.opt_bytes.resetOnStandby,
                true_str="enabled",
                false_str="disabled",
                false_fmt="blue",
            ),
        )
        opts_table.add_row(
            "Rst on Stop",
            binary_colour(
                self.stm_device.device.opt_bytes.resetOnStop,
                true_str="enabled",
                false_str="disabled",
                false_fmt="blue",
            ),
        )
        opts_table.add_row(
            "Data Byte 0", f"{hex(self.stm_device.device.opt_bytes.dataByte0)}"
        )
        opts_table.add_row(
            "Data Byte 1", f"{hex(self.stm_device.device.opt_bytes.dataByte1)}"
        )
        opts_table.add_row(
            "Write Prot 0", str(self.stm_device.device.opt_bytes.writeProtect0)
        )
        opts_table.add_row(
            "Write Prot 1", str(self.stm_device.device.opt_bytes.writeProtect1)
        )
        opts_table.add_row(
            "Write Prot 2", str(self.stm_device.device.opt_bytes.writeProtect2)
        )
        opts_table.add_row(
            "Write Prot 3", str(self.stm_device.device.opt_bytes.writeProtect3)
        )
        return Panel(
            opts_table,
            title="[bold cyan]Flash Option bytes[/bold cyan]",
            **panel_format,
        )

    def build_device_table(self) -> Table:
        device_table = Table("", "", **clear_table_format)
        device_table.add_row("", "")  # spacer
        device_table.add_row("Device Type   ", f"{self.stm_device.device.name}")
        device_table.add_row("Device ID     ", f"{hex(self.stm_device.getDeviceId())}")
        device_table.add_row(
            "Bootloader v  ", f"{str(self.stm_device.getDeviceBootloaderVersion())}"
        )
        device_table.add_row(
            "Flash Size    ", f"{hex(self.stm_device.device.flash_memory.size)}"
        )
        device_table.add_row(
            "Flash Pages   ",
            f"{self.stm_device.device.flash_page_num} Pages of {self.stm_device.device.flash_page_size}b",
        )
        device_table.add_row(
            "RAM Size      ", f"{hex(self.stm_device.device.ram.size)}"
        )
        self.dev_table = Panel(
            device_table, title="[bold yellow]Device[/bold yellow]", **panel_format
        )

        return self.dev_table

    def build_conn_table(self) -> Table:
        conn_table = Table("", "", **clear_table_format)
        conn_table.add_row("", "")  # spacer
        conn_table.add_row(
            "Connected    ",
            binary_colour(self.connected),
        )
        conn_table.add_row("Port         ", self.conn_port)
        conn_table.add_row("Baud         ", str(self.conn_baud))
        self.conn_table = Panel(
            conn_table, title="[bold yellow]Connection[/bold yellow]", **panel_format
        )
        return self.conn_table

    def build_readwrite_table(self) -> Table:
        rw_table = Table("", "", **clear_table_format)
        rw_table.add_row("", "")
        rw_table.add_row(
            "Operation     ",
            binary_colour(
                True if self.state == STATE_READ_MEM else False,
                true_str="Read",
                false_str="Write",
                true_fmt="green",
                false_fmt="blue",
            ),
        )
        rw_table.add_row("Address       ", f"{hex(self.address)}")
        rw_table.add_row("Length        ", f"{self.read_len}")
        rw_table.add_row("Offset        ", f"{self.offset}")
        rw_table.add_row("File path     ", f"{self.filepath}")

        return Panel(rw_table, title="[bold yellow]IO[/bold yellow]", **panel_format)

    def idle_state(self):
        return STATE_IDLE_DISCONNECTED if not self.connected else STATE_IDLE_CONNECTED

    def handle_connected(self):
        self.msg_log.write(SuccessMessage("Successfully connected!"))
        self.msg_log.write(
            SuccessMessage(f"Found device: {self.stm_device.device.name}")
        )
        self.msg_log.write(
            SuccessMessage(
                f"Flash start: {hex(self.stm_device.device.flash_memory.start)}"
            )
        )
        self.msg_log.write(
            SuccessMessage(
                f"Flash size: {hex(self.stm_device.device.flash_memory.size)}"
            )
        )
        self.chip = ChipImage(self.stm_device.device.name)
        self.active_menu = self.con_menu_items
        self.state = STATE_IDLE_CONNECTED
        self.update_tables()

    def device_connect(self) -> bool:
        success = False
        try:
            self.msg_log.write(
                InfoMessage(
                    f"Connecting to device on {self.conn_port} at {self.conn_baud}bps"
                )
            )
            success = self.stm_device.connectAndReadInfo(
                self.conn_port, baud=self.conn_baud, readOptBytes=True
            )
        except Exception as e:
            self.msg_log.write(e)
        finally:
            return success

    ### OPERATIONS ##

    async def long_running_task(self, function, *func_args):
        dev_info = self.get_widget_by_id("info")
        task = asyncio.get_running_loop().run_in_executor(None, function, *func_args)
        while not task.done():
            dev_info.update(
                Panel(
                    Group(
                        self.build_conn_table(),
                        self.build_device_table(),
                        next(self.chip),
                    ),
                    **panel_format,
                )
            )
            await asyncio.sleep(0.1)
        dev_info.update(
            Panel(
                Group(
                    self.build_conn_table(),
                    self.build_device_table(),
                    self.chip.chip_image,
                ),
                **panel_format,
            )
        )
        return task.result()

    async def input_to_attribute(self, msg: str, attribute: str, ex_type=str):
        """awaits user input and sets the variable
        @param attribute - the attribute to set
        @param ex_type - expected type (tries to convert)
        """
        prev_state = self.state
        self.state = STATE_AWAITING_INPUT
        self.msg_log.write(InfoMessage(f"{msg}"))
        self.set_focus(self.input)

        msg = await self.msg_queue.get()
        try:
            msg_fmtd = ex_type(msg)
            setattr(self, attribute, msg_fmtd)
            self.msg_log.write(InfoMessage(f"Set {attribute} to {msg_fmtd}"))
        except ValueError:
            self.msg_log.write(ErrorMessage(f"Invalid type: expected {ex_type}"))
        finally:
            self.state = prev_state

    ### KEYPRESS HANDLERS ###

    async def handle_vers_keypress(self):
        """handle print version keypress"""
        self.msg_log.write(
            InfoMessage(f"{APPLICATION_NAME} Version {APPLICATION_VERSION}")
        )
        self.state = self.idle_state()

    async def handle_port_keypress(self):
        """handle port input keypress"""
        await self.input_to_attribute("Enter connection port", "conn_port")
        self.update_tables()

    async def handle_baud_keypress(self):
        """handle baud input keypress"""
        await self.input_to_attribute("Enter connection baud", "conn_baud")
        self.update_tables()

    async def handle_connect_keypress(self):
        """handle the 'connect' keypress
        check parameters are set and connect to
        the STM device bootloader
        """
        if len(self.conn_port) == 0:
            self.msg_log.write(FailMessage("Must configure port first"))
        elif (
            self.conn_baud < STM_BOOTLOADER_MIN_BAUD
            or self.conn_baud > STM_BOOTLOADER_MAX_BAUD
        ):
            self.msg_log.write(
                FailMessage(
                    f"Invalid baud - min: {STM_BOOTLOADER_MIN_BAUD} max: {STM_BOOTLOADER_MAX_BAUD}"
                )
            )
        else:
            self.connected = self.device_connect()
            if self.connected == True:
                self.handle_connected()

    async def handle_readflash_keypress(self):
        """handle the 'read flash' keypress
        update menu to readwrite and update tables
        """
        self.state = STATE_READ_MEM
        self.active_menu = self.read_menu
        self.address = self.stm_device.device.flash_memory.start
        self.update_tables()

    async def handle_erase_keypress(self):
        """handle the erase keypress
        calls the globalErase operation on the device
        """
        self.msg_log.write(InfoMessage("Erasing flash memory..."))
        await self.long_running_task(self.stm_device.globalEraseFlash)
        self.msg_log.write(SuccessMessage("Succesfully erased all flash pages"))

    async def handle_readpages_keypress(self):
        self.msg_log.write(InfoMessage("Reading flash pages..."))
        occupied = 0
        empty = 0
        errors = 0

        for i in range(self.stm_device.device.flash_page_num):
            self.msg_log.write(InfoMessage(f"Reading flash pages {i}"))
            success, rx = await self.long_running_task(
                self.stm_device.readFromFlash,
                self.stm_device.device.flash_pages[i].start,
                self.stm_device.device.flash_page_num,
            )
            if not success:
                self.msg_log.write(FailMessage(f"Error reading flash page {i}"))
                errors += 1
            else:
                page_empty = True
                for b in rx:
                    if b != 0xFF:
                        page_empty = False
                        occupied += 1
                        break
                if page_empty == True:
                    empty += 1

        self.msg_log.write(
            InfoMessage(
                f"Read {self.stm_device.device.flash_page_num} pages (errors: {errors})"
            )
        )
        self.msg_log.write(
            InfoMessage(f"Page status-> Occupied pages: {occupied} Free pages: {empty}")
        )

    async def handle_filepath_keypress(self):
        self.msg_log.write(InfoMessage("Enter file path"))
        self.set_focus(self.input)
        ## wait for user input
        filepath = await self.msg_queue.get()
        filepath = filepath.strip("\n").strip("\r")
        if len(filepath) < 1:
            self.msg_log.write(ErrorMessage("Error - invalid filepath length"))
            return
        self.filepath = filepath
        self.update_tables()

    async def handle_offset_keypress(self):
        await self.input_to_attribute(
            "Enter offset from start address", self.offset, int
        )
        self.update_tables()

    async def handle_upload_keypress(self):
        pass

    def handle_exit_keypress(self):
        print("Bye!")
        sys.exit()

    async def handle_key(self, key: str):

        ## debug keybindings
        if key == "@":
            self.action_screenshot()

        if key == "l":
            await self.long_running_task(sleep, 5)

        ## menu commands
        for command in self.active_menu:
            if key == command["key"] and command["action"] is not None:
                asyncio.create_task(command["action"]())

    async def _on_key(self, event: Key) -> None:
        await super()._on_key(event)
        await self.handle_key(event.char)

    async def read_from_flash(self):
        if self.filepath is not None and self.read_len > 0:
            success = True
            chunks = int(self.read_len / 256)
            rem = int(self.read_len % 256)

            with open(self.filepath, "wb") as f:
                for i in range(chunks):
                    self.msg_log.write(InfoMessage(f"Reading chunk {i+1}"))
                    success, rx = self.stm_device.readFromFlash(
                        self.stm_device.device.flash_memory.start + self.offset,
                        256,
                    )
                    if success:
                        f.write(rx)
                    else:
                        self.msg_log.write(ErrorMessage(f"Error Reading chunk {i+1}"))
                        break

                if rem > 0 and success == True:
                    self.msg_log.write(InfoMessage(f"Reading chunk {chunks+1}"))
                    success, rx = self.stm_device.readFromFlash(
                        self.stm_device.device.flash_memory.start
                        + self.offset
                        + (chunks * 256),
                        rem,
                    )
                    if success:
                        f.write(rx)
                    else:
                        self.msg_log.write(
                            ErrorMessage(f"Error Reading chunk {chunks+1}")
                        )
            if success:
                self.msg_log.write(
                    SuccessMessage(
                        f"Succesfully read {self.read_len} bytes from flash into file {self.filepath}"
                    )
                )

        ## clear the self variables
        self.read_len = 0
        self.filepath = None
        self.offset = 0

    async def on_input_submitted(self, message: Input.Submitted) -> None:
        if self.state != STATE_AWAITING_INPUT:
            ## we are not expecting any inputs so ignore here
            pass
        else:
            ## send to message queue
            await self.msg_queue.put(message.value)


if __name__ == "__main__":
    app = StmApp()
    app.run()
