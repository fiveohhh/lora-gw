from spi import Spi
import rf95_registers

class Radio():
    def __init__(self, channel):
        #SPIchannel = 1
        SPIspeed = 500000
        self.radio = Spi(channel, SPIspeed)

        # put into sleep and lora mode
        self.radio.writeRegister(rf95_registers.RH_RF95_REG_01_OP_MODE, 0x80)

        # read reg back
        print("mode: " + str(bin(self.radio.readFieldInRegister(rf95_registers.RH_RF95_REG_01_OP_MODE, 0, 8))))

        # set up fifo to use full length
        self.radio.writeRegister(rf95_registers.RH_RF95_REG_0E_FIFO_TX_BASE_ADDR, 0x00)
        self.radio.writeRegister(rf95_registers.RH_RF95_REG_0F_FIFO_RX_BASE_ADDR, 0x00)

        # Put into standy
        self.radio.writeRegister(rf95_registers.RH_RF95_REG_01_OP_MODE, 0x01)

        # Config radio
        self.radio.writeRegister(rf95_registers.RH_RF95_REG_1D_MODEM_CONFIG1, 0x72)
        self.radio.writeRegister(rf95_registers.RH_RF95_REG_1E_MODEM_CONFIG2, 0x74)
        self.radio.writeRegister(rf95_registers.RH_RF95_REG_26_MODEM_CONFIG3, 0x00)

        # set preamble to 8
        self.radio.writeRegister(rf95_registers.RH_RF95_REG_20_PREAMBLE_MSB, 0x00)
        self.radio.writeRegister(rf95_registers.RH_RF95_REG_21_PREAMBLE_LSB, 0x08)

        # Set Frequency to 915
        val = 915000000*524288/32000000
        self.radio.writeRegister(rf95_registers.RH_RF95_REG_08_FRF_LSB , (val) & 0xff)
        self.radio.writeRegister(rf95_registers.RH_RF95_REG_07_FRF_MID , ((val >> 8) & 0xff))
        self.radio.writeRegister(rf95_registers.RH_RF95_REG_06_FRF_MSB , ((val >> 16) & 0xff ))

        # set tx power
        self.radio.writeRegister(rf95_registers.RH_RF95_REG_4D_PA_DAC,0x07)
        self.radio.writeRegister(rf95_registers.RH_RF95_REG_09_PA_CONFIG,0x8f)

        # set continusous rx
        self.radio.writeRegister(rf95_registers.RH_RF95_REG_01_OP_MODE, 0x05)
        self.radio.writeRegister(rf95_registers.RH_RF95_REG_40_DIO_MAPPING1, 0x00)

        #clear rx flags
        self.radio.writeRegister(rf95_registers.RH_RF95_REG_12_IRQ_FLAGS, 0xff)

    #def isPacketAvailable(self):
    #    flags = self.radio.readRegister(rf95_registers.RH_RF95_REG_12_IRQ_FLAGS)
    #    print(flags)
    #    if (flags & 40):
    #        print(flags)
    #        return flags
    #    else:
    #        return None


    #def waitForPacket(self):
    #    a = self.isPacketAvailable()
    #    while (a == None):
    #        a = self.isPacketAvailable()
    #        #print("wait")
    #        #let's update to wait gracefully
    #        pass
    #   # return(a)
