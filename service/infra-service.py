import time
import signal
import subprocess
import time
import os
import math
from datetime import datetime
from datetime import datetime

keepRunning = True

binFolder = "./"
dataFolder = "../data/"
imageFolder = "../images/"

def signal_handler(sig, frame):
    global keepRunning
    keepRunning = False
    global process
    process.send_signal(signal.SIGINT)
    time.sleep(1)
    global logfile
    logfile.close()
    exit(0)

def getHourFromString(timeStampAsString):
  millies = int(timeStampAsString)
  return int(millies / 1000 / 60 / 60)

def getSecondCsvPart(csvLine):
  return csvLine.split(";")[1]

def getFileNameForTimeStamp(dt_object):
  # TODO: Create children folder for each day
  return (dataFolder + format(dt_object.year, '04d') + 
    format(dt_object.month, '02d') + 
    format(dt_object.day, '02d') + 
    "/" + 
    format(dt_object.hour, '02d') + 
    format(dt_object.minute, '02d') + 
    ".csv")
  
def triggerImageGeneration(logFileName):
  process = subprocess.Popen(["/usr/bin/python3", binFolder + "create-images-geophon.py", logFileName, imageFolder], 
    stdin = None, stdout = None)

def writeLockFile(logFileName):
  lockfile = open(dataFolder + "lock", "w", 1)
  lockfile.write(logFileName)
  lockfile.close()

def writeNextBufferToLogFile(buffer):
  global logfile
  global startHour
  global logFileName
  # open file upon start
  if logfile == None:
    startMillies = getSecondCsvPart(buffer[0])
    startHour = getHourFromString(startMillies)
    dt_object = datetime.fromtimestamp(math.ceil(int(startMillies) / 1000))
    logFileName = getFileNameForTimeStamp(dt_object)
    print("New log file name" + logFileName)
    logSubDirName = os.path.dirname(logFileName)
    if (not os.path.isdir(logSubDirName)):
        os.mkdir(logSubDirName)
    logfile = open(logFileName, "w", 1)
    # only write relative path so that its accessable by the webservice as well
    writeLockFile(logFileName.replace(dataFolder, ""))
  # roll file if necessary
  endMillies = getSecondCsvPart(buffer[99])
  endHour =  getHourFromString(endMillies)
  if endHour > startHour:
    logfile.close()
    triggerImageGeneration(logFileName)
    dt_object = datetime.fromtimestamp(int(endMillies) / 1000)
    logFileName = getFileNameForTimeStamp(dt_object)
    print("New log file name" + logFileName)
    logSubDirName = os.path.dirname(logFileName)
    if (not os.path.isdir(logSubDirName)):
        os.mkdir(logSubDirName)
    logfile = open(logFileName, "w", 1)
    # only write relative path so that its accessable by the webservice as well
    writeLockFile(logFileName.replace(dataFolder, ""))
    startHour = endHour
  # write data
  logfile.write("\n".join(buffer))
  logfile.write("\n")

signal.signal(signal.SIGINT, signal_handler)
# global process
logfile = None
process = subprocess.Popen(["/usr/bin/python3", binFolder + "geophon-continous.py"], stdin = None, stdout = subprocess.PIPE)
pipe = process.stdout
buffer = [''] * 100
buffer_row = 0
while True:
  # handle signals
  if keepRunning == False:
    break
  buffer[buffer_row] = pipe.readline().decode().rstrip()
  # handle error
  if not buffer[buffer_row]:
    print("invalid result from process" + buffer[buffer_row])
    break
  buffer_row=buffer_row + 1
  if buffer_row == 100:
    # do write to logfile or roll logfile
    writeNextBufferToLogFile(buffer)
    buffer_row = 0
    
logfile.close()
process.send_signal(signal.SIGINT)
