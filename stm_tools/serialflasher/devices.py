from dataclasses import dataclass
from struct import unpack, pack
from enum import Enum
from dataclasses import dataclass
from collections import namedtuple
from .errors import DeviceNotSupportedError
from .utilities import getByteComplement, setBit, clearBit

#! FlashOptionBytes: named tuple used for unpacking
#  optionbytes register contents
FlashOptionBytes = namedtuple(
    "FlashOptionBytes",
    [
        "readProt",
        "nReadProt",
        "user",
        "nUser",
        "data0",
        "nData0",
        "data1",
        "nData1",
        "writeProt0",
        "nWriteProt0",
        "writeProt1",
        "nWriteProt1",
        "writeProt2",
        "nWriteProt2",
        "writeProt3",
        "nWriteProt3",
    ],
)


@dataclass
class Register:
    name: str
    start: int
    size: int


@dataclass
class Peripheral:
    """describes a peripheral on the device"""

    name: str
    start: int
    end: int

    @property
    def size(self) -> int:
        return self.end - self.start


@dataclass
class PeripheralRegister:
    """describes a Peripheral register
    Offset from peripheral start address
    and value at reset
    """

    peripheral: Peripheral
    offset: int
    reset: int


@dataclass
class Region:
    """describes a region of memory space on the device"""

    name: str
    start: int
    end: int

    @property
    def size(self):
        return self.end - self.start

    def is_valid(self, address: int):
        """return True if address is in range start -> end"""
        return address >= self.start and address < self.end


class DeviceDensity(Enum):
    DEVICE_TYPE_UNKNOWN = 0
    DEVICE_TYPE_LOW_DENSITY = 1
    DEVICE_TYPE_MEDIUM_DENSITY = 2
    DEVICE_TYPE_HIGH_DENSITY = 3
    DEVICE_TYPE_XL_DENSITY = 4


