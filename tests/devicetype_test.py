import unittest
from SerialFlasher.devices import DeviceType, Region, FlashOptionBytes
from SerialFlasher.errors import *
from collections import namedtuple

DEV_TEST_XL_DEVICE_ID = 0x0430
DEV_TEST_VALID_DEVICE_ID = 0x0410
DEV_TEST_INVALID_DEVICE_ID = 0xF410
DEV_TEST_VALID_BOOTLOADER_ID = 2.2
DEV_TEST_VALID_DEVICE_PAGE_SIZE = 1024


class DeviceTypeTestCase(unittest.TestCase):

    def testInitDeviceValidId(self):
        dev = DeviceType(DEV_TEST_VALID_DEVICE_ID, DEV_TEST_VALID_BOOTLOADER_ID)
        self.assertIsInstance(dev, DeviceType)
        self.assertEqual(dev.flash_page_size, DEV_TEST_VALID_DEVICE_PAGE_SIZE)

    def testInitDeviceInvalidId(self):
        with self.assertRaises(DeviceNotSupportedError):
            dev = DeviceType(DEV_TEST_INVALID_DEVICE_ID, DEV_TEST_VALID_BOOTLOADER_ID)

    def testDeviceBootloaderType(self):
        med_dev = DeviceType(DEV_TEST_VALID_DEVICE_ID, DEV_TEST_VALID_BOOTLOADER_ID)

        bootloader_med = med_dev.bootloader_ram
        self.assertIsInstance(bootloader_med, Region)
        self.assertIsInstance(bootloader_med.size, int)

    def testDeviceBootloaderRegionSize(self):
        xl_dev = DeviceType(DEV_TEST_XL_DEVICE_ID, DEV_TEST_VALID_BOOTLOADER_ID)
        med_dev = DeviceType(DEV_TEST_VALID_DEVICE_ID, DEV_TEST_VALID_BOOTLOADER_ID)

        bootloader_xl = xl_dev.bootloader_ram
        bootloader_med = med_dev.bootloader_ram

        self.assertGreater(bootloader_xl.size, bootloader_med.size)
        self.assertEqual(bootloader_med.size, 0x1FF)
        self.assertEqual(bootloader_xl.size, 0x7FF)

    def testDeviceFlashMemorySize(self):
        xl_dev = DeviceType(DEV_TEST_XL_DEVICE_ID, DEV_TEST_VALID_BOOTLOADER_ID)
        self.assertEqual(xl_dev.flash_memory.size, xl_dev.flash_page_num * xl_dev.flash_page_size)

    
    # namedtuple is not a specific type
    # def testOptionBytesType(self):
    #     dev = DeviceType(DEV_TEST_VALID_DEVICE_ID, DEV_TEST_VALID_BOOTLOADER_ID)
    #     self.assertIsInstance(dev.option_bytes_contents, FlashOptionBytes)