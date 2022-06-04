from dataclasses import dataclass
from enum import Enum
from dataclasses import dataclass
from typing import List


@dataclass
class Register:
    name: str
    start: int
    size: int

@dataclass
class Peripheral:
    """ describes a peripheral on the device """
    name: str
    start: int
    end: int

    def size(self) -> int:
        return self.end - self.start

@dataclass
class PeripheralRegister:
    """ describes a Peripheral register
        Offset from peripheral start address
        and value at reset
    """
    peripheral: Peripheral
    offset: int
    reset: int

@dataclass
class Region:
    """ describes a region of memory space on the device """
    name: str
    start: int
    size: int

class DeviceCommands(Enum):
    GET_COMMAND = 0
    VERSION_COMMAND = 1
    ID_COMMAND = 2

class DeviceDensity(Enum):
    DEVICE_TYPE_UNKNOWN = 0
    DEVICE_TYPE_LOW_DENSITY = 1
    DEVICE_TYPE_MEDIUM_DENSITY = 2
    DEVICE_TYPE_HIGH_DENSITY = 3
    DEVICE_TYPE_XL_DENSITY = 4


class DeviceMemoryMap:
    """ describes a device's memory layout - this is just a gathering place for information currently 
        it will be updated to be a good representation of the connected device's memory
    """

    Peripheral("FSMC", 0xA0000000, 0xA0000FFF),
    Peripheral("USB OTG FS ", 0x50000000, 0x5003FFFF),
    Peripheral("Reserved", 0x40030000, 0x4FFFFFFF),
    Peripheral("Ethernet", 0x40028000, 0x40029FFF),
    Peripheral("Reserved", 0x40023400, 0x40027FFF),
    Peripheral("CRC Section", 0x40023000, 0x400233FF),
    Peripheral("Flash memory interface", 0x40022000, 0x400223FF),
    Peripheral("Reserved", 0x40021400, 0x40021FFF),
    Peripheral("Reset and clock control RCC", 0x40021000, 0x400213FF),
    Peripheral("Reserved", 0x40020800, 0x40020FFF),
    Peripheral("DMA2", 0x40020400, 0x400207FF),
    Peripheral("DMA1", 0x40020000, 0x400203FF),
    Peripheral("Reserved ", 0x40018400, 0x4001FFFF),
    Peripheral("SDIO", 0x40018000, 0x400183FF),
    Peripheral("Reserved", 0x40015800, 0x40017FFF),
    Peripheral("TIM11 timer", 0x40015400, 0x400157FF),
    Peripheral("TIM10 timer", 0x40015000, 0x400153FF),
    Peripheral("TIM9 timer ", 0x40014C00, 0x40014FFF),
    Peripheral("Reserved", 0x40014000, 0x40014BFF),
    Peripheral("ADC3", 0x40013C00, 0x40013FFF),
    Peripheral("USART1", 0x40013800, 0x40013BFF),
    Peripheral("TIM8 timer", 0x40013400, 0x400137FF),
    Peripheral("SPI1", 0x40013000, 0x400133FF),
    Peripheral("TIM1 timer", 0x40012C00, 0x40012FFF),
    Peripheral("ADC2", 0x40012800, 0x40012BFF),
    Peripheral("ADC1", 0x40012400, 0x400127FF),
    Peripheral("GPIO Port G", 0x40012000, 0x400123FF),
    Peripheral("GPIO Port F", 0x40011C00, 0x40011FFF),
    Peripheral("GPIO Port E", 0x40011800, 0x40011BFF),
    Peripheral("GPIO Port D", 0x40011400, 0x400117FF),
    Peripheral("GPIO Port C", 0x40011000, 0x400113FF),
    Peripheral("GPIO Port B", 0x40010C00, 0x40010FFF),
    Peripheral("GPIO Port A", 0x40010800, 0x40010BFF),
    Peripheral("EXTI", 0x40010400, 0x400107FF),
    Peripheral("AFIO", 0x40010000, 0x400103FF),
    Peripheral("Reserved", 0x40007800, 0x4000FFFF),
    Peripheral("DAC", 0x40007400, 0x400077FF),
    Peripheral("Power control PWR", 0x40007000, 0x400073FF),
    Peripheral("Backup registers", 0x40006C00, 0x40006FFF),
    Peripheral("bxCAN1", 0x40006400, 0x400067FF),
    Peripheral("bxCAN2", 0x40006800, 0x40006BFF),
    Peripheral("Shared USB/CAN SRAM", 0x40006000, 0x400063FF),
    Peripheral("USB device FS registers", 0x40005C00, 0x40005FFF),
    Peripheral("I2C2", 0x40005800, 0x40005BFF),
    Peripheral("I2C1", 0x40005400, 0x400057FF),
    Peripheral("UART5", 0x40005000, 0x400053FF),
    Peripheral("UART4", 0x40004C00, 0x40004FFF),
    Peripheral("USART3", 0x40004800, 0x40004BFF),
    Peripheral("USART2", 0x40004400, 0x400047FF),
    Peripheral("Reserved", 0x40004000, 0x400043FF),
    Peripheral("SPI3/I2S", 0x40003C00, 0x40003FFF),
    Peripheral("SPI2/I2S", 0x40003800, 0x40003BFF),
    Peripheral("Reserved", 0x40003400, 0x400037FF),
    Peripheral("Independent watchdog", 0x40003000, 0x400033FF),
    Peripheral("Window watchdog", 0x40002C00, 0x40002FFF),
    Peripheral("RTC", 0x40002800, 0x40002BFF),
    Peripheral("Reserved", 0x40002400, 0x400027FF),
    Peripheral("TIM14 timer", 0x40002000, 0x400023FF),
    Peripheral("TIM13 timer", 0x40001C00, 0x40001FFF),
    Peripheral("TIM12 timer", 0x40001800, 0x40001BFF),
    Peripheral("TIM7 timer", 0x40001400, 0x400017FF),
    Peripheral("TIM6 timer", 0x40001000, 0x400013FF),
    Peripheral("TIM5 timer", 0x40000C00, 0x40000FFF),
    Peripheral("TIM4 timer", 0x40000800, 0x40000BFF),
    Peripheral("TIM3 timer", 0x40000400, 0x400007FF),
    Peripheral("TIM2 timer", 0x40000000, 0x400003FF),

    Register("Flash Size", 0x1FFFF7E0, 2)
    Register("UniqueId", 0x1FFFF7E8, 24)
    Register("OptionByte1", 0x1FFFF800, 4)
    Register("OptionByte2", 0x1FFFF804, 4)
    Register("OptionByte3", 0x1FFFF808, 4)
    Register("OptionByte4", 0x1FFFF80C, 4)

    Region("MainMemoryStart", 0x0800000, 2000)
    Region("Sytem memory", 0x1FFFF000, 2000) ## variable length depending on device type
    Region("OptionBytes", 0x1FFFF800, 16)
    Region("FLASH_ACR", 0x40022000, 4)
    Region("FLASH_KEYR", 0x40022004, 4,)
    Region("FLASH_OPTKEYR", 0x40022008, 4)
    Region("FLASH_SR", 0x4002200C, 4),      ## status refister
    Region("FLASH_CR", 0x40022010, 4)      ## control register
    Region("FLASH_AR", 0x40022014, 4)      ## address register
    Region("FLASH_OBR", 0x4002201C, 4)     ## option byte register
    Region("FLASH_WRPR", 0x40022020, 4)    ## write protect register

    flash_keys = {
        'RDPRT_KEY' : 0x00A5,
        'KEY_1': 0x45670123,
        'KEY_2': 0xCDEF89AB,
    }

    STMF1_SRAM_START = 0x20000000
    STMF1_FLASH_SIZE = 0x1FFFF7E0


@dataclass
class Device:

    bootloaderVersion: str
    validCommands: list
    # deviceDensity: DeviceDensity
    deviceType: int ## TODO: enumerate?
    flashSize: int
    deviceUid: bytearray
    flashLockState: bool ## TODO: Map this somehow
