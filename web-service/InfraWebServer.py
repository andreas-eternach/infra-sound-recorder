# Python 3 server example
from http.server import BaseHTTPRequestHandler, HTTPServer
import time
import os

hostName = "0.0.0.0"
serverPort = 8080
imageFolder = "../images/"

class InfraWebServer(BaseHTTPRequestHandler):
    def doListFolderStructure(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(bytes("<html><head><title>Geophon Data</title></head>", "utf-8"))
        self.wfile.write(bytes("<body>", "utf-8"))
        path = self.path.replace("/images/", "")
        for file in os.listdir(imageFolder + path):
          if os.path.isdir(imageFolder + path + "/" + file):
            self.wfile.write(bytes("<a href=\"/" + self.path + "/" + file + "\">" + file + "</a><br>", "utf-8"))
          else:
            self.wfile.write(bytes("<a href=\"/data" + self.path + "/" + file + "\">" + file + "</a><br>", "utf-8"))
        self.wfile.write(bytes("</body></html>", "utf-8"))

    def doDownloadFile(self):
      self.send_response(200)
      self.send_header('Content-type', 'image/jpg')
      self.end_headers()
      with open(self.path.replace("/data/images/", imageFolder), 'rb') as f:
        self.wfile.write(f.read())

    def do_GET(self):
        if self.path == '/' or self.path.startswith("/images/"):
          self.doListFolderStructure()
        elif self.path.startswith("/data/images/"):
          self.doDownloadFile()
        else:
          self.send_response(404)
          self.send_header("Content-type", "text/html")
          self.end_headers()
          self.wfile.write(bytes("<html><head><title>Not found</title></head>", "utf-8"))
          self.wfile.write(bytes("<body>", "utf-8"))
          self.wfile.write(bytes("<p>Not found.</p>", "utf-8"))
          self.wfile.write(bytes("</body></html>", "utf-8"))

if __name__ == "__main__":        
    webServer = HTTPServer((hostName, serverPort), InfraWebServer)
    print("Server started http://%s:%s" % (hostName, serverPort))

    try:
        webServer.serve_forever()
    except KeyboardInterrupt:
        pass

    webServer.server_close()
    print("Server stopped.")
