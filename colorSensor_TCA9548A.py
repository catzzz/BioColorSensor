# imports

import sys
import time
import datetime
import random
import SDL_Pi_TCA9548A
import subprocess
import smbus

#/*=========================================================================
#    I2C ADDRESS/BITS
#    -----------------------------------------------------------------------*/
TCA9548A_ADDRESS =                         (0x70)    # 1110011 (A0+A1=VDD)
#/*=========================================================================*/

#/*=========================================================================
#    I2C ADDRESS/BITS
#    -----------------------------------------------------------------------*/
TCS34725_ADDRESS =                         (0X29)    # 1110011 (A0+A1=VDD)
#/*=========================================================================*/

#/*=========================================================================
#    CONFIG REGISTER (R/W)
#    -----------------------------------------------------------------------*/
TCA9548A_REG_CONFIG            =          (0x00)
#    /*---------------------------------------------------------------------*/

TCA9548A_CONFIG_BUS0  =                (0x01)  # 1 = enable, 0 = disable
TCA9548A_CONFIG_BUS1  =                (0x02)  # 1 = enable, 0 = disable
TCA9548A_CONFIG_BUS2  =                (0x04)  # 1 = enable, 0 = disable
TCA9548A_CONFIG_BUS3  =                (0x08)  # 1 = enable, 0 = disable

#/*=========================================================================*/

# Main Program

print ""
print "Test SDL_Pi_TCA9548A Version 1.0 - SwitchDoc Labs"
print ""
print "Sample uses 0x70"
print "Program Started at:"+ time.strftime("%Y-%m-%d %H:%M:%S")
print ""

filename = time.strftime("%Y-%m-%d%H:%M:%SRTCTest") + ".txt"
starttime = datetime.datetime.utcnow()

tca9545 = SDL_Pi_TCA9548A.SDL_Pi_TCA9545(addr=TCA9548A_ADDRESS, bus_enable = TCA9548A_CONFIG_BUS0)

print "-----------BUS 2-------------------"

tca9545.write_control_register(TCA9548A_CONFIG_BUS2)
# read the control register back
control_register = tca9545.read_control_register()
print "tca9545 control register B3-B0 = 0x%x"% (control_register & 0x0f )
print "ignore Interrupts if INT3' - INT0' not connected"
print "tca9545 control register Interrupts = 0x%x"% ((control_register & 0xf0) >> 4)

i2ccommand = "sudo i2cdetect -y 1"
output = subprocess.check_output (i2ccommand,shell=True, stderr=subprocess.STDOUT )
print output


print "------Print data------------------"


def calculateColorTemperature(r, g ,b):
    X=0.0   #   RGB to XYZ correlation
    Y=0.0   #   RGB to XYZ correlation
    Z=0.0   #   RGB to XYZ correlation
    xc=0.0  #   Chromaticity co-ordinates
    yc=0.0  #   Chromaticity co-ordinates
    n=0.0   #   McCamy's formula
    cct=0.0 #   color temperature
    '''
    /* 1. Map RGB values to their XYZ counterparts.    */
    /* Based on 6500K fluorescent, 3000K fluorescent   */
    /* and 60W incandescent values for a wide range.   */
    /* Note: Y = Illuminance or lux                    */
    '''
    X = (-0.14282 * r) + (1.54924 * g) + (-0.95641 * b)
    Y = (-0.32466 * r) + (1.57837 * g) + (-0.73191 * b)
    Z = (-0.68202 * r) + (0.77073 * g) + ( 0.56332 * b)
    # 2. Calculate the chromaticity co-ordinates
    xc = (X) / (X + Y + Z)
    yc = (Y) / (X + Y + Z)
    #/* 3. Use McCamy's formula to determine the CCT    */
    n = (xc - 0.3320) / (0.1858 - yc)
    #/* Calculate the final CCT */
    cct = (449.0 * pow(n, 3)) + (3525.0 * pow(n, 2)) + (6823.3 * n) + 5520.33

    #/* Return the results in degrees Kelvin */
    return cct

def calculateLux(r,g,b):
    illuminance=0.0
    '''
    /* This only uses RGB ... how can we integrate clear or calculate lux */
    /* based exclusively on clear since this might be more reliable?      */
    '''
    illuminance = (-0.32466 * r) + (1.57837 * g) + (-0.73191 * b)

    return illuminance

def rgb_to_hex(r,g,b):
  return '#%02X%02X%02X' % (r,g,b)

bus = smbus.SMBus(1)
# I2C address 0x29
# Register 0x12 has device ver.
# Register addresses must be OR'ed with 0x80
bus.write_byte(0x29,0x80|0x12)
ver = bus.read_byte(0x29)
# version # should be 0x44
if ver == 0x44:
 print "Device found\n"
 bus.write_byte(0x29, 0x80|0x00) # 0x00 = ENABLE register
 bus.write_byte(0x29, 0x01|0x02) # 0x01 = Power on, 0x02 RGB sensors enabled
 bus.write_byte(0x29, 0x80|0x14) # Reading results start register 14, LSB then MSB
 while True:
    data = bus.read_i2c_block_data(0x29, 0)
    clear = clear = data[1] << 8 | data[0]
    red = data[3] << 8 | data[2]
    green = data[5] << 8 | data[4]
    blue = data[7] << 8 | data[6]
    crgb = "C: %s, R: %s, G: %s, B: %s\n" % (clear, red, green, blue)
    print crgb
    #// Figure out some basic hex code for visualization
    sum = float(clear)
    r = float(red)
    g = float(green)
    b = float(blue)
    if (not r==0 )or (not g ==0 )or (not b ==0):
        r /=sum
        g /=sum
        b /=sum
        r *=256
        g *=256
        b *=256
        hex =rgb_to_hex(r, g, b)    #==> '#ffffff'
        print 'red: '+str(r)+' green: '+str(g)+' blue: '+str(b)+' Hex: '+ hex
        colorTemp = calculateColorTemperature(red, green, blue);
        lux = calculateLux(red, green, blue);
        print 'color temp: '+str(colorTemp)
        print 'color lux: '+str(lux)+' K'
        time.sleep(1)


else:
 print "Device not found\n"