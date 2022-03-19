


class ValidAddressResponse(Enum):
    STM_ADDRESS_VALID = 1
    STM_ADDRESS_INVALID_SECTION = 2
    STM_ADDRESS_INVALID_LENGTH = 3
    STM_ADDRESS_INVALID_ACCESS = 4


class DeviceMemoryMap:

    BOOTLOADER_START = 0x20000000
    BOOTLOADER_LEN = 2048

    register_map = {
        "FSMC": [0xA0000000, 0xA0000FFF],
        "USB OTG FS ": [0x50000000, 0x5003FFFF],
        "Reserved": [0x40030000, 0x4FFFFFFF],
        "Ethernet": [0x40028000, 0x40029FFF],
        "Reserved": [0x40023400, 0x40027FFF],
        "CRC Section": [0x40023000, 0x400233FF],
        "Flash memory interface": [0x40022000, 0x400223FF],
        "Reserved": [0x40021400, 0x40021FFF],
        "Reset and clock control RCC": [0x40021000, 0x400213FF],
        "Reserved": [0x40020800, 0x40020FFF],
        "DMA2": [0x40020400, 0x400207FF],
        "DMA1": [0x40020000, 0x400203FF],
        "Reserved ": [0x40018400, 0x4001FFFF],
        "SDIO": [0x40018000, 0x400183FF],
        "Reserved": [0x40015800, 0x40017FFF],
        "TIM11 timer": [0x40015400, 0x400157FF],
        "TIM10 timer": [0x40015000, 0x400153FF],
        "TIM9 timer ": [0x40014C00, 0x40014FFF],
        "Reserved": [0x40014000, 0x40014BFF],
        "ADC3": [0x40013C00, 0x40013FFF],
        "USART1": [0x40013800, 0x40013BFF],
        "TIM8 timer": [0x40013400, 0x400137FF],
        "SPI1": [0x40013000, 0x400133FF],
        "TIM1 timer": [0x40012C00, 0x40012FFF],
        "ADC2": [0x40012800, 0x40012BFF],
        "ADC1": [0x40012400, 0x400127FF],
        "GPIO Port G": [0x40012000, 0x400123FF],
        "GPIO Port F": [0x40011C00, 0x40011FFF],
        "GPIO Port E": [0x40011800, 0x40011BFF],
        "GPIO Port D": [0x40011400, 0x400117FF],
        "GPIO Port C": [0x40011000, 0x400113FF],
        "GPIO Port B": [0x40010C00, 0x40010FFF],
        "GPIO Port A": [0x40010800, 0x40010BFF],
        "EXTI": [0x40010400, 0x400107FF],
        "AFIO": [0x40010000, 0x400103FF],
        "Reserved": [0x40007800, 0x4000FFFF],
        "DAC": [0x40007400, 0x400077FF],
        "Power control PWR": [0x40007000, 0x400073FF],
        "Backup registers": [0x40006C00, 0x40006FFF],
        "bxCAN1": [0x40006400, 0x400067FF],
        "bxCAN2": [0x40006800, 0x40006BFF],
        "Shared USB/CAN SRAM": [0x40006000, 0x400063FF],
        "USB device FS registers": [0x40005C00, 0x40005FFF],
        "I2C2": [0x40005800, 0x40005BFF],
        "I2C1": [0x40005400, 0x400057FF],
        "UART5": [0x40005000, 0x400053FF],
        "UART4": [0x40004C00, 0x40004FFF],
        "USART3": [0x40004800, 0x40004BFF],
        "USART2": [0x40004400, 0x400047FF],
        "Reserved": [0x40004000, 0x400043FF],
        "SPI3/I2S": [0x40003C00, 0x40003FFF],
        "SPI2/I2S": [0x40003800, 0x40003BFF],
        "Reserved": [0x40003400, 0x400037FF],
        "Independent watchdog": [0x40003000, 0x400033FF],
        "Window watchdog": [0x40002C00, 0x40002FFF],
        "RTC": [0x40002800, 0x40002BFF],
        "Reserved": [0x40002400, 0x400027FF],
        "TIM14 timer": [0x40002000, 0x400023FF],
        "TIM13 timer": [0x40001C00, 0x40001FFF],
        "TIM12 timer": [0x40001800, 0x40001BFF],
        "TIM7 timer": [0x40001400, 0x400017FF],
        "TIM6 timer": [0x40001000, 0x400013FF],
        "TIM5 timer": [0x40000C00, 0x40000FFF],
        "TIM4 timer": [0x40000800, 0x40000BFF],
        "TIM3 timer": [0x40000400, 0x400007FF],
        "TIM2 timer": [0x40000000, 0x400003FF],
    }

    flash_interface_registers = {
        "MainMemoryStart": {"address": 0x0800000, 'length': 2000},
        "Sytem Memory": {'address': 0x1FFFF000, 'length': 2000 }, ## variable length depending on device type
        "OptionBytes": {'address': 0x1FFFF800, 'length': 16 },
        "FLASH_ACR": {"address": 0x40022000, "length": 4,},
        "FLASH_KEYR": {"address": 0x40022004, "length": 4,},
        "FLASH_OPTKEYR": {"address": 0x40022008, "length": 4,},
        "FLASH_SR": {"address": 0x4002200C, "length": 4,},      ## status refister
        "FLASH_CR": {"address": 0x40022010, "length": 4,},      ## control register
        "FLASH_AR": {"address": 0x40022014, "length": 4,},      ## address register
        "FLASH_OBR": {"address": 0x4002201C, "length": 4,},     ## option byte register
        "FLASH_WRPR": {"address": 0x40022020, "length": 4,},    ## write protect register
    }

    flash_keys = {
        'RDPRT_KEY' : 0x00A5,
        'KEY_1': 0x45670123,
        'KEY_2': 0xCDEF89AB,
    }

    STMF1_SRAM_START = 0x20000000
    STMF1_FLASH_SIZE = 0x1FFFF7E0





