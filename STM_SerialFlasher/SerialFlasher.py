##
#  @file  Serial_Flasher.py
#  
#   Description: Python module creates an object with methods for 
#   interacting with the STM32 F1 line of microcontrollers via the 
#   Bootloader's serial interface.
# 
#   Also builds a profile of the device and its settings. 
#

import sys
import struct
import serial
import binascii

## SerialFlasher Class
#   This class represents the object used to interface
#   with the microcontroller. 
#  
#   methods:    
#   @param serial_port  - the name of the serial port to connect over
#   @param baud         - baud rate of connection. Use common rates, 1200 - 115200 inclusive.



BAUD = 57600
TIMEOUT_SPB_MOD = 30

CMD_GET = b'\x00'
CMD_BOOT_RP = b'\x01'
CMD_ID = b'\x02'

CMD_READOUT_LOCK = b'\x82'
CMD_READOUT_EN = b'\x92'
CMD_WRITE_PROT = b'\x63'
CMD_WRITE_EN = b'\x73'
CMD_HANDSHAKE = b'\x7F'

STM_ACK = b'\x79'
STM_NACK = b'\x1F'

ADDRESS_OPT_BYTES = bytearray(b'\x1F\xFF\xF8\x00')
ADDRESS_DEFAULT_CODESPACE = bytearray(b'\x80\x00\x00\x00')
ADDRESS_SCB_RST_OFFSET = 0x0C
SCB_RESET_REQUEST_VALUE = bytearray(b'\xfa\x05\x00\x04')

CFG_WRITE_TIMEOUT = 1




