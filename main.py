from serial import Serial, SerialTimeoutException, SerialException, PARITY_EVEN
from SerialFlasher.SerialFlasher import SerialTool
from struct import unpack


def main():
    pass


if __name__ == "__main__":
    fmt = ">H"
    serial = Serial(
        "/dev/ttyUSB0",
        57600,
        timeout=1.0,
        write_timeout=1.0,
    )
    serial.setDTR(False)
    sf = SerialTool(
        serial=serial
    )
    sf.connect()
    success, rx = sf.cmdGetId()

    if success:
        print(f"Success! CmdId {[hex(b) for b in rx]} {rx}")
    else:
        print("Activity failed")

    success, rx = sf.cmdGetInfo()

    if success:
        print(f"Success! CmdGet {[hex(b) for b in rx]}")
    else:
        print("Activity failed")


    success, rx = sf.cmdGetVersionProt()

    if success:
        print(f"Success! CmdVersionProtect {[hex(b) for b in rx]} {rx}")
    else:
        print("Activity failed")
    # success, rx = sf.cmdReadFromMemoryAddress(0x1FFFF7E0, 2)
    # d = unpack(fmt, rx)
    success, rx = sf.cmdReadFromMemoryAddress(0x1FFFF7E8, 24)
    print(f"State: {success} Data: {rx}")

    sf.reset()

    