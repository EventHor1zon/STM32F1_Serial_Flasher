##
#   Attempt to applify STM flasher with textual's tutorial
#
#
#
#
#

import sys

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
    Button,
    Header,
    Footer,
    Static,
    TextLog,
    DataTable,
    Input,
    Label,
    Placeholder,
)


APPLICATION_NAME = "StmF1 Flasher Tool"
APPLICATION_VERSION = "0.0.1"
APPLICATION_BANNER = """
░█▀▀░▀█▀░█▄█░░░█▀▀░█░░░█▀█░█▀▀░█░█░█▀▀░█▀▄
░▀▀█░░█░░█░█░░░█▀▀░█░░░█▀█░▀▀█░█▀█░█▀▀░█▀▄
░▀▀▀░░▀░░▀░▀░░░▀░░░▀▀▀░▀░▀░▀▀▀░▀░▀░▀▀▀░▀░▀
"""


print(f"{sys.path}")

import os

print(os.getcwd())
sys.path.append("../SerialFlasher")
print(f"{sys.path}")
from StmDevice import STMInterface


def SuccessMessage(msg):
    return Text(f"[+] {msg}", "bold italic green")


def InfoMessage(msg):
    return Text(f"[@] {msg}", "italic yellow")


def FailMessage(msg):
    return Text(f"[-] {msg}", "bold italic orange")


def ErrorMessage(msg):
    return Text(f"[!] {msg}", "bold red")


