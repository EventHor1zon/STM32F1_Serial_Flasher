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
from rich.style import StyleType
from rich.box import HEAVY, HEAVY_EDGE, SQUARE
from rich.text import Text
from rich import print as rprint
from textual.app import App, ComposeResult
from textual.events import Event, Key
from textual.message import Message
from textual.reactive import reactive
from textual.containers import Container
from textual.widgets import Button, Header, Footer, Static, TextLog, DataTable, Input, Label, Placeholder


APPLICATION_NAME="StmF1 Flasher Tool"
APPLICATION_VERSION="0.0.1"

print(f"{sys.path}")

import os
print(os.getcwd())
sys.path.append("../SerialFlasher")
print(f"{sys.path}")
from StmDevice import STMInterface



def SuccessMessage(msg):
    return Text(f"[white][[green]+[white]][green] {msg}", "bold italic")

def InfoMessage(msg):
    return Text(f"[white][[yellow]@[white]][yellow] {msg}", "bold italic")

def FailMessage(msg):
    return Text(f"[white][[orange]-[white]][orange] {msg}", "bold italic")

def ErrorMessage(msg):
    return Text(msg, "bold red")

INPUT_TYPE_NONE = 0
INPUT_TYPE_PORT = 1
INPUT_TYPE_BAUD = 2
INPUT_TYPE_FILEPATH = 3


connected = False
accept_input = False


disconnected_msg = Panel(f"""
    Options:
        c: Connect to Device
        v: Print Version
        b: Set Baud
        x: Exit
    connected: {connected}
""", box=SQUARE, title="[red]Welcome To STM Flasher[/red]", highlight=True, expand=True)

connected_msg = Panel(f"""
    Options:
        e: Erase all flash
        u: Upload application to flash
        r: Read device info
        o: Read option bytes
        x: Exit

    connected: {connected}
""", box=SQUARE, title="[red]Welcome To STM Flasher[/red]", highlight=True, expand=True)

conn_table = Table("", "", box=SQUARE, show_header=False, title="Device Info", title_style="bold yellow", title_justify="left", show_edge=False)



class OptBytesDisplay(Static):

    def update_table(self, device: STMInterface):
        t = Table("Option Byte", "Value", padding=(0, 1), expand=True, show_edge=False)
        t.add_row("Read Protect", SuccessMessage('enabled') if device.device.opt_bytes.readProtect else ErrorMessage('disabled'))
        t.add_row("Watchdog Type", "Hardware" if not device.device.opt_bytes.watchdogType else "Software")
        t.add_row("Rst on Standby", SuccessMessage('enabled') if device.device.opt_bytes.resetOnStandby else SuccessMessage("Disabled"))
        t.add_row("Rst on Stop", SuccessMessage('enabled') if device.device.opt_bytes.resetOnStop else SuccessMessage("Disabled"))
        t.add_row("Data Byte 0", f"{hex(device.device.opt_bytes.dataByte0)}")
        t.add_row("Data Byte 1", f"{hex(device.device.opt_bytes.dataByte1)}")
        t.add_row("Write Prot 0", str(device.device.opt_bytes.writeProtect0))
        t.add_row("Write Prot 1", str(device.device.opt_bytes.writeProtect1))
        t.add_row("Write Prot 2", str(device.device.opt_bytes.writeProtect2))
        t.add_row("Write Prot 3", str(device.device.opt_bytes.writeProtect3))
        self.update(Panel(t))


class StringGetter(Input):

    def __init__(self, value= None, placeholder: str = "", highlighter= None, password: bool = False, name= None, id= None, classes= None) -> None:
        super().__init__(value=value, placeholder=placeholder, highlighter=highlighter, password=password, name=name, id=id, classes=classes)
        self.styles.background = "black"


    async def action_submit(self) -> None:
        await super().action_submit()
        self.reset_focus()


class StringPutter(TextLog):

    def __init__(self, *, max_lines= None, min_width: int = 78, wrap: bool = False, highlight: bool = False, markup: bool = False, name= None, id= None, classes= None) -> None:
        super().__init__(max_lines=max_lines, min_width=min_width, wrap=wrap, highlight=highlight, markup=markup, name=name, id=id, classes=classes)

    def on_mount(self):
        self.write(f"Application Initialising....")
        self.write(f"{APPLICATION_NAME} v{APPLICATION_VERSION}")
        return super().on_mount()



class InfoDisplays(Static):
    """ class to display the top three columns of the app 
        display and update information about the device
        and commands
    """
    def compose(self) -> ComposeResult:
        yield Static(disconnected_msg if not connected else connected_msg, id="first")
        yield Static(conn_table, id="second")
        yield OptBytesDisplay(id="opts")


class StmApp(App):
    
    # BINDINGS = [("d", "toggle_dark", "Toggle dark mode")]
    CSS_PATH = "./css/stmapp_css.css"

    stm_device = STMInterface()
    conn_port = None
    conn_baud = 9600

    msg_log = StringPutter(max_lines=5, name="msg_log", id="msg_log")
    main_display = InfoDisplays()
    input = StringGetter()
    awaiting = INPUT_TYPE_NONE

    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()
        yield self.main_display
        yield self.msg_log
        yield self.input

    def build_device_table(self):
        conn_table.add_row("Device Type :", f"{self.stm_device.device.name}")
        conn_table.add_row("Device ID   :", f"{hex(self.stm_device.getDeviceId())}")
        conn_table.add_row("Flash Size  :", f"{hex(self.stm_device.device.flash_memory.size)}")
        conn_table.add_row("Flash Pages :", f"{self.stm_device.device.flash_page_num} Pages of {self.stm_device.device.flash_page_size}b")
        conn_table.add_row("RAM Size    :", f"{hex(self.stm_device.device.ram.size)}")

    def handle_connected(self):
        self.msg_log.write(SuccessMessage("Successfully connected!"))
        self.msg_log.write(SuccessMessage(f"Found device: {self.stm_device.device.name}"))
        self.build_device_table()
        dev_info = self.get_widget_by_id("second")
        dev_info.update(conn_table)
        message = self.get_widget_by_id("first")
        message.update(connected_msg)
        opts = self.get_widget_by_id("opts")
        opts.update_table(self.stm_device)

    def device_connect(self):
        success = False
        try:
            self.msg_log.write(Text(f"> Connecting to device on {self.conn_port} at {self.conn_baud}bps", "yellow"))
            success = self.stm_device.connectAndReadInfo(self.conn_port, baud=self.conn_baud, readOptBytes=True)
        except Exception as e:
            print(e)
            self.msg_log.write(e)
        finally:
            return success

    async def _on_key(self, event: Key) -> None:
        if not connected:
            if event.char == "c" and self.conn_port == None:
                self.awaiting = INPUT_TYPE_PORT
                self.msg_log.write("Connect - Enter port")
                self.set_focus(self.input)
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
            connected = self.device_connect()
            if connected == True:
                self.handle_connected()
        elif self.awaiting == INPUT_TYPE_BAUD:
            try:
                self.conn_baud = int(message.value)
                self.msg_log.write(InfoMessage(f"Setting baud to {self.conn_baud}"))
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