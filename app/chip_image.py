import sys

sys.path.append("../SerialFlasher")
print(f"{sys.path}")
from StmDevice import STMInterface

from rich.text import Text

CHIP_IMG_OFFSET = 12
CHIP_VALUE_WIDTH = 13

CHIP_IMG = f"""
{" "*CHIP_IMG_OFFSET}  █ █ █ █ █ █
{" "*CHIP_IMG_OFFSET}▄             ▄
{" "*CHIP_IMG_OFFSET}▄             ▄
{" "*CHIP_IMG_OFFSET}▄             ▄
{" "*CHIP_IMG_OFFSET}▄             ▄
{" "*CHIP_IMG_OFFSET}▄             ▄
{" "*CHIP_IMG_OFFSET}▄             ▄
{" "*CHIP_IMG_OFFSET}  █ █ █ █ █ █
"""


FLASH_IMAGE = """
▄ ▄ ▄ ▄ ▄ ▄ ▄ ▄
▄ ▄ ▄ ▄ ▄ ▄ ▄ ▄
▄ ▄ ▄ ▄ ▄ ▄ ▄ ▄
▄ ▄ ▄ ▄ ▄ ▄ ▄ ▄
▄ ▄ ▄ ▄ ▄ ▄ ▄ ▄
▄ ▄ ▄ ▄ ▄ ▄ ▄ ▄
▄ ▄ ▄ ▄ ▄ ▄ ▄ ▄
▄ ▄ ▄ ▄ ▄ ▄ ▄ ▄
"""


def generateChipImage(dev_type: str, density: str):
    r = CHIP_IMG.split("\n")
    ## format the name row
    if len(dev_type) > CHIP_VALUE_WIDTH:
        dev_type = dev_type[:CHIP_VALUE_WIDTH]
    spaces = CHIP_VALUE_WIDTH - len(dev_type)
    name = (
        (" " * CHIP_IMG_OFFSET)
        + ("▄")
        + (" " * int(spaces / 2))
        + dev_type
        + (" " * (int(spaces / 2) + 1 if spaces % 2 == 1 else int(spaces / 2)))
        + ("▄")
    )
    r[4] = name
    ## format the density row
    if len(density) > 13:
        density = density[:13]

    spaces = CHIP_VALUE_WIDTH - len(density)
    dens = (
        (" " * CHIP_IMG_OFFSET)
        + ("▄")
        + (" " * int(spaces / 2))
        + density
        + (" " * (int(spaces / 2) + 1 if spaces % 2 == 1 else int(spaces / 2)))
        + ("▄")
    )

    r[5] = dens

    return "\n".join(r)


def get_device_name_short(dev: STMInterface):
    return dev.device.name.split("xxx")[0] + "xxx"


def get_device_dens_string(dev: STMInterface):
    density = dev.device.name.split("xxx")[1].split("Density")
    return density[0] + ("VAL" if len(density) > 1 and len(density[1]) > 1 else "")
