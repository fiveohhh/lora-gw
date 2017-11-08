import wiringpi
import struct
import re
import msgpack
import requests
import urllib
import json
from aes_gcm import AES_GCM

SPIchannel = 1
SPIspeed = 500000



RH_RF95_REG_00_FIFO                        =        0x00
RH_RF95_REG_01_OP_MODE                     =        0x01
RH_RF95_REG_02_RESERVED                    =        0x02
RH_RF95_REG_03_RESERVED                    =        0x03
RH_RF95_REG_04_RESERVED                    =        0x04
RH_RF95_REG_05_RESERVED                    =        0x05
RH_RF95_REG_06_FRF_MSB                     =        0x06
RH_RF95_REG_07_FRF_MID                     =        0x07
RH_RF95_REG_08_FRF_LSB                     =        0x08
RH_RF95_REG_09_PA_CONFIG                   =        0x09
RH_RF95_REG_0A_PA_RAMP                     =        0x0a
RH_RF95_REG_0B_OCP                         =        0x0b
RH_RF95_REG_0C_LNA                         =        0x0c
RH_RF95_REG_0D_FIFO_ADDR_PTR               =        0x0d
RH_RF95_REG_0E_FIFO_TX_BASE_ADDR           =        0x0e
RH_RF95_REG_0F_FIFO_RX_BASE_ADDR           =        0x0f
RH_RF95_REG_10_FIFO_RX_CURRENT_ADDR        =        0x10
RH_RF95_REG_11_IRQ_FLAGS_MASK              =        0x11
RH_RF95_REG_12_IRQ_FLAGS                   =        0x12
RH_RF95_REG_13_RX_NB_BYTES                 =        0x13
RH_RF95_REG_14_RX_HEADER_CNT_VALUE_MSB     =        0x14
RH_RF95_REG_15_RX_HEADER_CNT_VALUE_LSB     =        0x15
RH_RF95_REG_16_RX_PACKET_CNT_VALUE_MSB     =        0x16
RH_RF95_REG_17_RX_PACKET_CNT_VALUE_LSB     =        0x17
RH_RF95_REG_18_MODEM_STAT                  =        0x18
RH_RF95_REG_19_PKT_SNR_VALUE               =        0x19
RH_RF95_REG_1A_PKT_RSSI_VALUE              =        0x1a
RH_RF95_REG_1B_RSSI_VALUE                  =        0x1b
RH_RF95_REG_1C_HOP_CHANNEL                 =        0x1c
RH_RF95_REG_1D_MODEM_CONFIG1               =        0x1d
RH_RF95_REG_1E_MODEM_CONFIG2               =        0x1e
RH_RF95_REG_1F_SYMB_TIMEOUT_LSB            =        0x1f
RH_RF95_REG_20_PREAMBLE_MSB                =        0x20
RH_RF95_REG_21_PREAMBLE_LSB                =        0x21
RH_RF95_REG_22_PAYLOAD_LENGTH              =        0x22
RH_RF95_REG_23_MAX_PAYLOAD_LENGTH          =        0x23
RH_RF95_REG_24_HOP_PERIOD                  =        0x24
RH_RF95_REG_25_FIFO_RX_BYTE_ADDR           =        0x25
RH_RF95_REG_26_MODEM_CONFIG3               =        0x26
                                           
RH_RF95_REG_40_DIO_MAPPING1                =        0x40
RH_RF95_REG_41_DIO_MAPPING2                =        0x41
RH_RF95_REG_42_VERSION                     =        0x42
                                                                                      
RH_RF95_REG_4B_TCXO                        =        0x4b
RH_RF95_REG_4D_PA_DAC                      =        0x4d
RH_RF95_REG_5B_FORMER_TEMP                 =        0x5b
RH_RF95_REG_61_AGC_REF                     =        0x61
RH_RF95_REG_62_AGC_THRESH1                 =        0x62
RH_RF95_REG_63_AGC_THRESH2                 =        0x63
RH_RF95_REG_64_AGC_THRESH3                 =        0x64




