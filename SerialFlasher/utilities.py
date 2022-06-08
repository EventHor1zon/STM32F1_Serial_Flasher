from struct import unpack


def unpack16BitInt(value: bytearray) -> int:
    id_fmt = ">H"
    return unpack(id_fmt, value)[0]

