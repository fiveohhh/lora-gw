


import wiringpi
import struct

class Spi():
    def __init__(self, channel, speed):
        self.channel = channel
        self.speed = speed
        wiringpi.wiringPiSetupGpio()
        wiringpi.wiringPiSPISetup(channel, speed)
       


    # byte char
    # startBit first bit we want to extract, from the right, 0 indexed
    # number of bits we want
    #  e.g. byte = "\xae" == 0b10101110
    #                             ^^^     
    # Given a start bit of 2  and a length of 3, these bits will be extracted
    def getBitsInByte(self, byte, startBit, numOfBits=1):
        # mask off lefty bits
        masked = byte & (0xff >> 8 - (startBit+numOfBits))
        final = masked >> startBit 
        return final


    # up to you to make sure value doesn't overflow into a different field
    def writeFieldInRegister(self, address, startBit, numOfBits, value):
        # Get original value
        # Make sure write bit isn't set
        readAddress = address & 0x7f
        sendData = struct.pack("<h", readAddress)
        original = wiringpi.wiringPiSPIDataRW(self.channel, sendData)[1][1]
        
        # clear the bits that we want to write
        rightMask =  (2**startBit) - 1
        leftMask = (0xff << (startBit + numOfBits)) & 0xff
        mask = (ord(struct.pack("B",rightMask)) | ord(struct.pack("B",leftMask)))
        
        # clear the bits in the area we care about
        originalMasked = ord(original) & mask

        # set the write bit
        address = address | 0x80
        shiftedAddress = address << 8
        writeData =  (value << startBit) | (originalMasked)
        sendData = shiftedAddress | writeData
        a = struct.pack(">H", sendData)
        wiringpi.wiringPiSPIDataRW(self.channel, a)


    def writeRegister(self, address, value):
        address = address | 0x80
        shiftedAddress = address << 8
        sendData = shiftedAddress
        sendData = sendData | value
        a = struct.pack(">H", sendData)
        wiringpi.wiringPiSPIDataRW(self.channel, a)


    def readRegister(self, address):
        sendAddress = (address & 0x7f)
        sendData = struct.pack("<h", sendAddress)
        res = wiringpi.wiringPiSPIDataRW(self.channel, sendData)[1][1]
        return ord(res)


    def readFieldInRegister(self, address, startBit, numOfBits):
        res = self.readRegister(address)
        return self.getBitsInByte(res, startBit, numOfBits)

    def readBytes(self, address, numOfBytes):
        sendAddress = (address & 0x7f)
        sendData = struct.pack("B", sendAddress)
        sendData = sendData + ("\x00" * numOfBytes)
        res = wiringpi.wiringPiSPIDataRW(self.channel, sendData)
        return res
