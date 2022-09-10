from asciimatics.screen import Screen
from asciimatics.scene import Scene
from asciimatics.effects import Cycle, Stars
from asciimatics.renderers import FigletText
from asciimatics.widgets.frame import Frame
from asciimatics.widgets.layout import Layout
from asciimatics.widgets.text import Text
from asciimatics.widgets.textbox import TextBox
from asciimatics.widgets.listbox import ListBox
from asciimatics.widgets.label import Label
from asciimatics.widgets.divider import Divider
from asciimatics.widgets import Widget
from asciimatics.constants import COLOUR_GREEN, A_BOLD
import sys
sys.path.append('..')
from SerialFlasher.StmDevice import STMInterface
from time import sleep
from serial import Serial
from rich import print as rprint
from rich.panel import Panel

TOOLNAME = "STM32F1 Serial Flasher"
TOOL_VERSION = 0.01
COLOUR_PRIMARY = COLOUR_GREEN
BORDER_WIDTH=1
TITLE_OFFSET_W = 8
TITLE_OFFSET_H = 2

def printTitle(screen: Screen):
    screen.print_at(TOOLNAME, TITLE_OFFSET_W, TITLE_OFFSET_H, COLOUR_PRIMARY, A_BOLD)

def drawBorders(screen: Screen, thin=False):
    ## screen border
    screen.move(0,0)
    screen.draw(screen.width-1, 0, thin=thin, colour=COLOUR_PRIMARY)
    screen.draw(screen.width-1, screen.height-1, thin=thin)
    screen.draw(0, screen.height-1, thin=thin)
    screen.draw(0, 0, thin=thin)
    
    ## draw horz border
    screen.move(0, screen.height / 2)
    screen.draw(screen.width-1, screen.height / 2, thin=thin, colour=COLOUR_PRIMARY)

    ## draw top vertical border
    screen.move(screen.width / 2, 0)
    screen.draw(screen.width / 2, screen.height / 2, thin=thin, colour=COLOUR_PRIMARY)

    printTitle(screen)

def printInteract(screen: Screen, message: str, line: int):
    start_w = 2
    start_h = int(screen.height / 2) + 1 + line
    screen.print_at(message, start_w, start_h, COLOUR_PRIMARY)


