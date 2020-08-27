from SerialFlasher import SerialTool
from rich.console import Console
import sys


def banner(c):
    c.print(
        "[bold green]/_____/_____/_____/_____/_____/_____/_____/_____/_____/_____/_____/_____/_____/_____/_____/_____/[/bold green]"
    )
    c.print(
        "[bold red]  / ___/_  __/  |/ [/bold red][bold yellow] /__  /__ \\ [/bold yellow]   / ___/___  _____(_)___ _/ / ____/ /___ ______/ /_  ___  _____  "
    )
    c.print(
        "[bold red]  \\__ \\ / / / /|_[/bold red][bold yellow]/ / /_ <__/ /[/bold yellow]    \\__ \\/ _ \\/ ___/ / __ `/ / /_  / / __ `/ ___/ __ \\/ _ \\/ ___/  "
    )
    c.print(
        "[bold red] ___/ // / / /  / /[/bold red][bold yellow]___/ / __/[/bold yellow]    ___/ /  __/ /  / / /_/ / / __/ / / /_/ (__  ) / / /  __/ /      "
    )
    c.print(
        "[bold red]/____//_/ /_/  /_//[/bold red][bold yellow]____/____/[/bold yellow]   /____/\\___/_/  /_/\\__,_/_/_/   /_/\\__,_/____/_/ /_/\\___/_/    "
    )
    c.print(
        "[bold green] __________________________________________________________________________________________ [/bold green]     "
    )
    c.print(
        "[bold green]/_____/_____/_____/_____/_____/_____/_____/_____/_____/_____/_____/_____/_____/_____/_____/[/bold green]"
    )


def display_read_menu(c):
    pass


def display_del_menu(c):
    pass


def display_write_menu(c):
    pass


def menu(c):
    c.print(
        "[bold]Welcome to the STM32 SerialFlasher Software!\r\nPlease Pick an option:[/bold]"
    )
    c.print("[bold green]1[/bold green]: Read from STM32 Flash")
    c.print("[bold green]2[/bold green]: Delete STM32 Flash")
    c.print("[bold green]3[/bold green]: Write to STM32 Flash")
    c.print("[bold][[red]q[/red]] quit [[blue]v[/blue]] verbosity[/bold]")

    select = input(">>>:")

    if select == "q":
        sys.exit(0)
    elif select == "v":
        pass
    elif select == "1":
        display_read_menu(c)
    elif select == "2":
        display_del_menu(c)
    elif select == "3":
        display_write_menu(c)
    else:
        c.print("[red]Error[/red]: Invalid selection")


def main():

    console = Console()
    console.print("[bold red]Hello[/bold red] world\n")

    banner(console)
    menu(console)


if __name__ == "__main__":
    main()
