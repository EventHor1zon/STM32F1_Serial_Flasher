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
    success, rx = sf.cmdReadFromMemoryAddress(0x1FFFF7E0, 2)
    d = unpack(fmt, rx)
    print(f"State: {success} Data: {rx} d {d}")

    sf.reset()

    