class DeviceObject:
    """ The device object should:
        - describe the connected device
        - keep track of the device information retrieved
        - provide higher level interface to the device
        - allow reading/writing of specific sections
        - translate device areas into specific memory addresses
    """

    def __init__(
        self, bl_version: int = None, valid_cmds: list = None, dev_id: int = None
    ):
        self.bootloader_version = bl_version
        self.valid_cmds = valid_cmds
        self.device_id = dev_id

    def updateFromGETrsp(self, data: bytearray):
        self.bootloader_version = data[2]
        self.valid_cmds = data[3:13]

    def updateFromIDrsp(self, data: bytearray):
        pid_msb = data[2]
        pid_lsb = data[3]
        self.device_id = (pid_msb << 8) | pid_lsb

    def getBootloaderVersion(self):
        return self.bootloader_version

    def getValidCommands(self):
        return self.valid_cmds

    def getDeviceId(self):
        return self.device_id

    def unpackDeviceInfo(self, get_rx: bytearray, id_rx: bytearray):
        """
            # TODO - delete & redo
            populate device information from a 'GET' command response 
            and ID commands response
            bytes: 0 - ACK
                    1 - N (11)
                    2 - BL Vers (0 - 255)
                    3 - cmd (0)
                    4 - cmd (1)
                    ...
                    -1 - ACK
        """
        success = False

        ## check acks in both packets
        if get_rx[0] != STM_CMD_ACK:
            print("Invalid Device info byte 1")
        elif get_rx[-1] != STM_CMD_ACK:
            print("Invalid device info byte 15")
        elif id_rx[0] != STM_CMD_ACK:
            print("Invalid device id byte 0")
        elif id_rx[4] != STM_CMD_ACK:
            print("Invalid device id byte 4")
        else:
            ## unpack values 
            bl_v = get_rx[1]
            v_cmds = list(get_rx[3:14])
            d_id = (id_rx[2] << 8) | id_rx[3]

            success = True
        return success

    def getDeviceBootloaderVersion(self):
        if self.device_info == None or self.bootloader_read == False:
            raise InformationNotRetrieved("Bootloader version not read yet")
        else:
            return self.device_info.bootloader_version

    def getDeviceValidCommands(self):
        if self.device_info == None or self.valid_cmds_read == False:
            raise InformationNotRetrieved("Valid commands have not been read yet")
        else:
            return self.device_info.valid_cmds

    def getDeviceId(self):
        if self.device_info == None or self.device_id_read == False:
            raise InformationNotRetrieved("Device ID has not been read yet")
        else:
            return self.device_info.device_id


    def readDeviceInfo(self):
        """
            read the device information using the
            GET and GET_ID commands
        """

        success, get_rx = self.cmdGetInfo()
        if success:
            success, id_rx = self.cmdGetId()

        if success:
            success = self.unpackDeviceInfo(get_rx, id_rx)

        return success

    def readOptionBytes(self):
        pass