wiringpi.wiringPiSetupGpio()

wiringpi.wiringPiSPISetup(SPIchannel, SPIspeed)


def getCik(deviceId):
    if deviceId == 7:
        return "hh7acpkq64F8d7hxDQYWYoth2hNJ5Pv3b077Bg8i"

    else:
        return None


gcms = {}

def getGCM(deviceId):
    if deviceId == 6:
        return gcms[deviceId]


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
    masked = byte & (0xff >> 8 - (startBit+numOfBits))
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


def writeRegister(address, value):
    address = address | 0x80
    shiftedAddress = address << 8
    sendData = shiftedAddress
    sendData = sendData | value
    a = struct.pack(">H", sendData)
    wiringpi.wiringPiSPIDataRW(SPIchannel, a)


def readRegister(address):
    sendAddress = (address & 0x7f)
    sendData = struct.pack("<h", sendAddress)
    res = wiringpi.wiringPiSPIDataRW(SPIchannel, sendData)[1][1]
    return ord(res)


def readFieldInRegister(address, startBit, numOfBits):
    res = readRegister(address)
    return getBitsInByte(res, startBit, numOfBits)

def readBytes(address, numOfBytes):
    sendAddress = (address & 0x7f)
    sendData = struct.pack("B", sendAddress)
    sendData = sendData + ("\x00" * numOfBytes)
    res = wiringpi.wiringPiSPIDataRW(SPIchannel, sendData)
    return res



# PACKET STRUCTURE
######################################
#  to  # from # id  # flags # payload#
######################################
# to/from/id/flags are all 1 byte
# payload is remaining packet
# to: 0xff is broadcast, all other values are availble addresses
# from: address of sending radio
# id: id to identify the packet, used for application level logic
# flags: TBD
FLAG_ACK_REQ = 0x01 # This is used to tell the receiver you want an ack.  The receiver will also set this bit in response
                    # but it will use the same message ID and have an empty payload

class Packet(object):
    def __init__(self, packet, payload):
        if len(packet) < 5:
            # not a valid packet
            return None
        
        self.toAddress = struct.unpack("B", packet[0])[0]
        self.fromAddress = struct.unpack("B", packet[1])[0]
        self.id = struct.unpack("B", packet[2])[0]
        self.flags = struct.unpack("B", packet[3])[0]
        self.payload = payload
        self.message = msgpack.unpackb(self.payload)

        
    def __str__(self):
        out = "To: {} From: {} ID: {} msgPayload: {}".format(self.toAddress, self.fromAddress, self.id, self.message)
        return out




def initRadio():
    # put into sleep and lora mode
    writeRegister(RH_RF95_REG_01_OP_MODE, 0x80)

    # read reg back
    print("mode: " + str(bin(readFieldInRegister(RH_RF95_REG_01_OP_MODE, 0, 8))))

    # set up fifo to use full length
    writeRegister(RH_RF95_REG_0E_FIFO_TX_BASE_ADDR, 0x00)
    writeRegister(RH_RF95_REG_0F_FIFO_RX_BASE_ADDR, 0x00)

    # Put into standy
    writeRegister(RH_RF95_REG_01_OP_MODE, 0x01)

    # Config radio
    writeRegister(RH_RF95_REG_1D_MODEM_CONFIG1, 0x72)
    writeRegister(RH_RF95_REG_1E_MODEM_CONFIG2, 0x74)
    writeRegister(RH_RF95_REG_26_MODEM_CONFIG3, 0x00)

    # set preamble to 8
    writeRegister(RH_RF95_REG_20_PREAMBLE_MSB, 0x00)
    writeRegister(RH_RF95_REG_21_PREAMBLE_LSB, 0x08)

    # Set Frequency to 915
    val = 915000000*524288/32000000
    writeRegister(RH_RF95_REG_08_FRF_LSB , (val) & 0xff)
    writeRegister(RH_RF95_REG_07_FRF_MID , ((val >> 8) & 0xff))
    writeRegister(RH_RF95_REG_06_FRF_MSB , ((val >> 16) & 0xff ))

    # set tx power
    writeRegister(RH_RF95_REG_4D_PA_DAC,0x07)
    writeRegister(RH_RF95_REG_09_PA_CONFIG,0x8f)

    # set continusous rx
    writeRegister(RH_RF95_REG_01_OP_MODE, 0x05)
    writeRegister(RH_RF95_REG_40_DIO_MAPPING1, 0x00)

    #clear rx flags
    writeRegister(RH_RF95_REG_12_IRQ_FLAGS, 0xff)