INPUT_TYPE_NONE = 0
INPUT_TYPE_PORT = 1
INPUT_TYPE_BAUD = 2
INPUT_TYPE_FILEPATH = 3


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

    disconnected_msg = Panel(
        Text.from_markup(
            """


[green]Actions[/green]

    [bold]c[/bold]: Connect to Device
    [bold]v[/bold]: Print Version
    [bold]b[/bold]: Set Baud
    [bold]p[/bold]: Set Port

    [bold]x[/bold]: Exit

    """
        ),
        box=SQUARE,
        title="[bold red]Menu[/bold red]",
        expand=True,
        title_align="left",
        border_style=Style(color="yellow"),
    )

    connected_msg = Panel(
        Text.from_markup(
            """


[green]Actions[/green]

    [bold]r[/bold]: Read Flash memory
    [bold]m[/bold]: Read RAM
    [bold]e[/bold]: Erase all flash
    [bold]u[/bold]: Upload application to flash
    [bold]o[/bold]: Configure option bytes

    [bold]x[/bold]: Exit

    """
        ),
        box=SQUARE,
        title="[bold red]Menu[/bold red]",
        expand=True,
        title_align="left",
        border_style=Style(color="yellow"),
    )

    # BINDINGS = [("d", "toggle_dark", "Toggle dark mode")]
    CSS_PATH = "./css/stmapp_css.css"

    connected = False
    stm_device = STMInterface()
    conn_port = ""
    conn_baud = 9600

    default_conn_info = Table(
        "",
        "",
        show_edge=False,
        show_header=False,
        expand=True,
        box=None,
        padding=(0, 1),
    )

    default_device_info = Panel(
        Text.from_markup(
            "No Device",
            style=Style(color="red", bold=True, italic=True, blink=True),
        ),
        box=SQUARE,
        title="[bold orange]Device[/bold orange]",
        expand=True,
        title_align="left",
        border_style=Style(color="yellow"),
    )

    banner = Static(APPLICATION_BANNER, expand=True, id="banner")
    msg_log = StringPutter(max_lines=8, name="msg_log", id="msg_log")

    ## there's probably a more elegent way of doing this but it works
    main_display = InfoDisplays(
        menu=disconnected_msg,
        info=Panel(
            Group(
                Panel(
                    default_conn_info,
                    box=SQUARE,
                    title="[bold yellow]Connection[/bold yellow]",
                    expand=True,
                    title_align="left",
                    border_style=Style(color="yellow"),
                ),
                default_device_info,
                fit=True,
            ),
            box=SQUARE,
            expand=True,
            border_style=Style(color="yellow"),
        ),
        opts="",
    )
    input = StringGetter()

    ## keep track of expected input so we know
    ## when to pay attention to the input box
    awaiting = INPUT_TYPE_NONE

    def __init__(self, driver_class=None, css_path=None, watch_css: bool = False):
        self.default_conn_info.add_row(
            "Connected    ",
            Text.from_markup(
                f"[red]{self.connected}[/red]"
                if not self.connected
                else f"[green]{self.connected}[/green]"
            ),
        )
        self.default_conn_info.add_row("Port         ", f"{self.conn_port}")
        self.default_conn_info.add_row("Baud         ", f"{self.conn_baud}")
        super().__init__(driver_class, css_path, watch_css)

    def compose(self) -> ComposeResult:
        yield Header()
        yield self.banner
        yield self.main_display
        yield self.msg_log
        yield self.input

    def update_tables(self):
        print("Updating tables")
        dev_info = self.get_widget_by_id("info")
        menu = self.get_widget_by_id("menu")
        opts = self.get_widget_by_id("opts")

        if self.connected:
            dev_info.update(
                Panel(Group(self.build_conn_table(), self.build_device_table()))
            )

            menu.update(self.connected_msg)

            opts.update(self.build_opts_table())
        else:
            dev_info.update(
                Panel(
                    Group(self.build_conn_table(), self.default_device_info),
                    box=SQUARE,
                    expand=True,
                    border_style=Style(color="yellow"),
                )
            )
            opts.update("")
            menu.update(self.disconnected_msg)

    def build_opts_table(self) -> Table:
        opts_table = Table(
            "Option Byte", "Value", padding=(0, 1), expand=True, show_edge=False
        )
        opts_table.add_row(
            "Read Protect",
            Text.from_markup(
                "[green]enabled[/green]"
                if self.stm_device.device.opt_bytes.readProtect
                else "[orange]disabled[/orange]"
            ),
        )
        opts_table.add_row(
            "Watchdog Type",
            Text.from_markup(
                "[yellow]Hardware[/yellow]"
                if not self.stm_device.device.opt_bytes.watchdogType
                else "[purple]Software[/purple]"
            ),
        )
        opts_table.add_row(
            "Rst on Standby",
            SuccessMessage("enabled")
            if self.stm_device.device.opt_bytes.resetOnStandby
            else SuccessMessage("Disabled"),
        )
        opts_table.add_row(
            "Rst on Stop",
            SuccessMessage("enabled")
            if self.stm_device.device.opt_bytes.resetOnStop
            else SuccessMessage("Disabled"),
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
        return Panel(opts_table, box=SQUARE, border_style=Style(color="yellow"))

    def build_device_table(self) -> Table:
        device_table = Table(
            "",
            "",
            box=SQUARE,
            show_header=False,
            title_style="bold yellow",
            title_justify="left",
            show_edge=False,
            padding=(0, 1),
        )
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
        return Panel(
            device_table,
            box=SQUARE,
            border_style=Style(color="yellow"),
        )

    def build_conn_table(self) -> Table:
        conn_table = Table(
            "",
            "",
            show_edge=False,
            show_header=False,
            expand=True,
            box=None,
            padding=(0, 1),
        )
        conn_table.add_row(
            "Connected    ",
            Text.from_markup(
                f"[red]{self.connected}[/red]"
                if not self.connected
                else f"[green]{self.connected}[/green]"
            ),
        )
        conn_table.add_row("Port         ", self.conn_port)
        conn_table.add_row("Baud         ", str(self.conn_baud))
        return Panel(
            conn_table,
            box=SQUARE,
            title="[bold yellow]Connection[/bold yellow]",
            border_style=Style(color="yellow"),
        )

    def handle_connected(self):
        self.msg_log.write(SuccessMessage("Successfully connected!"))
        self.msg_log.write(
            SuccessMessage(f"Found device: {self.stm_device.device.name}")
        )
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
            print(e)
            self.msg_log.write(e)
        finally:
            return success

    async def _on_key(self, event: Key) -> None:
        if not self.connected:
            if event.char == "p":
                self.msg_log.write(InfoMessage("Enter Port: "))
                self.awaiting = INPUT_TYPE_PORT
                self.set_focus(self.input)
            elif event.char == "c" and len(self.conn_port) == 0:
                self.msg_log.write(ErrorMessage("Error - must configure port first"))
                self.awaiting = INPUT_TYPE_PORT
                self.set_focus(self.input)
            elif event.char == "c":
                self.connected = self.device_connect()
                if self.connected == True:
                    self.handle_connected()
            elif event.char == "b":
                self.awaiting = INPUT_TYPE_BAUD
                self.msg_log.write("Enter baud: ")
                self.set_focus(self.input)
        else:
            if event.char == "r":
                pass
        return await super()._on_key(event)

    async def on_input_submitted(self, message: Input.Submitted) -> None:
        if self.awaiting == INPUT_TYPE_NONE:
            pass
        elif self.awaiting == INPUT_TYPE_PORT:
            self.conn_port = message.value
            self.msg_log.write(InfoMessage(f"Setting port to {self.conn_port}"))
            self.update_tables()
        elif self.awaiting == INPUT_TYPE_BAUD:
            try:
                self.conn_baud = int(message.value)
                self.msg_log.write(InfoMessage(f"Setting baud to {self.conn_baud}"))
                self.update_tables()
            except ValueError:
                self.msg_log.write(ErrorMessage("Invalid baud"))
        elif self.awaiting == INPUT_TYPE_FILEPATH:
            self.filepath = message.value
        else:
            pass
        self.awaiting = INPUT_TYPE_NONE
        self.input.value = ""


if __name__ == "__main__":
    app = StmApp()
    app.run()
