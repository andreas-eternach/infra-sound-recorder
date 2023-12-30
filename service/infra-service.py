import time
import signal
import subprocess
import time
from datetime import datetime
from datetime import datetime

keepRunning = True

def signal_handler(sig, frame):
    global keepRunning
    keepRunning = False
    global process
    process.send_signal(signal.SIGINT)
    time.sleep(1)
    exit(0)

signal.signal(signal.SIGINT, signal_handler)
while keepRunning:
    with open("timestamp.txt", "a") as f:
        f.write("The current timestamp is: " + str(datetime.now()))
        f.close()
    dt_object = datetime.now()
    logfile = open("/home/pi/i2c/" + 
      format(dt_object.year, '04d') + 
      format(dt_object.month, '02d') + 
      format(dt_object.day, '02d') + 
      "-" + 
      format(dt_object.hour, '02d') + 
      format(dt_object.minute, '02d') + 
      ".csv", "w", 1)
    global process
    process = subprocess.Popen(["/usr/bin/python3", "/home/pi/i2c/test.py"], stdin = None, stdout = logfile)
    time.sleep(600)
    if (keepRunning):
      process.send_signal(signal.SIGINT)
      time.sleep(1)
