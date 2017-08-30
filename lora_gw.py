import wiringpi
import struct
SPIchannel = 1
SPIspeed = 500000
wiringpi.wiringPiSetupGpio()

wiringpi.wiringPiSPISetup(SPIchannel, SPIspeed)

# sendData = ("\x01\x00\x00")
# val = wiringpi.wiringPiSPIDataRW(SPIchannel, sendData)

# byte char
# startBit first bit we want to extract, from the right, 0 indexed
# number of bits we want
#  e.g. byte = "\xae" == 0b10101110
#                             ^^^     
# Given a start bit of 2  and a length of 3, these bits will be extracted
def getBitsInByte(byte, startBit, numOfBits=1):
    # mask off lefty bits
    masked = ord(byte) & (0xff >> 8 - (startBit+numOfBits))
    final = masked >> startBit 
    return final


# up to you to make sure value doesn't overflow into a different field
def writeFieldInRegister(address, startBit, numOfBits, value):
    # Get original value
    # Make sure write bit isn't set
    readAddress = address & 0x7f
    sendData = struct.pack("<h", readAddress)
    original = wiringpi.wiringPiSPIDataRW(SPIchannel, sendData)[1][1]
    
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
    wiringpi.wiringPiSPIDataRW(SPIchannel, a)

def readFieldInRegister(address, startBit, numOfBits):
    sendAddress = (address & 0x7f)
    sendData = struct.pack("<h", sendAddress)
    res = wiringpi.wiringPiSPIDataRW(SPIchannel, sendData)
    return getBitsInByte(res[1][1], startBit, numOfBits)


#put into standyby
print(writeFieldInRegister(0x01, 0, 3, 0))

# lora mode
print(writeFieldInRegister(0x01, 7, 1, 1))

# read reg back
readFieldInRegister(0x01, 0, 8)