pendingPackets = {}

def processPacket(packet):
    global pendingPackets
    if packet.flags & FLAG_ACK_REQ:
        if packet.id in pendingPackets:
            # send ack to node
            pendingPackets.pop(packet.id)
            return

    headers = {
            'X-Exosite-cik': getCik(packet.fromAddress),
            'Content-type':'application/x-www-form-urlencoded'
            }
    payload = {'raw_data':json.dumps(packet.message['values'])}
    o = requests.post('https://p1sva9qt09ds00000.m2.exosite.io/onep:v1/stack/alias', headers=headers, data=urllib.urlencode(payload))
    print(o)

def verifyPacket(raw_packet):
    # get authenticated data
    ad = raw_packet[0:4]

    # get IF
    iv = raw_packet[4:16]

    # get ciphertext
    ct = raw_packet[16:-16]

    # get tag
    tag = raw_packet[-16:]


    if str(ord(raw_packet[1])) in gcms:
        # have key
        a = gcms[str(ord(raw_packet[1]))].decrypt(int(iv.encode('hex'),16), ct, int(tag.encode('hex'),16), ad)
        print("valid")
        return(a)

    else:
        print("No key for: " + str(ord(raw_packet[1])))
        return None

def main():
    global gcms
    initRadio()
    gcms['6'] = AES_GCM(0xfeffe9928665731c6d6a8f9467308308)
    print("waiting for message")

    pendingPackets = {}


    while (True):
        flags = readRegister(RH_RF95_REG_12_IRQ_FLAGS)
        while (not (flags & 0x40)):
            #print("waiting")
            flags = readRegister(RH_RF95_REG_12_IRQ_FLAGS)

        #received packet
        from datetime import datetime
        print(datetime.now())

        # Check CRC
        isCrcValid = True if flags & 0x20 == 0 else False
        #print("Flags: {}".format(hex(flags)))
        #:print("CRC valid: {}" .format(isCrcValid))
        
        if isCrcValid == False:
            print("Invalid CRC")
            writeRegister(RH_RF95_REG_12_IRQ_FLAGS, 0xff)
            continue
        # Get length of packet
        length = readFieldInRegister(RH_RF95_REG_13_RX_NB_BYTES, 0, 8)

        # reset fifo ptr to start of rx packet
        rxStart = readFieldInRegister(RH_RF95_REG_10_FIFO_RX_CURRENT_ADDR, 0, 8)
        writeFieldInRegister(RH_RF95_REG_0D_FIFO_ADDR_PTR, 0, 8, rxStart)

        # read latest rx packet
        packet = readBytes(RH_RF95_REG_00_FIFO, length)[1][1:]
        #hex_chars = map(hex, map(ord,packet))

        #print(hex_chars)
        payload = verifyPacket(packet)
        if payload != None:
          try:
              p = Packet(packet, payload)
              processPacket(p)
          except Exception as e:
              print("Invalid message pack?")
              print(e)
        
        
        # reset flag
        writeRegister(RH_RF95_REG_12_IRQ_FLAGS, 0xff)


if __name__ == "__main__":
    main()
