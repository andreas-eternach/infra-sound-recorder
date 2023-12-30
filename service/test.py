import signal
import sys
import time

keepRunning = True

def signal_handler(sig, frame):
    global keepRunning
    keepRunning = False

signal.signal(signal.SIGINT, signal_handler)
while (keepRunning == True):
  time.sleep(5)
  print("Test")

