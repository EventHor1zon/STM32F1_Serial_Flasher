##! Tests for the OptionBytes class
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


class OptioByteTestCase(unittest.TestCase):
    def testInitOptionBytesAttributesInstance(self):
        fob = OptionBytes.FromAttributes()
        self.assertIsInstance(fob, OptionBytes)

    def testOptionBytesFromBytesInstance(self):
        fob = OptionBytes.FromBytes(OPTBYTE_TEST_VALID_OPTION_BYTES)
        self.assertIsInstance(fob, OptionBytes)

    def testOptionBytesFromBytesKnownData(self):
        fob = OptionBytes.FromBytes(OPTBYTE_TEST_VALID_OPTION_BYTES)
        self.assertEqual(fob.data_byte_1, 0xA5)

    def testOptionBytesFromAttributesKnownData(self):
        fob = OptionBytes.FromAttributes(data_byte_1=0x1F)
        self.assertEqual(fob.data_byte_1, 0x1F)

    def testOptionBytesFromAttributesKnownWdType(self):
        fob = OptionBytes.FromAttributes(watchdog_type=1)
        self.assertEqual(fob.watchdogType, 1)

    def testOptionBytesToBytesMethod(self):
        fob = OptionBytes.FromBytes(OPTBYTE_TEST_VALID_OPTION_BYTES)
        raw = fob.rawBytes
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
