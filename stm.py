from SerialFlasher.devices import OptionBytes
from SerialFlasher.StmDevice import STMInterface
from time import sleep

data = b'\xa5Z\xff\x00\x00\xff\x00\xff\xff\x00\xff\x00\xff\x00\xff\x00'

def main():
    st = STMInterface()
    st.connectToDevice('/dev/ttyUSB0', 9600)

    success = st.readDeviceInfo()

    print(f"s: {success}")

    success = st.readOptionBytes()

    if success:
        op = st.device.opt_bytes
        print(f"data = {op.rawBytes}")
        print(f"{'Hardware' if op.watchdogType == 0 else 'Software'} Watchdog")
        
        print(f"ReadProtect: {hex(op.readProtect)}")
        print(f"WriteProtect: {hex(op.write_protect_0)} {hex(op.write_protect_1)}")
        print(f"WriteProtect: {hex(op.write_protect_2)} {hex(op.write_protect_3)}")
        print(f"Data 0: {hex(op.data_byte_0)} Data 1: {hex(op.dataByte1)}")
    else:
        print("error")


    if success:
        op.dataByte0 = 0xAA
        raw = op.toBytes()
        print(f"Writing {raw} to option bytes")
        success = st.writeToOptionBytes(raw, reconnect=True)

        if not success:
            print("Write failed")
        else:
            print("Write succeeded")

    success = st.readDeviceInfo()

    print(f"s1: {success}")

    success = st.readOptionBytes()

    if success:
        op = st.device.opt_bytes
        print(f"data = {op.rawBytes}")
        print(f"{'Hardware' if op.watchdogType == 0 else 'Software'} Watchdog")
        
        print(f"ReadProtect: {hex(op.readProtect)}")
        print(f"WriteProtect: {hex(op.write_protect_0)} {hex(op.write_protect_1)}")
        print(f"WriteProtect: {hex(op.write_protect_2)} {hex(op.write_protect_3)}")
        print(f"Data 0: {hex(op.data_byte_0)} Data 1: {hex(op.dataByte1)}")
    else:
        print("error")


    # sleep(1)

    # success = st.serialTool.reconnect()

    # if not success:
    #     print("didn't reconnect")
    # else:
    #     st.readOptionBytes()

    #     new = st.device.opt_bytes

    #     print(f"new {new}")
    

if __name__ == "__main__":
    main()