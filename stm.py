from SerialFlasher.StmDevice import STMInterface




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

if __name__ == "__main__":
    main()