

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




