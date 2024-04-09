import time
import signal
import subprocess
import time
import os
import sys
import math
from datetime import datetime
from datetime import datetime

keepRunning = True

def signal_handler(sig, frame):
    print("Received Termination signal")
    global keepRunning
    keepRunning = False
    #global process
    #process.send_signal(signal.SIGINT)

from enum import Enum

class SubProcessType(str, Enum):
  INFRASOUND = 'infrasound'
  TEST = 'test'
  GEOPHON = 'geophon'

class InfraService(object):

  def getHourFromString(self, timeStampAsString):
    millies = int(timeStampAsString)
    return int(millies / 1000 / 60 / 60)

  def getSecondCsvPart(self, csvLine):
    return csvLine.split(";")[1]

  def getFileNameForTimeStamp(self, dt_object):
    return (self.dataFolder + format(dt_object.year, '04d') + 
      format(dt_object.month, '02d') + 
      format(dt_object.day, '02d') + 
      "/" + 
      format(dt_object.hour, '02d') + 
      format(dt_object.minute, '02d') + 
      ".csv")
  
  def triggerImageGeneration(self, logFileName):
    subprocess.Popen(["/usr/bin/python3", self.binFolder + "create-images-geophon.py", self.logFileName, self.imageFolder], 
      stdin = None, stdout = None)

  def writeLockFile(self, logFileName):
    lockfile = open(self.dataFolder + "lock", "w", 1)
    lockfile.write(logFileName)
    lockfile.close()

  def writeNextBufferToLogFile(self, buffer, bufferRowCount, isFinalBuffer):
    # open file upon start
    if self.logfile == None:
      startMillies = self.getSecondCsvPart(buffer[0])
      self.startHour = self.getHourFromString(startMillies)
      dt_object = datetime.fromtimestamp(int(startMillies) / 1000)
      self.logFileName = self.getFileNameForTimeStamp(dt_object)
      print("New log file name" + self.logFileName)
      logSubDirName = os.path.dirname(self.logFileName)
      if (not os.path.isdir(logSubDirName)):
        os.mkdir(logSubDirName)
      self.logfile = open(self.logFileName, "w", 1)
      # only write relative path so that its accessable by the webservice as well
      self.writeLockFile(self.logFileName.replace(self.dataFolder, ""))
    # write data
    self.logfile.write("\n".join(buffer))
    self.logfile.write("\n")
    # roll file if necessary
    if isFinalBuffer:
      self.logfile.close()
      self.triggerImageGeneration(self.logFileName)
      return
    endMillies = self.getSecondCsvPart(self.buffer[bufferRowCount])
    endHour =  self.getHourFromString(endMillies)
    if endHour > self.startHour or isFinalBuffer:
      self.logfile.close()
      self.triggerImageGeneration(self.logFileName)
      dt_object = datetime.fromtimestamp(int(endMillies) / 1000)
      self.logFileName = self.getFileNameForTimeStamp(dt_object)
      print("New log file name" + self.logFileName)
      logSubDirName = os.path.dirname(self.logFileName)
      if (not os.path.isdir(logSubDirName)):
        os.mkdir(logSubDirName)
      self.logfile = open(self.logFileName, "w", 1)
      # only write relative path so that its accessable by the webservice as well
      self.writeLockFile(self.logFileName.replace(self.dataFolder, ""))
      self.startHour = endHour

  def __init__(self, subProcessType):
    if subProcessType == None:
        raise "Inavlid subprocess type"
    self.subProcessType = subProcessType
    self.logfile = None
    self.process = None
    self.buffer = [''] * 100
    self.buffer_row = 0
    self.startHour = None
    self.logFileName = None
    self.binFolder = "./"
    self.dataFolder = "../data/"
    self.imageFolder = "../images/"
    self.subProcessTypes = {
      SubProcessType.GEOPHON: ["/usr/bin/python3", self.binFolder + "geophon-continous.py"],
      SubProcessType.INFRASOUND: ["/usr/bin/sensorcontrol"],
      SubProcessType.TEST: ["/usr/bin/python3", self.binFolder + "test.py"]
    }
    self.imageGenerationByType = {
      SubProcessType.GEOPHON: [
        ["/usr/bin/python3", self.binFolder + "create-images.py", "geophon_", "lin"]
      ],
      SubProcessType.TEST: [
        ["/usr/bin/python3", self.binFolder + "create-images.py", "geophon_", "lin"]
      ],
      SubProcessType.INFRASOUND: [
        ["/usr/bin/python3", self.binFolder + "create-images.py", "infra_", "log", "lowerhalf"],
        ["/usr/bin/python3", self.binFolder + "create-images.py", "infra_", "log", "upperhalf"]
      ]
    }


  def work(self):
    subProcessInfo = self.subProcessTypes[self.subProcessType]
    if subProcessInfo == None:
      raise "Invalid sub-process-type " + subProcessType
    global keepRunning
    # global process
    self.process = subprocess.Popen(subProcessInfo, stdin = None, stdout = subprocess.PIPE)
    pipe = self.process.stdout
    while True:
      # handle signals
      if keepRunning == False:
        self.writeNextBufferToLogFile(self.buffer, self.buffer_row, True)
        break
      self.buffer[self.buffer_row] = pipe.readline().decode().rstrip()
      # handle error
      if not self.buffer[self.buffer_row]:
        print("invalid result from process" + self.buffer[self.buffer_row])
        break
      self.buffer_row = self.buffer_row + 1
      if self.buffer_row == 100:
        # do write to logfile or roll logfile
        self.writeNextBufferToLogFile(self.buffer, self.buffer_row - 1, False)
        self.buffer_row = 0
        
    self.logfile.close()
    self.process.send_signal(signal.SIGINT)


if __name__ == "__main__":
  signal.signal(signal.SIGINT, signal_handler)
  print("Infra-Server started")
  subProcessType = sys.argv[1]
  infraServer = InfraService(SubProcessType[subProcessType])
  try:
    infraServer.work()
  except KeyboardInterrupt:
    pass

  print("Infra-Server stopped.")