class OptionBytes:
    """!
    enough messing about with tuples
    make a proper class with functionality
    and stuff. This might have got out of control.
    But it's almost worth it if only for the practice
    """

    user: int = 0x00
    read_protect: int = 0x00
    watchdog_type: int = 0
    reset_on_stop: int = 0
    reset_on_standby: int = 1
    data_byte_0: int = 0x00
    data_byte_1: int = 0x00
    raw_bytes: bytearray = bytearray([])
    write_protect_0: int = 0x00
    write_protect_1: int = 0x00
    write_protect_2: int = 0x00
    write_protect_3: int = 0x00

    def __init__(self):
        pass

    @classmethod
    def FromAttributes(
        cls,
        read_protect: int = 0x00,
        watchdog_type: int = 0,
        reset_on_stop: int = 1,
        reset_on_standby: int = 0,
        data_byte_0: int = 0x00,
        data_byte_1: int = 0x00,
        write_protect_0: int = 0x00,
        write_protect_1: int = 0x00,
        write_protect_2: int = 0x00,
        write_protect_3: int = 0x00,
    ):
        self = OptionBytes()
        self.read_protect = read_protect
        self.watchdog_type = watchdog_type
        self.reset_on_stop = reset_on_stop
        self.reset_on_standby = reset_on_standby
        self.user = self.generateUserByte()
        self.data_byte_0 = data_byte_0
        self.data_byte_1 = data_byte_1
        self.write_protect_0 = write_protect_0
        self.write_protect_1 = write_protect_1
        self.write_protect_2 = write_protect_2
        self.write_protect_3 = write_protect_3
        self.raw_bytes = self.toBytes()
        return self

    @classmethod
    def FromBytes(cls, data: bytearray):
        """! Create an OptionBytes object from a bytearray of data
        @param data the bytearray - must be 16 bytes long. Will raise
                    unpack error if data is badly formatted
        """
        self = OptionBytes()
        fob = FlashOptionBytes._make(unpack(">16B", data))
        self.read_protect = fob.readProt
        self.watchdog_type = fob.user & 0b1
        self.reset_on_stop = 0 if ((fob.user >> 1) & 0b1) else 1
        self.reset_on_standby = 0 if ((fob.user >> 2) & 0b1) else 1
        self.user = fob.user
        self.data_byte_0 = fob.data0
        self.data_byte_1 = fob.data1
        self.write_protect_0 = fob.writeProt0
        self.write_protect_1 = fob.writeProt1
        self.write_protect_2 = fob.writeProt2
        self.write_protect_3 = fob.writeProt3
        self.raw_bytes = data
        return self

    def generateUserByte(self):
        userbyte = 0x00
        userbyte = (
            setBit(userbyte, 0) if self.watchdog_type > 0 else clearBit(userbyte, 0)
        )
        userbyte = (
            setBit(userbyte, 1) if not self.reset_on_stop > 0 else clearBit(userbyte, 1)
        )
        userbyte = (
            setBit(userbyte, 2)
            if not self.reset_on_standby > 0
            else clearBit(userbyte, 2)
        )
        return userbyte

    def toBytes(self):
        self.user = self.generateUserByte()

        fob = FlashOptionBytes(
            self.read_protect,
            getByteComplement(self.read_protect),
            self.user,
            getByteComplement(self.user),
            self.data_byte_0,
            getByteComplement(self.data_byte_0),
            self.data_byte_1,
            getByteComplement(self.data_byte_1),
            self.write_protect_0,
            getByteComplement(self.write_protect_0),
            self.write_protect_1,
            getByteComplement(self.write_protect_1),
            self.write_protect_2,
            getByteComplement(self.write_protect_2),
            self.write_protect_3,
            getByteComplement(self.write_protect_3),
        )

        raw = pack(">16B", *[ob for ob in fob])
        return raw

    def updateRawBytes(self):
        self.raw_bytes = self.toBytes()

    @property
    def rawBytes(self) -> bytearray:
        return self.raw_bytes

    @property
    def watchdogType(self):
        """! get watchdog type from option bytes"""
        return self.watchdog_type

    @watchdogType.setter
    def watchdogType(self, watchdog_type: bool):
        """! setter for the watchdog type
        update the user byte too
        @param type - False - Hardware Watchdog
                      True - Software watchdog
        """
        self.watchdog_type = int(watchdog_type)
        self.updateRawBytes()

    @property
    def resetOnStop(self):
        """! get reset on stop setting"""
        return self.reset_on_stop

    @resetOnStop.setter
    def resetOnStop(self, ros: bool):
        self.reset_on_stop = int(ros)
        self.updateRawBytes()

    @property
    def resetOnStandby(self):
        """! get reset on standby setting"""
        return self.reset_on_standby

    @resetOnStandby.setter
    def resetOnStandby(self, ros: bool):
        self.reset_on_standby = int(ros)
        self.updateRawBytes()

    @property
    def dataByte0(self):
        return self.data_byte_0

    @dataByte0.setter
    def dataByte0(self, data: int):
        """! set the data 0 byte - only the first byte is valid
        @param data value to load (0x00 - 0xFF)
        """
        self.data_byte_0 = data & 0xFF
        self.updateRawBytes()

    @property
    def dataByte1(self):
        return self.data_byte_1

    @dataByte1.setter
    def dataByte1(self, data: int):
        """! set the data 0 byte - only the first byte is valid
        @param data value to load (0x00 - 0xFF)
        """
        self.data_byte_1 = data & 0xFF
        self.updateRawBytes()

    @property
    def readProtect(self) -> bool:
        return False if self.read_protect == 0xA5 else True

    @readProtect.setter
    def readProtect(self, enabled: bool):
        if enabled:
            self.read_protect = 0
        else:
            self.read_protect = 0xA5
        self.updateRawBytes()

    @property
    def writeProtect0(self):
        return self.write_protect_0

    @writeProtect0.setter
    def writeProtect0(self, data: int):
        self.write_protect_0 = data & 0xFF
        self.updateRawBytes()

    @property
    def writeProtect1(self):
        return self.write_protect_1

    @writeProtect1.setter
    def writeProtect1(self, data: int):
        self.write_protect_1 = data & 0xFF
        self.updateRawBytes()

    @property
    def writeProtect2(self):
        return self.write_protect_2

    @writeProtect2.setter
    def writeProtect2(self, data: int):
        self.write_protect_2 = data & 0xFF
        self.updateRawBytes()

    @property
    def writeProtect3(self):
        return self.write_protect_3

    @writeProtect3.setter
    def writeProtect3(self, data: int):
        self.write_protect_3 = data & 0xFF
        self.updateRawBytes()

    def enableWriteProtect(self):
        self.write_protect_0 = 0
        self.write_protect_1 = 0
        self.write_protect_2 = 0
        self.write_protect_3 = 0
        self.updateRawBytes()

    def disableWriteProtect(self):
        self.write_protect_0 = 0xFF
        self.write_protect_1 = 0xFF
        self.write_protect_2 = 0xFF
        self.write_protect_3 = 0xFF
        self.updateRawBytes()

    def dumpOptionBytes(self):
        print(f"nUser [{getByteComplement(self.user)}] user [{self.user}]", end="\t")
        print(f"Wdt type: {'software' if self.watchdog_type else 'hardware'}", end="\t")
        print(f"ReadProtect: {hex(self.readProtect)}")
        print(f"Data Byte 0: {hex(self.dataByte0)}\tData Byte 1: {hex(self.dataByte1)}")
        print("Raw: ", end="\t")
        print(self.raw_bytes)

    def rawBytesToString(self):
        output = ""
        for i in range(16):
            output += f"{hex(self.raw_bytes[i]).strip('0x').zfill(2).upper()} "
            if (i + 1) % 4 == 0:
                output += "\n"
        return output