class MainView(Frame):

    start_options = {
        "c": ("c: Connect to device", 0),
        "p": ("p: Set port", 1),
        "b": ("b: Set Baud (default=9600)", 2),
        "q": ("q: Quit", 3),
    }

    main_options = {
        "a": ("a: Flash Application file", 0),
        "e": ("e: Erase Device Flash", 1),
        "o": ("o: Inspect Option Bytes", 2)
    }

    input_modes = [
        "port",
        "baud",
        "optbyte",
    ]

    frame_palette = {
        "background": (Screen.COLOUR_WHITE, Screen.A_NORMAL, Screen.COLOUR_BLUE),
        "shadow": (Screen.COLOUR_BLACK, None, Screen.COLOUR_BLACK),
        "disabled": (Screen.COLOUR_BLACK, Screen.A_BOLD, Screen.COLOUR_BLUE),
        "invalid": (Screen.COLOUR_YELLOW, Screen.A_BOLD, Screen.COLOUR_RED),
        "label": (Screen.COLOUR_GREEN, Screen.A_BOLD, Screen.COLOUR_BLUE),
        "borders": (Screen.COLOUR_BLACK, Screen.A_BOLD, Screen.COLOUR_BLUE),
        "scroll": (Screen.COLOUR_CYAN, Screen.A_NORMAL, Screen.COLOUR_BLUE),
        "title": (Screen.COLOUR_WHITE, Screen.A_BOLD, Screen.COLOUR_BLUE),
        "edit_text": (Screen.COLOUR_WHITE, Screen.A_NORMAL, Screen.COLOUR_BLUE),
        "focus_edit_text": (Screen.COLOUR_WHITE, Screen.A_BOLD, Screen.COLOUR_CYAN),
        "readonly": (Screen.COLOUR_BLACK, Screen.A_BOLD, Screen.COLOUR_BLUE),
        "focus_readonly": (Screen.COLOUR_BLACK, Screen.A_BOLD, Screen.COLOUR_CYAN),
        "button": (Screen.COLOUR_WHITE, Screen.A_NORMAL, Screen.COLOUR_BLUE),
        "focus_button": (Screen.COLOUR_WHITE, Screen.A_BOLD, Screen.COLOUR_CYAN),
        "control": (Screen.COLOUR_YELLOW, Screen.A_NORMAL, Screen.COLOUR_BLUE),
        "selected_control": (Screen.COLOUR_YELLOW, Screen.A_BOLD, Screen.COLOUR_BLUE),
        "focus_control": (Screen.COLOUR_YELLOW, Screen.A_NORMAL, Screen.COLOUR_BLUE),
        "selected_focus_control": (Screen.COLOUR_YELLOW, Screen.A_BOLD, Screen.COLOUR_CYAN),
        "field": (Screen.COLOUR_WHITE, Screen.A_NORMAL, Screen.COLOUR_BLUE),
        "selected_field": (Screen.COLOUR_YELLOW, Screen.A_BOLD, Screen.COLOUR_BLUE),
        "focus_field": (Screen.COLOUR_WHITE, Screen.A_NORMAL, Screen.COLOUR_BLUE),
        "selected_focus_field": (Screen.COLOUR_WHITE, Screen.A_BOLD, Screen.COLOUR_CYAN),
    }

    def __init__(self, screen, model, primary_col=Screen.COLOUR_RED, secondary_col=Screen.COLOUR_BLACK):
        super(MainView, self).__init__(screen,
            screen.height,
            screen.width,
            on_load=self._reloadInfo,
            title="Main",
            has_border=True
        )

        self.device = model
        self.update_palette(primary_col, secondary_col)

        top_layout = Layout([1, 1, 1], fill_frame=True)
        mid_layout = Layout([1])
        input_layout = Layout([1])
        div_a = Layout([1])
        message_layout = Layout([1])
        div_b = Layout([1])
        div_c = Layout([1])
        footer = Layout([3])
        self.mode = 0

        self.add_layout(top_layout)
        self.add_layout(mid_layout)
        self.add_layout(div_a)
        self.add_layout(message_layout)
        self.add_layout(div_b)
        self.add_layout(input_layout)
        self.add_layout(div_c)
        self.add_layout(footer)

        self.messages = []
        top_layout.add_widget(Label(TOOLNAME), 0)
        top_layout.add_widget(TextBox(6, name="Info", disabled=True), 1)
        top_layout.add_widget(ListBox(6, self.device.getDetails() if self.device.getConnected() else [("No Device Connected", 0)], label="Details"), 2)
        mid_layout.add_widget(ListBox(6, self.menuOptions(), label="Menu"), 0)
        div_a.add_widget(Divider())
        message_layout.add_widget(ListBox(2, self.messages, name="messages"))
        div_b.add_widget(Divider())
        input_layout.add_widget(TextBox(2, label=">>>", name="input", on_change=self.handle_input), 0)
        div_c.add_widget(Divider())
        footer.add_widget(Text(label=f"STM Tool v{TOOL_VERSION}", readonly=True), 0)
        self.fix()

    def handle_input(self):
        self.save()
        print(self.data['input'])
        if self.data['input'][-1] == '':
            data = self.data['input'][0]
            if self.mode == 0 and data in self.start_options.keys():
                 if data == 'p':
                     pass
        

    def menuOptions(self):
        if self.mode == 0:
            # start mode options
            return [self.start_options[opt] for opt in self.start_options]
        elif self.mode == 1:
            # connected options
            return [self.main_options[opt] for opt in self.main_options]
        elif self.mode == 2:
            # option bytes options
            return (0,0,0)
        else:
            return (0,0,0)

    def update_palette(self, col_a, col_b): 
        updated = {field: (col_a, Screen.A_NORMAL, col_b) for field in self.frame_palette.keys()}
        self.palette = updated 

    def _reloadInfo(self):
        pass

class OptByteView(Frame):

    def __init__(self, screen, model):
        super(OptByteView, self).__init__(screen,
            screen.height,
            screen.width,
            on_load=self._reloadInfo,
            title="OptBytes"
        )

class StmProxy(object):

    def __init__(self):
        self.stm = STMInterface()

    def connect(self, port, baud):
        try:
            self.stm.connectToDevice(port, baud=baud)
            self.getDeviceInfo()
        except Exception as e:
            return e.message

    def getDeviceInfo(self):
        success = self.stm.readDeviceInfo()
        if not success:
            return "Error reading device info"
        success = self.stm.readOptionBytes()
        if not success:
            return "Error reading opt bytes"

    def getConnected(self):
        return self.stm.connected

    def getDetails(self):
        details = {
            "Device Type": self.stm.device.name,
            "Flash Memory": self.stm.device.flash_memory.size,
            "Pages": self.stm.device.flash_page_num,
            "Page Size": self.stm.device.flash_page_size,
        }
        dstring = ""
        for i, key in enumerate(details):
            dstring += f"{key}: {details[key]}\n"
        return dstring

def demo(screen):
    # effects = [
    #     Cycle(
    #         screen,
    #         FigletText("ASCIIMATICS", font='big'),
    #         screen.height // 2 - 8),
    #     Cycle(
    #         screen,
    #         FigletText("ROCKS!", font='big'),
    #         screen.height // 2 + 3),
    #     Stars(screen, (screen.width + screen.height) // 2)
    # ]
    # screen.play([Scene(effects, 500)])

    # drawBorders(screen, thin=True)
    # printInteract(screen, "Menu", 0)
    
    # if not stm.connected:
    #     printInteract(screen, "Connect To Device", 0)

    stm = StmProxy()
    # screen.play(frame)
    # sleep(10)
    # frame = Frame(screen, 80, 20, has_border=False)
    # layout = Layout([1, 1, 1, 1])
    # frame.add_layout(layout)
    screen.play([Scene([MainView(screen, stm)])])

Screen.wrapper(demo)