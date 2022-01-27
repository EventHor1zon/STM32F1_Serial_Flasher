## @file serialflasher_test.py
#
#   unit tests for the SerialFlasher class


VALID_PORT = "/dev/ttyUSB0"
INVALID_PORT = "/dev/ttyS0"

CMD_HANDSHAKE = b'\x79'
STM_ACK = b'\x7F'

import unittest
import serial
import SerialFlasher.SerialFlasher as SF
import sys
from time import sleep


# a non-existent serial port
DEVICE_SERIAL_PORT = '/dev/ttyUSB0'
DEVICE_SERIAL_BAUD = 57600

SFTEST_INVALID_SERIAL_PORT="/dev/ttyABCD"



class SerialFlasherTestCase(unittest.TestCase):

    def setUp(self):
        self.serial = serial.Serial(DEVICE_SERIAL_PORT, DEVICE_SERIAL_BAUD)
        self.sf = SF.SerialTool()

    def tearDown(self):
        """ Teardown: Close socket and reset device """
        self.serial.close()
        self.resetDevice()
        return super().tearDown()

    def resetDevice(self):
        """ uses the DTR pin of USB->Serial to reset board """
        self.serial.setDTR(1)
        sleep(0.001)
        self.serial.setDTR(0)


    ## test the initliser values
    def testInvalidLowBaud(self):
        baud = 100  # too low
        with self.assertRaises(ValueError):
            self.sf.setBaud(baud)


    def testInvalidHighBaud(self):
        baud = 1000000  # too high
        with self.assertRaises(ValueError):
            self.sf.setBaud(baud)


    def testInvalidBaudType(self):
        baud = "AAA"
        with self.assertRaises(TypeError):
            self.sf.setBaud(baud)


    def testSetPortInvalidType(self):
        port = 1234
        with self.assertRaises(TypeError):
            self.sf.setPort(port)


    def testOpenPortNoneSet(self):
        self.assertFalse(self.sf.openPort())

    def testGetTimeout(self):
        pass

    def testGetSerialState(self):
        pass

    def testValidWriteDevice(self):
        pass

    def testInvalidDataWriteDevice(self):
        pass

    def testReadPortType(self):
        pass

    def testSendHandshake(self):
        pass
        

    
    
    


