import signal
import sys
import time

keepRunning = True

def signal_handler(sig, frame):
    global keepRunning
    keepRunning = False

signal.signal(signal.SIGINT, signal_handler)
while keepRunning == True:
  time.sleep(0.01)
  print("0;" + str(int(time.time() * 1000)))

