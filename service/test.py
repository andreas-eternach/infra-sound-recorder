import signal
import sys
import time

keepRunning = True

def signal_handler(sig, frame):
    print("Subprocess received termination signal")
    global keepRunning
    keepRunning = False

signal.signal(signal.SIGINT, signal_handler)
sleepTime = 1/128
while keepRunning == True:
  time.sleep(sleepTime)
  print("0;" + str(int(time.time() * 1000)))
