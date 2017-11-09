import struct
import re
import msgpack
import requests
import urllib
import json
import sys
import rf95_registers
from aes_gcm import AES_GCM
import devices
from rfm95_lora import Radio

def getCik(deviceId):
    if deviceId == 7:
        return "hh7acpkq64F8d7hxDQYWYoth2hNJ5Pv3b077Bg8i"

    else:
        return None


gcms = {}

def getGCM(deviceId):
    if deviceId == 6:
        return gcms[deviceId]

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
    o = requests.post('https://' + str(devices.devices[str(packet.fromAddress)]['pid'])  + '.m2.exosite.io/onep:v1/stack/alias', headers=headers, data=urllib.urlencode(payload))
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

def initKeys():
    global gcms
    for id, device in devices.devices.iteritems():
        gcms[id] = AES_GCM(device['key'])

def main():
    global gcms
    r = Radio(1)
    initKeys()
    pendingPackets = {}

    print("waiting for message")
    while (True):
        flags = r.radio.readRegister(rf95_registers.RH_RF95_REG_12_IRQ_FLAGS)
        while (not (flags & 0x40)):
            #print("waiting")
            flags = r.radio.readRegister(rf95_registers.RH_RF95_REG_12_IRQ_FLAGS)
        #flags = r.waitForPacket()
        #received packet
        from datetime import datetime
        print(datetime.now())

        # Check CRC
        isCrcValid = True if flags & 0x20 == 0 else False
        #print("Flags: {}".format(hex(flags)))
        #:print("CRC valid: {}" .format(isCrcValid))
        
        if isCrcValid == False:
            print("Invalid CRC")
            r.radio.writeRegister(rf95_registers.RH_RF95_REG_12_IRQ_FLAGS, 0xff)
            continue
        # Get length of packet
        length = r.radio.readFieldInRegister(rf95_registers.RH_RF95_REG_13_RX_NB_BYTES, 0, 8)

        # reset fifo ptr to start of rx packet
        rxStart = r.radio.readFieldInRegister(rf95_registers.RH_RF95_REG_10_FIFO_RX_CURRENT_ADDR, 0, 8)
        r.radio.writeFieldInRegister(rf95_registers.RH_RF95_REG_0D_FIFO_ADDR_PTR, 0, 8, rxStart)

        # read latest rx packet
        packet = r.radio.readBytes(rf95_registers.RH_RF95_REG_00_FIFO, length)[1][1:]
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
        r.radio.writeRegister(rf95_registers.RH_RF95_REG_12_IRQ_FLAGS, 0xff)
        sys.stdout.flush()


if __name__ == "__main__":
    main()