class DeviceType:

    name: str
    ram: Region
    bootloader_ram: Region
    pid: int
    uid: int = 0
    system_memory: Region

    # 512 * 2kb XL density
    # 256 * 2kb high density
    # 128 * 1kb medium density
    # 32 * 1kb low density
    # 128 * 2kb connectivity density
    flash_page_size: int
    flash_page_num: int

    # 770 * 64bits XL
    # 2360 Connectivity
    # 258 rest
    flash_info_blk_size: int

    # 4kbB * 64bit low density
    # 16kB * 64bits med
    # 64kB * 64bits high
    # 32kB * 64 conn
    flash_mem_size: int

    def __init__(self, pid: int, bootloaderVersion: float):

        # same across most devices, intialise first, overwrite if neccesary
        self.pid = pid
        self.bootloaderVersion = bootloaderVersion
        self.bootloader_ram = Region("bootloader ram", 0x20000000, 0x200001FF)
        self.system_memory = Region("system memory", 0x1FFFF000, 0x1FFFF7FF)

        # select device characteristics from pid
        if self.pid == 0x0412:
            self.name = "stm32f10xxxLowDensity"
            self.ram = Region("ram", 0x20000200, 0x200027FF)
            self.flash_page_size = 1024
            self.flash_page_num = 32
            self.flash_info_blk_size = 258
        elif self.pid == 0x0410:
            self.name = "stm32f10xxxMedDensity"
            self.ram = Region("ram", 0x20000200, 0x20004FFF)
            self.flash_page_size = 1024
            self.flash_page_num = 128
            self.flash_info_blk_size = 258
        elif self.pid == 0x0414:
            self.name = "stm32f10xxxHighDensity"
            self.ram = Region("ram", 0x20000200, 0x2000FFFF)
            self.flash_page_size = 2048
            self.flash_page_num = 256
            self.flash_info_blk_size = 258
        elif self.pid == 0x0420:
            self.name = "stm32f10xxxMedDensityValueLine"
            self.ram = Region("ram", 0x20000200, 0x20001FFF)
            self.flash_page_size = 1024
            self.flash_page_num = 128
            self.flash_info_blk_size = 258
        elif self.pid == 0x0428:
            self.name = "stm32f10xxxHighDensityValueLine"
            self.ram = Region("ram", 0x20000200, 0x20007FFF)
            self.flash_page_size = 2048
            self.flash_page_num = 256
            self.flash_info_blk_size = 258
        elif self.pid == 0x0430:
            self.name = "stm32f10xxxXlDensity"
            self.ram = Region("ram", 0x20000800, 0x20017FFF)
            self.system_memory = Region("system memory", 0x1FFFF000, 0x1FFF77FF)
            self.flash_page_size = 2048
            self.flash_page_num = 256
            self.flash_info_blk_size = 258
            self.bootloader_ram = Region("bootloader ram", 0x20000000, 0x200007FF)
        else:
            raise DeviceNotSupportedError("Either an invalid or unsupported product")

        # flash memory region common
        self.flash_memory = Region(
            "flash memory",
            0x08000000,
            (0x08000000 + (self.flash_page_num * self.flash_page_size)),
        )

        self.flash_pages = []
        for i in range(self.flash_page_num):
            self.flash_pages.append(
                Region(
                    f"flash_page_{i}",
                    start=(self.flash_memory.start + (i * self.flash_page_size)),
                    end=(self.flash_memory.start + (i * self.flash_page_size))
                    + self.flash_page_size,
                )
            )

        # the flash option bytes should be read in their entirety
        # so use region rather than Register
        self.flash_option_bytes = Region("OptionBytes", 0x1FFFF800, 0x1FFF800 + 16)

        ## fill this in on demand
        self.opt_bytes = OptionBytes.FromAttributes()

    def updateOptionBytes(self, data: bytearray) -> None:
        self.opt_bytes = OptionBytes.FromBytes(data)

    def getFlashPageAddress(self, page: int):
        """! get the flash page start address
         checks the flash page is valid
        @param page - the flash page number
        @return page start address or None
        """
        if page > self.flash_page_num:
            return None
        offset = page * self.flash_page_size
        return self.flash_memory.start + offset
