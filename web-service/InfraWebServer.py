# Python 3 server example
from http.server import BaseHTTPRequestHandler, HTTPServer
import time
import os
import io
import sys
import FrequencyImageGenerator
from urllib.parse import parse_qs 
import numpy as np

hostName = "0.0.0.0"
serverPort = 8080
imageFolder = "../images/"
dataFolder = "../data/"

class InfraWebServer(BaseHTTPRequestHandler):
    geophonFrequency = 100

    def gotoPositionWithTime(self, file, fileLength, desiredStartSecond, frequency):
       # jump by approx 2 seconds
       pageSize = frequency * 16 * 2
       position = pageSize
       while True:
          file.seek(position)
          file.readline()
          pageSecond = self.readNextSecondFromFile(file)
          if pageSecond > desiredStartSecond:
            file.seek(position - pageSize)
            pageSecond = self.readNextSecondFromFile(file)
            break
          position = position + pageSize
          if position > fileLength:
            print("Ups, reached end of file")
            break

    def readNextSecondFromFile(self, file):
       while True:
            linestring = file.readline()
            if linestring.startswith('#'):
               continue
            values = linestring.split(";")
            next_date_value = float(values[1])
            return next_date_value / 1000 
          
    def readDataFromLogFile(self, logFileName, offsetInSeconds, numberInSeconds, frequency):
       desiredSampleNumber = frequency * numberInSeconds
       data = np.empty((2, desiredSampleNumber), np.float64)
       sampleCounter = 0
       absoluteLogFileName = dataFolder + logFileName
       with open(absoluteLogFileName, "r") as f:
          # seek start position
          startSecond = self.readNextSecondFromFile(f)
          f.seek(0) 
          self.gotoPositionWithTime(f, os.path.getsize(absoluteLogFileName), startSecond + offsetInSeconds, frequency)
          while True:
            linestring = f.readline()
            # in case the file ended before the request
            if (linestring == None or linestring == ""):
               print("Reached end of file")
               truncatedData = np.empty((2, sampleCounter - 1), np.float64)
               truncatedData[0] = data[0, :sampleCounter - 1]
               truncatedData[1] = data[1, :sampleCounter - 1]
               return truncatedData
            # in case its not a comment
            if linestring.startswith('#'):
               continue
            values = linestring.split(";")
            next_value = float(values[0])
            next_date_value = float(values[1]) 
            data[0, sampleCounter] = next_value 
            data[1, sampleCounter] = next_date_value
            sampleCounter = sampleCounter + 1
            if (sampleCounter == desiredSampleNumber):
              break
       return data
       
    def generateCurrentImage(self):
        self.send_response(200)
        self.send_header("Content-type", "image/jpg")
        self.end_headers()
        parameters = parse_qs(self.path[self.path.find('?')+1:]) 
        geophon_frequency = int(parameters.get("geophonFrequency", [str(self.geophonFrequency)])[0])
        scale_mode = parameters.get("scaleMode", ["linear"])[0]
        source_transform_factor = float(parameters.get("sourceTransformFactor", ["1.2"])[0])
        clip_min = float(parameters.get("clipMin", ["0"])[0])
        clip_max = float(parameters.get("clipMax", ["60"])[0])
        # self.wfile.write(bytes(str(parameters), "utf-8"))
        currentLogFileName = None
        with open(dataFolder + "lock", "r") as lockfile:
          currentLogFileName = lockfile.readline()

        data_values_buffer = self.readDataFromLogFile(currentLogFileName, 
                                                      int(parameters["offsetSeconds"][0]),
                                                      int(parameters["numberSeconds"][0]),
                                                      geophon_frequency)
        print("Start:" + str(data_values_buffer[1, 0]))
        print("End:" + str(data_values_buffer[1, data_values_buffer[1].size - 1]))

        ft = FrequencyImageGenerator.FrequencyImageGenerator(data_values_buffer[0], 
                                     data_values_buffer[1, 0], 
                                     data_values_buffer[1, data_values_buffer[1].size - 1], 
                                     geophon_frequency,
                                     win_size=parameters["windowSize"][0], 
                                     fft_size=parameters["windowSize"][0],
                                     overlap_fac=float(parameters["overlapFactor"][0]))
        fig = ft.createFrequencyImage(
          scale_mode=scale_mode,
          clip_window=(clip_min, clip_max),
          sensor_scale=source_transform_factor
        )
        #buf = io.BytesIO()
        #fig.savefig(buf, format='png')
        fig.savefig(self.wfile, format='jpg', dpi=250)

       
    def doListFolderStructure(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(bytes("<html><head><title>Geophon Data</title></head>", "utf-8"))
        self.wfile.write(bytes("<body>", "utf-8"))
        path = self.path.replace("/images/", "")
        files = os.listdir(imageFolder + path)
        files.sort()
        for file in files:
          if os.path.isdir(imageFolder + path + "/" + file):
            self.wfile.write(bytes("<a href=\"" + self.path + file + "\">" + file + "</a><br>", "utf-8"))
          else:
            self.wfile.write(bytes("<a href=\"/data" + self.path + "/" + file + "\">" + file + "</a><br>", "utf-8"))
        self.wfile.write(bytes("""<hr/>
                               <form action="/current" target="_blank">
                               <label for="windowSize">Window Size</label><br>
                               <input type="text" name="windowSize" value="2500" list="windowSizeOptions">
                               <datalist id="windowSizeOptions">
                               <option value="2500"></option>
                               <option value="2000"></option>
                               <option value="1500"></option>
                               <option value="1000"></option>
                               </datalist>
                               <br>
                               <label for="geophonFrequency">Geophon Frequency</label><br>
                               <select name="geophonFrequency">
                               <option value="100" selected>100</option>
                               <option value="128">128</option>
                               </select>
                               <br>
                               <label for="overlapFactor">Overlap Factor</label><br>
                               <input type="text" name="overlapFactor" value="0.9">
                               <br> 
                               <label for="numberSeconds">Number of seconds</label><br>
                               <input type="text" name="numberSeconds" value="3600">
                               <br>
                               <label for="offsetSeconds">Offset of seconds</label><br>
                               <input type="text" name="offsetSeconds" value="0">
                               <br>
                               <label for="scaleMode">Scale</label><br>
                               <select name="scaleMode">
                               <option value="linear">Linear</option>
                               <option value="log" selected>Logarithmic</option>
                               </select>
                               <br>
                               <label for="sourceTransformFactor">Source Transformation</label><br>
                               <select name="sourceTransformFactor">
                               <option value="1.2" selected>Infrasound source (1.2)</option>
                               <option value="1.0">No transformation (1.0)</option>
                               </select>
                               <br>
                               <label for="clipMin">Clip Window Min</label><br>
                               <input type="text" name="clipMin" value="0">
                               <br>
                               <label for="clipMax">Clip Window Max</label><br>
                               <input type="text" name="clipMax" value="60">
                               <br>
                               <input type="submit" value="Submit">
                               </form>
                               """, "utf-8"))
        self.wfile.write(bytes("</body></html>", "utf-8"))

    def redirectToImages(self):
      self.send_response(302)
      self.send_header('Location', '/images/')
      self.end_headers() 
     
    def doDownloadFile(self):
      self.send_response(200)
      self.send_header('Content-type', 'image/jpg')
      self.end_headers()
      with open(self.path.replace("/data/images/", imageFolder), 'rb') as f:
        self.wfile.write(f.read())

    def do_GET(self):
        if self.path == '/':
          self.redirectToImages()
        if self.path.startswith("/images/"):
          self.doListFolderStructure()
        elif self.path.startswith("/data/images/"):
          self.doDownloadFile()
        elif self.path.startswith("/current?"):
          self.generateCurrentImage()
        else:
          self.send_response(404)
          self.send_header("Content-type", "text/html")
          self.end_headers()
          self.wfile.write(bytes("<html><head><title>Not found</title></head>", "utf-8"))
          self.wfile.write(bytes("<body>", "utf-8"))
          self.wfile.write(bytes("<p>Not found." + self.path + "</p>", "utf-8"))
          self.wfile.write(bytes("</body></html>", "utf-8"))

if __name__ == "__main__":
    serverPort = int(sys.argv[1])        
    webServer = HTTPServer((hostName, serverPort), InfraWebServer)
    print("Server started http://%s:%s" % (hostName, serverPort))

    try:
        webServer.serve_forever()
    except KeyboardInterrupt:
        pass

    webServer.server_close()
    print("Server stopped.")