class SerialTool:

    deviceInfo = {
    'v_bootloader':0,
    'supported_commands':[],
    'readProtectionState':0,
    'readAccesses':0,
    'device_id':0,
    }
    
    def __init__(self, port=None, baud=9600):
        self.ser = serial.Serial(port=None)
        self.port = port
        self.baud = baud
        self.timeout = 1
        self.handshake_complete = 0

    def getBaud(self):
        return self.baud

    def setBaud(self, baud):
        if(self.checkBaud(baud)):
            self.baud = baud
        else:
            return False
        return True

    def checkBaud(self, baud):
        if not isinstance(baud, int):
            print("[!] Error: Baud must be of type int")
            return False
        if baud > 115200 or baud < 1200:
            return False
        else:
            return True

    def getPort(self):
        if self.port == None:
            return ""
        elif not isinstance(self.port, str):
            raise TypeError
        else:
            return self.port

    def setPort(self, port):
        if not isinstance(port, str):
            raise TypeError
        elif len(port) == 0:
            raise ValueError
        else:
            self.port = port
        return True

    def openPort(self):
        # sanity check connection details then connect
        if self.port == None:
            return False
        try:
            self.ser = serial.Serial(self.port, self.baud, parity=serial.PARITY_EVEN, timeout=self.timeout, write_timeout=CFG_WRITE_TIMEOUT)
        except serial.SerialException as e:
            print("[!] Error opening socket on port [" + self.port + "] with Baud " + str(self.baud))
            raise serial.SerialException
        return True

    def close(self):
        # close the socket
        if self.ser.is_open:
            self.ser.close()

    def getTimeout(self):
        ## generate read timeout of 100 bitwidths
        spb = float(1) / float(self.baud)
        return 100 * spb

    def utilGetSerialState(self):
        if self.ser == None:
            return 0
        else:
            return self.ser.is_open

    def utilAddCrc(self, data):
        if type(data) != bytearray and type(data) != bytes:
            raise ValueError

    def writeDevice(self, data):
        ## sanity check data, return serial.write
        sent = 0
        if not self.ser.is_open:
            print("[!] Error - Serial connection is closed")
            return 0
        if type(data) == bytes or type(data) == bytearray:
            try:
                sent = self.ser.write(data)
            except serial.SerialTimeoutException:
                print("[!] Attempt to write timed out")
            except serial.SerialException:
                print("[!] Attempt to write to serial caused an error")
            finally:
                return sent
        else:
            print("[!] Data type Error")
            return 0

    def readDevice(self, length):
        ## read len bytes from device
        # @ret bytes read,rx bytes

        rx = b''
        bytes_read = 0
        if not self.ser.is_open:
            print("[!] Error, serial port is closed")
            return 0
        for i in range(length):    
            try:   
                rx += self.ser.read(1)
                bytes_read += 1
            except serial.SerialException:
                print("[!] Error in reading from serial port")
                break 
            except serial.SerialTimeoutException:
                break
        
        return bytes_read,rx

    def checkRxForAck(self, data):
        ## check the first byte of data for ack
        # @ret True/False 
        if(type(data) != bytes and type(data) != bytearray):
            print("[!] Error: Invalid data type")
            return False
        elif len(data) < 1:
            print("[!] Error: Data is empty")
            return False
        else:
            a = data[0]
            b = bytes([a])
            if b == STM_ACK:
                return True 
            else:
                return False


    def sendHandshake(self):
        try:
            if self.ser.is_open:
                self.writeDevice(CMD_HANDSHAKE)
                rx_len,rx = self.readDevice(1)
                if rx == STM_ACK:
                    print("[+] Handshake Success!")
                    self.handshake_complete = 1
                    return rx
                else:
                    print("[!] Handshake failed")
                    return b''
        except serial.SerialException:
            print("[!] Error in making handshake")
            return b''  


    def cmdGetInfo(self):
        ## send the Get Info command 
        ## @ret - Rx data
        empty = b''
        if not self.ser.is_open:
            return empty
        if not self.handshake_complete:
            self.sendHandshake()

        crc = ~CMD_GET
        commands = bytearray([CMD_GET, crc])
        self.ser.write(commands)
        rx_len,rx = self.readDevice(16)

        return rx_len,rx

    def cmdGetVersionProt(self):
        ## send the Version/ReadProtection command 
        ## @ret - Rx data
        empty = b''
        if not self.ser.is_open:
            return empty
        if not self.handshake_complete:
            self.sendHandshake()
        commands = bytearray([CMD_BOOT_RP])
        self.utilAddCrc(commands)
        self.writeDevice(commands)
        rx_len, rx = self.readDevice(32)
        
        return rx_len, rx

    def cmdGetDeviceID(self):
        ## send the Get ID command
        # @ret - device ID
        pass

    def getDeviceInfo(self):
        ## get device information from Version/Getinfo 
        ## @ret - Dict containing device info
        pass
    
    def cmdWriteEnable(self):
        ## send the write-enable command 
        ## @ret - >??
        pass

    def cmdReadoutProtect(self):
        ## send the readout protect command 
        ## @ret - Rx data
        pass

    def cmdReadoutProtectOff(self):
        ## send the readout protect off command 
        ## @ret - Rx data
        pass

    def cmdGoToAddress(self, address):
        ## send the Go command 
        ## @ret - Rx data
        pass

    def writeToAddress(self, data, address):
        ## write data to address on device 
        ## @ret - ??
        pass

    def loadFlash(self, data, address):
        ## load a flash program to the device at address 
        ## @ret - Rx data
        pass

    def flashAndGo(self, data, address):
        ## load a flash program to address and execute
        ## @ret ??
        pass

    def readFlashFromAddress(self, length, address):
        ## read the flash starting at address, length bytes
        # @ret ??
        pass

    def dumpFlash(self):
        ## read the entire flash
        # @ret flash contents
        pass

    def dumpFlashToFile(self, file):
        ## read the entire flash and dump to file
        # @ret success/fail 
        pass

    def checkAddressInRange(self, address):
        ## check if address is valid
        # @ret true/false 
        pass

    def checkCandidateExecutable(self, exe):
        ## check if exe is valid 
        # @ret true/false 
        pass

