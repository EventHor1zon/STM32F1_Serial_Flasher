CHIP_IMG = """
              █ █ █ █ █ █
            ▄             ▄
            ▄             ▄
            ▄             ▄
            ▄             ▄
            ▄             ▄
            ▄             ▄
              █ █ █ █ █ █
"""


def generateImage(dev_type: str, density: str):
    r = CHIP_IMG.split("\n")
    ## format the name row
    if len(dev_type) > 13:
        dev_type = dev_type[:13]
    spaces = 13 - len(dev_type)
    new = (
        (" " * 12)
        + ("▄")
        + (" " * int(spaces / 2))
        + dev_type
        + (" " * (int(spaces / 2) + 1 if spaces % 2 == 1 else int(spaces / 2)))
        + ("▄")
    )
    r[4] = new
    ## format the density row
    if len(density) > 13:
        density = density[:13]

    spaces = 13 - len(density)
    dens = (
        (" " * 12)
        + ("▄")
        + (" " * int(spaces / 2))
        + density
        + (" " * (int(spaces / 2) + 1 if spaces % 2 == 1 else int(spaces / 2)))
        + ("▄")
    )

    r[5] = dens

    return "\n".join(r)
