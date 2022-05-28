


from dataclasses import dataclass
from enum import Enum
from dataclasses import dataclass


@dataclass
class Register:
    name: str
    start: int
    end: int

    def width(self) -> int:
        return self.end - self.start

@dataclass
class Region:
    name: str
    start: int
    size: int

class DeviceCommands(Enum):
    GET_COMMAND = 0
    VERSION_COMMAND = 1
    ID_COMMAND = 2


class DeviceType(Enum):
    NONE = 0


class DeviceMemoryMap:

    BOOTLOADER_START = 0x20000000
    BOOTLOADER_LEN = 2048

    Register("FSMC", 0xA0000000, 0xA0000FFF),
    Register("USB OTG FS ", 0x50000000, 0x5003FFFF),
    Register("Reserved", 0x40030000, 0x4FFFFFFF),
    Register("Ethernet", 0x40028000, 0x40029FFF),
    Register("Reserved", 0x40023400, 0x40027FFF),
    Register("CRC Section", 0x40023000, 0x400233FF),
    Register("Flash memory interface", 0x40022000, 0x400223FF),
    Register("Reserved", 0x40021400, 0x40021FFF),
    Register("Reset and clock control RCC", 0x40021000, 0x400213FF),
    Register("Reserved", 0x40020800, 0x40020FFF),
    Register("DMA2", 0x40020400, 0x400207FF),
    Register("DMA1", 0x40020000, 0x400203FF),
    Register("Reserved ", 0x40018400, 0x4001FFFF),
    Register("SDIO", 0x40018000, 0x400183FF),
    Register("Reserved", 0x40015800, 0x40017FFF),
    Register("TIM11 timer", 0x40015400, 0x400157FF),
    Register("TIM10 timer", 0x40015000, 0x400153FF),
    Register("TIM9 timer ", 0x40014C00, 0x40014FFF),
    Register("Reserved", 0x40014000, 0x40014BFF),
    Register("ADC3", 0x40013C00, 0x40013FFF),
    Register("USART1", 0x40013800, 0x40013BFF),
    Register("TIM8 timer", 0x40013400, 0x400137FF),
    Register("SPI1", 0x40013000, 0x400133FF),
    Register("TIM1 timer", 0x40012C00, 0x40012FFF),
    Register("ADC2", 0x40012800, 0x40012BFF),
    Register("ADC1", 0x40012400, 0x400127FF),
    Register("GPIO Port G", 0x40012000, 0x400123FF),
    Register("GPIO Port F", 0x40011C00, 0x40011FFF),
    Register("GPIO Port E", 0x40011800, 0x40011BFF),
    Register("GPIO Port D", 0x40011400, 0x400117FF),
    Register("GPIO Port C", 0x40011000, 0x400113FF),
    Register("GPIO Port B", 0x40010C00, 0x40010FFF),
    Register("GPIO Port A", 0x40010800, 0x40010BFF),
    Register("EXTI", 0x40010400, 0x400107FF),
    Register("AFIO", 0x40010000, 0x400103FF),
    Register("Reserved", 0x40007800, 0x4000FFFF),
    Register("DAC", 0x40007400, 0x400077FF),
    Register("Power control PWR", 0x40007000, 0x400073FF),
    Register("Backup registers", 0x40006C00, 0x40006FFF),
    Register("bxCAN1", 0x40006400, 0x400067FF),
    Register("bxCAN2", 0x40006800, 0x40006BFF),
    Register("Shared USB/CAN SRAM", 0x40006000, 0x400063FF),
    Register("USB device FS registers", 0x40005C00, 0x40005FFF),
    Register("I2C2", 0x40005800, 0x40005BFF),
    Register("I2C1", 0x40005400, 0x400057FF),
    Register("UART5", 0x40005000, 0x400053FF),
    Register("UART4", 0x40004C00, 0x40004FFF),
    Register("USART3", 0x40004800, 0x40004BFF),
    Register("USART2", 0x40004400, 0x400047FF),
    Register("Reserved", 0x40004000, 0x400043FF),
    Register("SPI3/I2S", 0x40003C00, 0x40003FFF),
    Register("SPI2/I2S", 0x40003800, 0x40003BFF),
    Register("Reserved", 0x40003400, 0x400037FF),
    Register("Independent watchdog", 0x40003000, 0x400033FF),
    Register("Window watchdog", 0x40002C00, 0x40002FFF),
    Register("RTC", 0x40002800, 0x40002BFF),
    Register("Reserved", 0x40002400, 0x400027FF),
    Register("TIM14 timer", 0x40002000, 0x400023FF),
    Register("TIM13 timer", 0x40001C00, 0x40001FFF),
    Register("TIM12 timer", 0x40001800, 0x40001BFF),
    Register("TIM7 timer", 0x40001400, 0x400017FF),
    Register("TIM6 timer", 0x40001000, 0x400013FF),
    Register("TIM5 timer", 0x40000C00, 0x40000FFF),
    Register("TIM4 timer", 0x40000800, 0x40000BFF),
    Register("TIM3 timer", 0x40000400, 0x400007FF),
    Register("TIM2 timer", 0x40000000, 0x400003FF),

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




