from SerialFlasher.StmDevice import STMInterface
from time import sleep

data = b'\xa5Z\xff\x00\x00\xff\x00\xff\xff\x00\xff\x00\xff\x00\xff\x00'

def main():
    st = STMInterface()
    st.connectToDevice('/dev/ttyUSB0', 9600)

    success = st.readDeviceInfo()

    print(f"s: {success}")

    success = st.readOptionBytes()

    if success == True:
        print(f"data = {st.device.option_bytes_contents}")
    else:
        print("error")

    copy = st.device.option_bytes_contents

    print(copy)

    success = st.writeToOptionBytes(data)

    if not success:
        print("Option byte write error")
    else:
        print("Opt byte write success")


    sleep(1)

    success = st.serialTool.reconnect()

    if not success:
        print("didn't reconnect")
    else:
        st.readOptionBytes()

        new = st.device.option_bytes_contents

        print(f"new {new}")
    

if __name__ == "__main__":
    main()