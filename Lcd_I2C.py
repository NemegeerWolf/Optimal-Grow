from RPi import GPIO
from smbus import SMBus
import time


class Lcd_I2C:
    GPIO.setmode(GPIO.BCM)

    def __init__(self, adres, enable_pin, instruction_pin, readWrite_pin=-1, hoogte=2, breedte=16, cursor=0, cursor_blinking=0, bit4=0):
        self.I2C = SMBus()
        self.I2C.open(1)

        self.adres = adres
        self.lcd_hoogte = hoogte
        self.lcd_breedte = breedte

        self.enable_pin = enable_pin
        self.readWrite_pin = readWrite_pin
        self.instruction_pin = instruction_pin
        self.bit4 = bit4
        if readWrite_pin != -1:
            GPIO.setup((enable_pin, readWrite_pin, instruction_pin), GPIO.OUT)
        else:

            GPIO.setup((enable_pin, instruction_pin), GPIO.OUT)

        self.send_instruction(0x38 ^ (bit4 << 4))
        self.send_instruction(0x0C | (cursor << 1) | cursor_blinking)
        self.send_instruction(0x01)

    def send_instruction(self, value):
        GPIO.output(self.instruction_pin, False)
        GPIO.output(self.enable_pin, True)
        self.set_data_bits(value)
        GPIO.output(self.enable_pin, False)

    def send_character(self, value):
        GPIO.output(self.instruction_pin, True)
        GPIO.output(self.enable_pin, True)
        self.set_data_bits(value)

    def set_data_bits(self, value):
        if not self.bit4:

            self.I2C.write_byte(self.adres, value)
          #  print(self.I2C.read_byte(self.adres))
            time.sleep(0.001)
            GPIO.output(self.enable_pin, False)
        else:
            for e in range(0, 2):
                for i in range(0, 4):
                    GPIO.output(self.pinnen[i], value &
                                (1 << i+4))  # 0101 0101
                value = value << 4
                time.sleep(0.01)
                GPIO.output(self.enable_pin, False)
                time.sleep(0.01)
                GPIO.output(self.enable_pin, True)
        GPIO.output(self.enable_pin, True)

    def print(self, text):
        # if(len(text)> self.lcd_breedte):
        #     text = text.split()
        # if(type(text) == list):
        #     for line in text:
        #         for character in line:
        #             self.send_character(ord(character))
        # else:
        for character in text:
            self.send_character(ord(character))

    def set_cursor(self, x, y):
        positie = (x + y*0x40) | 0x80
        self.send_instruction(positie)
