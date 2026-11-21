import socket
import json

#Using the Static IP assiged to pico
PICO_IP = '10.42.0.178'
PORT = 5000

class pico_client:
    def __init__(self):
        self.picodata = None
        self.fileobj = None
        self.pico_connect()

    def pico_connect(self):
        try:
            if self.picodata:
                self.picodata.close()
            self.picodata = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.picodata.settimeout(2.0)
            self.picodata.connect((PICO_IP, PORT))
            # makefile gives us readline() which reads exactly up to \n
            self.fileobj = self.picodata.makefile('r')
            print("Connected to Pico")
        except Exception as e:
            print(f"Connection failed: {e}")
            self.picodata = None
            self.fileobj = None

def getPicoData(self):
    try:
        if self.fileobj is None:
            self.pico_connect()
            return None
        line = self.fileobj.readline() # reads exactly one \n-terminated line
        if not line:
            raise ConnectionError("Socket closed")
        return json.loads(line)
    except Exception as e:
        print(f"Error: {e} — reconnecting...")
        self.picodata = None
        self.fileobj = None
        return None