import signal
import sys
import threading

stopped = False
def signal_handler(sig, frame):
  global stopped
  stopped = True
signal.signal(signal.SIGINT, signal_handler)

#import all necessary functionality to the Script
import time
import Adafruit_ADS1x15

# Create an ADS1115 ADC (16-bit) instance. Note you can change the I2C address from its default (0x48) and/or bus number
#adc = Adafruit_ADS1x15.ADS1115()
adc = Adafruit_ADS1x15.ADS1115(address=0x48, busnum=1)

# Choose a gain of 1 for reading voltages from 0 to 4.09V.
# Or pick a different gain to change the range of voltages that are read:
#  - 2/3 = +/-6.144V
#  -   1 = +/-4.096V
#  -   2 = +/-2.048V
#  -   4 = +/-1.024V
#  -   8 = +/-0.512V
#  -  16 = +/-0.256V
# See table 3 in the ADS1015/ADS1115 datasheet for more info on gain.
GAIN = 16

#We will use this as a small counter to determine how long it took to recieve all the data points
t0 = time.time()

#If you want the script to run for a whole day this will enable that to happen
t_end = time.time() + (60 * 60 * 24)

start_read = time.time() 

def record():
  global stopped
  # Read the difference between channel 0 and 1 (i.e. channel 0 minus channel 1).
  # Note you can change the differential value to the following:
  #  - 0 = Channel 0 minus channel 1
  #  - 1 = Channel 0 minus channel 3
  #  - 2 = Channel 1 minus channel 3
  #  - 3 = Channel 2 minus channel 3
  adc.start_adc_difference(3, gain=GAIN, data_rate=128)
  while not stopped:
    starttime = time.time()
    value = adc.get_last_result()
    endtime = time.time()
    difftime = 1/131 - (endtime - starttime)
    #print(difftime)
    if (difftime > 0):
      time.sleep(difftime)
    #value = adc.read_adc_difference(3, gain=GAIN)
    print(str((value))+';' + str(int(time.time()*1000)))
  # Note you can also pass an optional data_rate parameter above, see
  # simpletest.py and the read_adc function for more information.
  # Value will be a signed 12 or 16 bit integer value (depending on the ADC
  # precision, ADS1015 = 12-bit or ADS1115 = 16-bit).
  # print(str((value))+';' + str(int(time.time()*1000)) + '\n')
    
  adc.stop_adc()    
 
t1 = threading.Thread(target=record)
t1.start()
t1.join()
