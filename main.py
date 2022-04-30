# Created by: Jonathan Stendahl (me@jonathanstendahl.com)

import time
from array import *
import busio
import digitalio
import board
import adafruit_mcp3xxx.mcp3008 as MCP
from adafruit_mcp3xxx.analog_in import AnalogIn

try:
    from time import sleep_us
except ImportError:
    from time import sleep


def sleep_us(us):
    sleep(us/1000000)


sampling_time = 280
cov_ratio = 0.2  # ug/mmm / mv
no_dust_voltage = 400  # mv
sys_voltage = 3300


class Dust:
    def __init__(self):

        # create the spi bus
        self.spi = busio.SPI(clock=board.SCK, MISO=board.MISO, MOSI=board.MOSI)
        # create the cs (chip select)
        self.cs = digitalio.DigitalInOut(board.D22)
        # create the mcp object
        self.mcp = MCP.MCP3008(self.spi, self.cs)
        # create an analog input channel on pin 0
        self.chan0 = AnalogIn(self.mcp, MCP.P0)
        self.led = digitalio.DigitalInOut(board.D18)
        self.led.direction = digitalio.Direction.OUTPUT
        self.conversion_factor = 3.3 / (65535)
        self.flag_first = 0
        self.buff = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        self.sum1 = 0

    def Filter(self, ad_value):
        buff_max = 10
        if self.flag_first == 0:
            self.flag_first = 1
            for i in range(buff_max):
                self.buff[i] = ad_value
                self.sum1 = self.sum1+self.buff[i]
            return ad_value
        else:
            self.sum1 = self.sum1-self.buff[0]
            for i in range(buff_max-1):
                self.buff[i] = self.buff[i+1]
            self.buff[9] = ad_value
            self.sum1 = self.sum1 + self.buff[9]
            i = self.sum1 / 10.0
            return i


if __name__ == "__main__":
    Dust = Dust()
    while True:
        Dust.led.value = True  # power on the LED
        sleep_us(sampling_time)
        ad_value = Dust.chan0.value  # read the dust value
        Dust.led.value = False  # turn the LED off
        adcvalue = Dust.Filter(ad_value)
        voltage = (sys_voltage / 65536.0) * ad_value * 11
        if voltage >= no_dust_voltage:
            voltage -= no_dust_voltage
            density = voltage * cov_ratio
        else:
            density = 0
            print("voltage low: ", voltage)

        print("The current dust concentration is:", density, "ug/m3\n")
        time.sleep(1)
