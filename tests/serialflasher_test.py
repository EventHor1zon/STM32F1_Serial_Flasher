## @file serialflasher_test.py
#
#   unit tests for the SerialFlasher class


DEFAULT_BAUD = 9600
VALID_PORT = "/dev/ttyUSB0"
INVALID_PORT = "/dev/ttyS0"

CMD_HANDSHAKE = b'\x7F'
STM_ACK = b'\x79'

import unittest
import serial
import STM_SerialFlasher.SerialFlasher as SF
import sys

class SerialFlasherTestCase(unittest.TestCase):

    def setUp(self):
        self.sf = SF.SerialTool()
    
    def tearDown(self):
        ## on teardown, close the socket
        self.sf.close()

    ## Utility functions 

    ## automate steps to open the port 
    def openPort(self):
        try:
            self.sf.port = VALID_PORT
            self.sf.openPort()
        except:
            print("Error Opening port!")
            return 0
        return 1

    def openPortWithHandshake(self):
        try:
            self.openPort()
            self.sf.writeDevice(CMD_HANDSHAKE)
            a = self.sf.readDevice(1)
            if a != STM_ACK:
                print("[!] Handshake ACK failed ")
                return 0
        except:
            print("[!] Error Opening serial port")
            return 0
        return 1

    ## test the initliser values
    def testInvalidLowBaud(self):
        baud = 100  # too low
        a = self.sf.setBaud(baud)
        self.assertEqual(a, False)

    def testInvalidHighBaud(self):
        baud = 1000000  # too high
        a = self.sf.setBaud(baud)
        self.assertEqual(a, False)

    def testInvalidBaudType(self):
        baud = "AAA"
        a = self.sf.setBaud(baud)
        self.assertEqual(a, False)
            

    def testSetPortInvalidType(self):
        port = 1234
        with self.assertRaises(TypeError):
            self.sf.setPort(port)

    def testGetBaudType(self):
        a = self.sf.getBaud()
        self.assertIsInstance(a, int)
        self.assertEqual(a, DEFAULT_BAUD)

    #def testSetNonexistentPort(self):
    #    self.sf.setPort("ABCD")
        

    def testOpenPortNoneSet(self):
        self.assertFalse(self.sf.openPort())

    def testClosePort(self):
        self.openPort()
        a = self.sf.ser.is_open
        self.assertEqual(a, True)
        self.sf.close()
        b = self.sf.ser.is_open
        self.assertNotEqual(a, b)


    def testGetTimeout(self):
        a = self.sf.getTimeout()
        self.assertIsInstance(a, float)
        self.assertGreater(a, 0.0009)  # ~ 1 / 115200  * 100
        self.assertLess(a, 0.085)      # ~ 1 / 1200  * 100

    def testGetSerialState(self):
        self.assertEqual(self.sf.getSerialState(), False)
        self.sf.setPort(VALID_PORT)
        self.sf.openPort()
        a=self.sf.getSerialState()
        self.assertEqual(a, True)

    def testValidWriteDevice(self):
        d = b'\x79'
        self.sf.setPort(VALID_PORT)
        self.sf.openPort()
        a = self.sf.writeDevice(d)
        self.assertEqual(a, 1)

    def testInvalidDataWriteDevice(self):
        d = [ "string", ('tupple', 1) ]
        self.sf.setPort(INVALID_PORT)
        self.sf.openPort()
        a = self.sf.writeDevice(d)
        self.assertEqual(a, 0)

    def testReadPortType(self):
        ## errrr... test against device??
        ## test against file?? 
        ## test against virtual serial port? 
        self.assertEqual(1, 1)
    
    def testCheckRxForAck(self):
        a = bytearray([0x79, 0x01, 0x02])
        b = bytearray([0x00, 0x01, 0x02])
        x = self.sf.checkRxForAck(a)
        y = self.sf.checkRxForAck(b)
        self.assertTrue(x)
        self.assertFalse(y)

    def testSendHandshake(self):
        # this is above - cant do twice in a row
        # assume success here implies read success?
        self.openPort()
        a = self.sf.sendHandshake()
        self.assertIsInstance(a, (bytearray, bytes))
        self.assertTrue(len(a) > 0)
        self.assertEqual(a, STM_ACK)

    def testCmdGetInfo(self):
        self.openPortWithHandshake()
        a = self.sf.cmdGetInfo()
        self.assertIsInstance(a, (bytearray, bytes))
        self.assertTrue(len(a) > 0)

    def testCmdGetVersionProt(self):
        self.openPortWithHandshake()
        a = self.sf.cmdGetVersionProt()
        self.assertIsInstance(a, (bytes, bytearray))
        self.assertTrue(len(a) > 0)

    def testGetDeviceInfo(self):
        self.openPortWithHandshake()
        a = self.sf.getDeviceInfo()
        self.assertIsInstance(a, dict)
            
    


