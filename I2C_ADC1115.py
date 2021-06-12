import time
from smbus import SMBus
from RPi import GPIO
class I2C_ADC1115:
    
    def __init__(self, bus, adr):
        if(type(bus)==SMBus):
            self.bus = bus
            self.adr = adr
        else:
            raise TypeError("bus need to be of type SMbus")

    def get_value(self, port):
        if(port>=0 and port <=3):
            data_out = [(1<<7)+((4+port)<<4)+0x5, 0x83]
            print(data_out)
            self.bus.write_i2c_block_data(0x48, 0x01, data_out)
            time.sleep(0.1)
            bezig = self.bus.read_i2c_block_data(0x48, 0x01, 1)
            while(not(bezig[0]>>7)&0x1):
                bezig = self.bus.read_i2c_block_data(0x48, 0x0, 1)
                # print(bezig[0])
                # print((bezig[0]>>7)&0x1)
                time.sleep(0.1)

            data_in = self.bus.read_i2c_block_data(0x48, 0x00, 2)
            return data_in
        else:
            raise ValueError("port don't exist. avaleble port (0,1,2,3)")