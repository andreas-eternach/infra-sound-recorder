import signal
import time
import numpy as np

keepRunning = True

# sampling rate
sr = 128
# sampling interval
ts = 1.0/sr
t = np.arange(0,1,ts)

freq = 1.
x = 3*np.sin(2*np.pi*freq*t)

freq = 16
x += np.sin(2*np.pi*freq*t)

freq = 45   
x += 0.5* np.sin(2*np.pi*freq*t)

index = 0

def signal_handler(sig, frame):
    print("Subprocess received termination signal")
    global keepRunning
    keepRunning = False

signal.signal(signal.SIGINT, signal_handler)
sleepTime = 1/128
while keepRunning == True:
  if index == x.size:
      index = 0
  time.sleep(sleepTime)
  print(str(x[index] * 10)+ ";" + str(int(time.time() * 1000)))
  index = index + 1
