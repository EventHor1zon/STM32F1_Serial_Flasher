from dataclasses import dataclass
from struct import unpack
from enum import Enum
from dataclasses import dataclass
from collections import namedtuple
from .errors import DeviceNotSupportedError

STM32_F1_FLASH_KEYS = {
    "RDPRT_KEY": 0x00A5,
    "KEY_1": 0x45670123,
    "KEY_2": 0xCDEF89AB,
}


FlashOptionBytes = namedtuple(
    "FlashOptionBytes",
    [
        "nUser",
        "user",
        "nReadProt",
        "readProt",
        "nData1",
        "data1",
        "nData0",
        "data0",
        "nWriteProt1",
        "writeProt1",
        "nWriteProt0",
        "writeProt0",
        "nWriteProt3",
        "writeProt3",
        "nWriteProt2",
        "writeProt2",
    ],
)


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
    end: int

    @property
    def size(self):
        return self.end - self.start


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

    def __init__(self, pid: int, bootloaderVersion: int):

        # same across most devices, intialise first, overwrite if neccesary
        self.bootloaderVersion = bootloaderVersion
        self.bootloader_ram = Region("bootloader ram", 0x20000000, 0x200001FF)
        self.system_memory = Region("system memory", 0x1FFFF000, 0x1FFFF7FF)

        # select device characteristics from pid
        if pid == 0x0412:
            self.name = "stm32f10xxxLowDensity"
            self.ram = Region("ram", 0x20000200, 0x200027FF)
            self.flash_page_size = 1024
            self.flash_page_num = 32
            self.flash_info_blk_size = 258
        elif pid == 0x0410:
            self.name = "stm32f10xxxMedDensity"
            self.ram = Region("ram", 0x20000200, 0x20004FFF)
            self.flash_page_size = 1024
            self.flash_page_num = 128
            self.flash_info_blk_size = 258
        elif pid == 0x0414:
            self.name = "stm32f10xxxHighDensity"
            self.ram = Region("ram", 0x20000200, 0x2000FFFF)
            self.flash_page_size = 2048
            self.flash_page_num = 256
            self.flash_info_blk_size = 258
        elif pid == 0x0420:
            self.name = "stm32f10xxxMedDensityValueLine"
            self.ram = Region("ram", 0x20000200, 0x20001FFF)
            self.flash_page_size = 1024
            self.flash_page_num = 128
            self.flash_info_blk_size = 258
        elif pid == 0x0428:
            self.name = "stm32f10xxxHighDensityValueLine"
            self.ram = Region("ram", 0x20000200, 0x20007FFF)
            self.flash_page_size = 2048
            self.flash_page_num = 256
            self.flash_info_blk_size = 258
        elif pid == 0x0430:
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

        # the flash option bytes should be read in their entirety
        # so use region rather than Register
        self.flash_option_bytes = Region("OptionBytes", 0x1FFFF800, 0x1FFF800 + 16)

        ## fill this in on demand
        self.option_bytes_contents = None

    def updateOptionBytes(self, data: bytearray) -> None:
        self.option_bytes_contents = FlashOptionBytes._make(unpack(">16B", data))



