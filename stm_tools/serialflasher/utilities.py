from struct import unpack


def unpack16BitInt(value: bytearray) -> int:
    id_fmt = ">H"
    return unpack(id_fmt, value)[0]

def getByteComplement(byte):
    return byte ^ 0xFF

def clearBit(byte, bit):
    return (byte & getByteComplement((1 << bit)))

def setBit(byte, bit):
    return (byte | (1 << bit))

