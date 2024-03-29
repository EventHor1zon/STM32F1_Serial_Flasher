"""This file contains definitions for the OptionBytes and DeviceType classes. See README for 
a fuller description.

"""

from __future__ import annotations

from dataclasses import dataclass
from struct import unpack, pack
from enum import Enum
from dataclasses import dataclass
from collections import namedtuple
from .errors import DeviceNotSupportedError, InvalidAddressError
from .utilities import getByteComplement, setBit, clearBit

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
class Region:
    """describes a region of memory space on the device"""

    name: str
    start: int
    end: int

    @property
    def size(self) -> int:
        """get size of region in bytes

        Returns:
            int: size in bytes
        """
        return self.end - self.start

    def is_valid(self, address: int) -> bool:
        """return True if address is in range start -> end

        Args:
            address (int): address to validate

        Returns:
            bool: is_valid
        """
        return address >= self.start and address < self.end


class DeviceDensity(Enum):
    DEVICE_TYPE_UNKNOWN = 0
    DEVICE_TYPE_LOW_DENSITY = 1
    DEVICE_TYPE_MEDIUM_DENSITY = 2
    DEVICE_TYPE_HIGH_DENSITY = 3
    DEVICE_TYPE_XL_DENSITY = 4


class OptionBytes:
    """Enough messing about with tuples
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
        """Default Constructor - do not use"""
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
    ) -> OptionBytes:
        """constructor - create an option-bytes object from supplied
        attributes

        Args:
            read_protect (int, optional): read-protect setting. Defaults to 0x00,
            watchdog_type (int, optional): watchdog type. Defaults to 0,
            reset_on_stop (int, optional): reset on stop enabled. Defaults to 1,
            reset_on_standby (int, optional): reset on standby enabled. Defaults to 0.
            data_byte_0 (int, optional): User Data byte 0 value . Defaults to 0x00.
            data_byte_1 (int, optional): User Data byte 1 value. Defaults to 0x00.
            write_protect_0 (int, optional): wp0. Defaults to 0x00.
            write_protect_1 (int, optional): wp1. Defaults to 0x00.
            write_protect_2 (int, optional): wp2. Defaults to 0x00.
            write_protect_3 (int, optional): wp3. Defaults to 0x00.

        Returns:
            OptionBytes: the OptionBytes object
        """
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
    def FromBytes(cls, data: bytearray) -> OptionBytes:
        """Constructor - creates an option-bytes object from
        an array of bytes. Simplifies decoding the option-byte
        settings read from a device

        Args:
            data (bytearray): 16-byte array of option-bytes

        Returns:
            OptionBytes: the option-bytes object
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

    def generateUserByte(self) -> int:
        """generate the user-byte from watchdog and reset settings

        Returns:
            int: assembled user-byte
        """
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

    def toBytes(self) -> bytearray:
        """generate option bytes as raw bytes from attributes

        Returns:
            bytearray: raw bytes
        """
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

    def updateRawBytes(self) -> None:
        """updates the raw bytes attribute from self attributes"""
        self.raw_bytes = self.toBytes()

    @property
    def rawBytes(self) -> bytearray:
        """raw bytes getter

        Returns:
            bytearray: option bytes as 16-byte array
        """
        return self.raw_bytes

    @property
    def watchdogType(self) -> int:
        """getter for watchdog type
            TODO: Fix this as a variable type - don't mix
                    bool/int in getter/setter!

        Returns:
            int: watchdog type
        """
        return self.watchdog_type

    @watchdogType.setter
    def watchdogType(self, watchdog_type: bool) -> None:
        """setter for the watchdog type
        update the user byte too
        Args:
            watchdog_type: False - Hardware Watchdog
                           True - Software watchdog
        """
        self.watchdog_type = int(watchdog_type)
        self.updateRawBytes()

    @property
    def resetOnStop(self) -> int:
        """reset on stop getter

        Returns:
            int: reset on stop enabled
        """
        return self.reset_on_stop

    @resetOnStop.setter
    def resetOnStop(self, ros: bool) -> None:
        """setter for reset on stop

        Args:
            ros (bool): reset on stop enabled
        """
        self.reset_on_stop = int(ros)
        self.updateRawBytes()

    @property
    def resetOnStandby(self) -> bool:
        """geetter for reset on standby

        Returns:
            bool: enabled
        """
        return self.reset_on_standby

    @resetOnStandby.setter
    def resetOnStandby(self, ros: bool) -> None:
        """reset on standby enabled

        Args:
            ros (bool): enabled
        """
        self.reset_on_standby = int(ros)
        self.updateRawBytes()

    @property
    def dataByte0(self) -> int:
        """getter for data byte 0

        Returns:
            int: data byte 0 value
        """
        return self.data_byte_0

    @dataByte0.setter
    def dataByte0(self, data: int) -> None:
        """setter for dataByte0

        Args:
            int: data byte value (max 255)
        """
        self.data_byte_0 = data & 0xFF
        self.updateRawBytes()

    @property
    def dataByte1(self) -> int:
        """getter for data byte 1

        Returns:
            int: data byte 1
        """
        return self.data_byte_1

    @dataByte1.setter
    def dataByte1(self, data: int) -> None:
        """! set the data 0 byte - only the first byte is valid
        @param data value to load (0x00 - 0xFF)
        """
        self.data_byte_1 = data & 0xFF
        self.updateRawBytes()

    @property
    def readProtect(self) -> bool:
        """getter for read protect setting

        Returns:
            bool: read protect enabled
        """
        return False if self.read_protect == 0xA5 else True

    @readProtect.setter
    def readProtect(self, enabled: bool) -> None:
        """setter for read protect setting

        Args:
            enabled (bool): read protect enable
        """
        if enabled:
            self.read_protect = 0
        else:
            self.read_protect = 0xA5
        self.updateRawBytes()

    @property
    def writeProtect0(self) -> int:
        """getter for write protect section 0

        Returns:
            int: write protect setting
        """
        return self.write_protect_0

    @writeProtect0.setter
    def writeProtect0(self, data: int) -> None:
        """setter for write protect 0

        Args:
            data (int): write protect 0 byte
        """
        self.write_protect_0 = data & 0xFF
        self.updateRawBytes()

    @property
    def writeProtect1(self):
        """getter for write protect section 1

        Returns:
            int: write protect setting
        """
        return self.write_protect_1

    @writeProtect1.setter
    def writeProtect1(self, data: int):
        """setter for write protect 1

        Args:
            data (int): write protect 0 byte
        """
        self.write_protect_1 = data & 0xFF
        self.updateRawBytes()

    @property
    def writeProtect2(self):
        """getter for write protect section 2

        Returns:
            int: write protect setting
        """
        return self.write_protect_2

    @writeProtect2.setter
    def writeProtect2(self, data: int):
        """setter for write protect 2

        Args:
            data (int): write protect 0 byte
        """
        self.write_protect_2 = data & 0xFF
        self.updateRawBytes()

    @property
    def writeProtect3(self):
        """getter for write protect section 3

        Returns:
            int: write protect setting
        """
        return self.write_protect_3

    @writeProtect3.setter
    def writeProtect3(self, data: int):
        """setter for write protect 3

        Args:
            data (int): write protect 0 byte
        """
        self.write_protect_3 = data & 0xFF
        self.updateRawBytes()

    def enableWriteProtect(self) -> None:
        self.write_protect_0 = 0
        self.write_protect_1 = 0
        self.write_protect_2 = 0
        self.write_protect_3 = 0
        self.updateRawBytes()

    def disableWriteProtect(self) -> None:
        self.write_protect_0 = 0xFF
        self.write_protect_1 = 0xFF
        self.write_protect_2 = 0xFF
        self.write_protect_3 = 0xFF
        self.updateRawBytes()

    def dumpOptionBytes(self) -> None:
        print(f"nUser [{getByteComplement(self.user)}] user [{self.user}]", end="\t")
        print(f"Wdt type: {'software' if self.watchdog_type else 'hardware'}", end="\t")
        print(f"ReadProtect: {hex(self.readProtect)}")
        print(f"Data Byte 0: {hex(self.dataByte0)}\tData Byte 1: {hex(self.dataByte1)}")
        print("Raw: ", end="\t")
        print(self.raw_bytes)

    def rawBytesToString(self) -> None:
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

    def __init__(self, pid: int, bootloaderVersion: float) -> DeviceType:
        """constructor for the DeviceType

        Args:
            pid (int): ID read from the device
            bootloaderVersion (float): bootloader version read from device
            TODO: Probably don't need BL version for constructor...?

        Raises:
            DeviceNotSupportedError: Device ID is not currently supported. See README for
            supported devices
        """
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

        # fill this in on demand
        self.opt_bytes = OptionBytes.FromAttributes()

    def updateOptionBytes(self, data: bytearray) -> None:
        """create the OptionBytes object

        Args:
            data (bytearray): raw optionbytes data
        """
        self.opt_bytes = OptionBytes.FromBytes(data)

    def getFlashPageAddress(self, page: int) -> int:
        """get the address for a particular flash page

        Args:
            page (int): page index

        Returns:
            int: page address
        """
        if page >= self.flash_page_num:
            raise InvalidAddressError(
                f"Invalid flash page requested (max {self.flash_pages_num-1})"
            )
        return self.flash_pages[page].start