class DeviceMemoryMap:
    """ describes a device's memory layout - this is just a gathering place for information currently 
        it will be updated to be a good representation of the connected device's memory
    """

    fsmc = (Peripheral("FSMC", 0xA0000000, 0xA0000FFF),)
    usb_otg_fs = (Peripheral("USB OTG FS ", 0x50000000, 0x5003FFFF),)
    reserved1 = (Peripheral("Reserved", 0x40030000, 0x4FFFFFFF),)
    ethernet = (Peripheral("Ethernet", 0x40028000, 0x40029FFF),)
    reserved2 = (Peripheral("Reserved", 0x40023400, 0x40027FFF),)
    crc_sect = (Peripheral("CRC Section", 0x40023000, 0x400233FF),)
    flash_mem = (Peripheral("Flash memory interface", 0x40022000, 0x400223FF),)
    reserved3 = (Peripheral("Reserved", 0x40021400, 0x40021FFF),)
    reset_clk_control = (
        Peripheral("Reset and clock control RCC", 0x40021000, 0x400213FF),
    )
    reserved4 = (Peripheral("Reserved", 0x40020800, 0x40020FFF),)
    dma2 = (Peripheral("DMA2", 0x40020400, 0x400207FF),)
    dma1 = (Peripheral("DMA1", 0x40020000, 0x400203FF),)
    reserved5 = (Peripheral("Reserved ", 0x40018400, 0x4001FFFF),)
    sdio = (Peripheral("SDIO", 0x40018000, 0x400183FF),)
    reserved6 = (Peripheral("Reserved", 0x40015800, 0x40017FFF),)
    timer11 = (Peripheral("TIM11 timer", 0x40015400, 0x400157FF),)
    timer10 = (Peripheral("TIM10 timer", 0x40015000, 0x400153FF),)
    timer9 = (Peripheral("TIM9 timer ", 0x40014C00, 0x40014FFF),)
    reserved7 = (Peripheral("Reserved", 0x40014000, 0x40014BFF),)
    adc3 = (Peripheral("ADC3", 0x40013C00, 0x40013FFF),)
    usart1 = (Peripheral("USART1", 0x40013800, 0x40013BFF),)
    timer8 = (Peripheral("TIM8 timer", 0x40013400, 0x400137FF),)
    spi1 = (Peripheral("SPI1", 0x40013000, 0x400133FF),)
    timer1 = (Peripheral("TIM1 timer", 0x40012C00, 0x40012FFF),)
    adc2 = (Peripheral("ADC2", 0x40012800, 0x40012BFF),)
    adc1 = (Peripheral("ADC1", 0x40012400, 0x400127FF),)
    gpio_g = (Peripheral("GPIO Port G", 0x40012000, 0x400123FF),)
    gpio_f = (Peripheral("GPIO Port F", 0x40011C00, 0x40011FFF),)
    gpio_e = (Peripheral("GPIO Port E", 0x40011800, 0x40011BFF),)
    gpio_d = (Peripheral("GPIO Port D", 0x40011400, 0x400117FF),)
    gpio_c = (Peripheral("GPIO Port C", 0x40011000, 0x400113FF),)
    gpio_b = (Peripheral("GPIO Port B", 0x40010C00, 0x40010FFF),)
    gpio_a = (Peripheral("GPIO Port A", 0x40010800, 0x40010BFF),)
    exti = (Peripheral("EXTI", 0x40010400, 0x400107FF),)
    afio = (Peripheral("AFIO", 0x40010000, 0x400103FF),)
    reserved8 = (Peripheral("Reserved", 0x40007800, 0x4000FFFF),)
    dac = (Peripheral("DAC", 0x40007400, 0x400077FF),)
    power_control = (Peripheral("Power control PWR", 0x40007000, 0x400073FF),)
    backup = (Peripheral("Backup registers", 0x40006C00, 0x40006FFF),)
    can1 = (Peripheral("bxCAN1", 0x40006400, 0x400067FF),)
    can2 = (Peripheral("bxCAN2", 0x40006800, 0x40006BFF),)
    shared_usb_can_sram = (Peripheral("Shared USB/CAN SRAM", 0x40006000, 0x400063FF),)
    usb_fs = (Peripheral("USB device FS registers", 0x40005C00, 0x40005FFF),)
    i2c2 = (Peripheral("I2C2", 0x40005800, 0x40005BFF),)
    i2c1 = (Peripheral("I2C1", 0x40005400, 0x400057FF),)
    uart5 = (Peripheral("UART5", 0x40005000, 0x400053FF),)
    uart4 = (Peripheral("UART4", 0x40004C00, 0x40004FFF),)
    usart3 = (Peripheral("USART3", 0x40004800, 0x40004BFF),)
    usart2 = (Peripheral("USART2", 0x40004400, 0x400047FF),)
    reserved9 = (Peripheral("Reserved", 0x40004000, 0x400043FF),)
    spi3_i2s = (Peripheral("SPI3/I2S", 0x40003C00, 0x40003FFF),)
    spi_i2s_2 = (Peripheral("SPI2/I2S", 0x40003800, 0x40003BFF),)
    reserved10 = (Peripheral("Reserved", 0x40003400, 0x400037FF),)
    wdt = (Peripheral("Independent watchdog", 0x40003000, 0x400033FF),)
    window_wdt = (Peripheral("Window watchdog", 0x40002C00, 0x40002FFF),)
    rtc = (Peripheral("RTC", 0x40002800, 0x40002BFF),)
    reserved11 = (Peripheral("Reserved", 0x40002400, 0x400027FF),)
    timer14 = (Peripheral("TIM14 timer", 0x40002000, 0x400023FF),)
    timer13 = (Peripheral("TIM13 timer", 0x40001C00, 0x40001FFF),)
    timer12 = (Peripheral("TIM12 timer", 0x40001800, 0x40001BFF),)
    timer7 = (Peripheral("TIM7 timer", 0x40001400, 0x400017FF),)
    timer6 = (Peripheral("TIM6 timer", 0x40001000, 0x400013FF),)
    timer5 = (Peripheral("TIM5 timer", 0x40000C00, 0x40000FFF),)
    timer4 = (Peripheral("TIM4 timer", 0x40000800, 0x40000BFF),)
    timer3 = (Peripheral("TIM3 timer", 0x40000400, 0x400007FF),)
    timer2 = (Peripheral("TIM2 timer", 0x40000000, 0x400003FF),)

    flash_size = Register("Flash Size", 0x1FFFF7E0, 2)
    uid = Register("UniqueId", 0x1FFFF7E8, 24)
    flash_opt1 = Register("OptionByte1", 0x1FFFF800, 4)
    flash_opt2 = Register("OptionByte2", 0x1FFFF804, 4)
    flash_opt3 = Register("OptionByte3", 0x1FFFF808, 4)
    flash_opt4 = Register("OptionByte4", 0x1FFFF80C, 4)

    main_mem = Region("MainMemoryStart", 0x0800000, 2000)
    sys_mem = Region(
        "Sytem memory", 0x1FFFF000, 2000
    )  ## variable length depending on device type
    flash_option_bytes = Region("OptionBytes", 0x1FFFF800, 16)
    flash_acr = Register("FLASH_ACR", 0x40022000, 4)
    flash_kr = Register(
        "FLASH_KEYR", 0x40022004, 4,
    )
    flash_optkey = Register("FLASH_OPTKEYR", 0x40022008, 4)
    flash_status_reg = Register("FLASH_SR", 0x4002200C, 4),  ## status refister
    flash_control_reg = Register("FLASH_CR", 0x40022010, 4)  ## control register
    flash_addr_reg = Register("FLASH_AR", 0x40022014, 4)  ## address register
    flash_optbyte_reg = Register("FLASH_OBR", 0x4002201C, 4)  ## option byte register
    flash_wrprot_reg = Register("FLASH_WRPR", 0x40022020, 4)  ## write protect register

    STMF1_SRAM_START = 0x20000000
    STMF1_FLASH_SIZE = 0x1FFFF7E0


class DeviceDescriptor:

    bootloaderVersion: str
    validCommands: list
    # deviceDensity: DeviceDensity
    deviceType: int  ## TODO: enumerate?
    flashSize: int
    deviceUid: bytearray
    flashLockState: bool  ## TODO: Map this somehow

