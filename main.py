from time import sleep
from serial import Serial, SerialTimeoutException, SerialException, PARITY_EVEN
from SerialFlasher.SerialFlasher import SerialTool
from SerialFlasher.devices import OptionBytes
from struct import unpack
import sys


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
    sf = SerialTool(serial=serial)
    sf.connect()
    success, rx = sf.cmdGetId()

    # if success:
    #     d = unpack(fmt, rx)
    #     print(f"Success! CmdId {[hex(b) for b in rx]} {rx} {d[0]}")
    # else:
    #     print("Activity failed")

    success, rx = sf.cmdGetInfo()

    if success:
        print(f"Success! CmdGet {[hex(b) for b in rx]}")
    else:
        print("Activity failed")

    # success = sf.cmdReadoutUnprotect()

    # if success:
    #     print("Success! Readout should now be allowed. Device will reset.")
    # else:
    #     print("Failed to cmd Read Unprotect")
    #     sys.exit(0)

    # sleep(2)
    # print("Reconnecting...")

    # sf.connect()

    success = sf.cmdWriteUnprotect()

    if success:
        print("Success! Write should now be allowed. Device will reset.")
    else:
        print("Failed to cmd Write Unprotect")
        sys.exit(0)

    sleep(2)
    print("Reconnecting...")

    sf.connect()

    # success, rx = sf.cmdGetVersionProt()

    # if success:
    #     print(f"Success! CmdVersionProtect {[hex(b) for b in rx]} {rx}")
    # else:
    #     print("Activity failed")

    success, rx = sf.cmdReadFromMemoryAddress(0x1FFFF800, 16)
    print(f"State {success}, rx {rx} {len(rx)}")

    opts = OptionBytes.FromBytes(rx)

    opts.dumpOptionBytes()

    # fmt = ">16B"

    # (
    #     nUsr,
    #     Usr,
    #     nRdp,
    #     Rdp,
    #     nD1,
    #     D1,
    #     nD0,
    #     D0,
    #     nWrp1,
    #     Wrp1,
    #     nWrp0,
    #     Wrp0,
    #     nWrp3,
    #     Wrp3,
    #     nWrp2,
    #     Wrp2,
    # ) = unpack(fmt, rx)

    # print(f"{bin(Usr)}|{bin(nUsr)} - {Rdp}|{nRdp}")
    # print(f"{D1}|{nD1} - {D0}|{nD0}")
    # print(f"{Wrp1}|{nWrp1} - {Wrp0}|{nWrp0}")
    # print(f"{Wrp3}|{nWrp3} - {Wrp2}|{nWrp2}")

    """
    90|165 - 0|255
    0|255  - 0|255
    0|255  - 0|255
    0|255  - 0|255

    """

    # success, rx = sf.cmdReadFromMemoryAddress(0x1FFFF7E0, 2)
    # d = unpack(fmt, rx)
    # print(f"State: {success} Data {d}")

    # success = sf.cmdWriteToMemoryAddress(
    #     0x08000000, bytearray([0x01, 0x02, 0x03, 0x04])
    # )

    # print(f"Write to flash memory: {success}")

    # success, rx = sf.cmdReadFromMemoryAddress(0x08000000, 4)
    # print(f"State: {success} Data: {rx}")

    # success = sf.cmdWriteToMemoryAddress(
    #     0x08000400, bytearray([0x41, 0x42, 0x43, 0x44])
    # )

    # print(f"2nd Write to flash memory: {success}")

    # success, rx = sf.cmdReadFromMemoryAddress(0x08004000, 4)
    # print(f"State: {success} Data: {rx}")

    # success = sf.cmdEraseFlashMemoryPages(bytearray([0, 1, 2]))
    # print(f"State: {success}")

    # sleep(3)

    # success, rx = sf.cmdReadFromMemoryAddress(0x08000000, 4)
    # print(f"State: {success} Data: {rx}")

    # success, rx = sf.cmdReadFromMemoryAddress(0x08004000, 4)
    # print(f"State: {success} Data: {rx}")

    # success = sf.cmdReadoutUnprotect()

    # sleep(1)
    # print("Reconnecting")
    # success = sf.connect()
    # if not success:
    #     print("unable to reconnect")

    # success, rx = sf.cmdReadFromMemoryAddress(0x1FFFF800, 16)
    # print(f"State {success}, rx {rx}")

    # fmt = ">16B"

    # nUsr, Usr, nRdp, Rdp, nD1, D1, nD0, D0, nWrp1, Wrp1, nWrp0, Wrp0, nWrp3, Wrp3, nWrp2, Wrp2 = unpack(fmt, rx)

    # print(f"{bin(Usr)}|{bin(nUsr)} - {Rdp}|{nRdp}")
    # print(f"{D1}|{nD1} - {D0}|{nD0}")
    # print(f"{Wrp1}|{nWrp1} - {Wrp0}|{nWrp0}")
    # print(f"{Wrp3}|{nWrp3} - {Wrp2}|{nWrp2}")

    sf.reset()
