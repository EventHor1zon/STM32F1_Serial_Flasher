from serial import Serial, SerialTimeoutException, SerialException, PARITY_EVEN
from SerialFlasher.SerialFlasher import SerialTool

def main():
    pass


if __name__ == "__main__":
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
    success, rx = sf.cmdReadFromMemoryAddress(0x1FFFF800, 4)
    print(f"State: {success} Data: {rx}")
    sf.reset()

    