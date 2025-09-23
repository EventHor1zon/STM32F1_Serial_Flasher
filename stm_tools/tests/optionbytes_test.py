#! Tests for the OptionBytes class
#
# Test the loading/unloading of bytes
# against a known good option bytes contents
#

import unittest
from stm_tools.serialflasher.devices import OptionBytes
from stm_tools.serialflasher.errors import *

OPTBYTE_TEST_VALID_OPTION_BYTES = (
    b"\xa5Z\xff\x00Z\xa5\xff\x00\xff\x00\xff\x00\xff\x00\xff\x00"
)

OPTBYTE_TEST_VALID_ATTRIBUTES = {
    "read_protect": 0x00,
    "watchdog_type": 0x01,
    "reset_on_stop": 0x01,
    "reset_on_standby": 0x01,
    "data_byte_0": 0x00,
    "data_byte_1": 0xA5,
    "write_protect_0": 0x00,
    "write_protect_1": 0x00,
    "write_protect_2": 0x00,
    "write_protect_3": 0x00,
}

class OptioByteTestCase(unittest.TestCase):
    def testInitOptionBytesAttributesInstance(self):
        fob = OptionBytes.FromAttributes()
        self.assertIsInstance(fob, OptionBytes)

    def testOptionBytesFromBytesInstance(self):
        fob = OptionBytes.FromBytes(OPTBYTE_TEST_VALID_OPTION_BYTES)
        self.assertIsInstance(fob, OptionBytes)

    def testOptionBytesFromKnownAttributes(self):
        fob = OptionBytes.FromAttributes(**OPTBYTE_TEST_VALID_ATTRIBUTES)
        for field, value in OPTBYTE_TEST_VALID_ATTRIBUTES.items():
            # check that all attributes are set succesfully
            self.assertEqual(value, fob.__getattribute__(field))

    def testOptionBytesFromBytesKnownData(self):
        fob = OptionBytes.FromBytes(OPTBYTE_TEST_VALID_OPTION_BYTES)
        self.assertEqual(fob.data_byte_1, 0xA5)

    def testOptionBytesFromInvalidLenData(self):
        with self.assertRaises(UnpackInfoFailedError):
            invalid_length_data = OPTBYTE_TEST_VALID_OPTION_BYTES+b'\xCA\xFE\xBA\xBE'
            fob = OptionBytes.FromBytes(invalid_length_data)

    def testOptionBytesStrictCheckingInvalid(self):
        with self.assertRaises(InvalidChecksumError):
            invalid_checksum_data = OPTBYTE_TEST_VALID_OPTION_BYTES
            invalid_checksum_data[4] = 0x01
            fob = OptionBytes.FromBytes(invalid_checksum_data, strict_checking=True)
    
    def testOptionBytesStrictCheckingValid(self):
        fob = OptionBytes.FromBytes(OPTBYTE_TEST_VALID_OPTION_BYTES, strict_checking=True)
        self.assertIsInstance(fob, OptionBytes)

    def testOptionBytesFromAttributesKnownUserData(self):
        fob = OptionBytes.FromAttributes(data_byte_1=0x1F)
        self.assertEqual(fob.data_byte_1, 0x1F)

    def testOptionBytesFromAttributesKnownWdType(self):
        fob = OptionBytes.FromAttributes(watchdog_type=1)
        self.assertEqual(fob.watchdogType, 1)

    def testOptionBytesToBytesMethod(self):
        fob = OptionBytes.FromBytes(OPTBYTE_TEST_VALID_OPTION_BYTES)
        raw = fob.toBytes()
        self.assertIsInstance(raw, bytes)
        self.assertEqual(raw, OPTBYTE_TEST_VALID_OPTION_BYTES)

    def testOptionBytesResetsFromKnown(self):
        fob = OptionBytes.FromBytes(OPTBYTE_TEST_VALID_OPTION_BYTES)
        self.assertEqual(fob.resetOnStop, 0)
        self.assertEqual(fob.resetOnStandby, 1)
        self.assertEqual((fob.user >> 1 & 0b1), 1)
        self.assertEqual((fob.user >> 2 & 0b1), 0)

    def testOptionBytesSetWatchdogType(self):
        fob = OptionBytes.FromAttributes(watchdog_type=1)
        wdtbit = fob.toBytes()[1] & 0b1
        self.assertEqual(wdtbit, 1)

    def testOptionBytesSetWatchdogValue(self):
        fob = OptionBytes.FromAttributes(watchdog_type=0)
        fob.watchdogType = 1
        self.assertEqual(fob.watchdogType, 1)

    def testOptionBytesRawGetterMethodUpdates(self):
        fob = OptionBytes.FromAttributes(watchdog_type=0)
        raw_a = OptionBytes.rawBytes()
        OptionBytes.dataByte0 = 0x12
        raw_b = OptionBytes.rawBytes()
        self.assertNotEqual(raw_a, raw_b)

