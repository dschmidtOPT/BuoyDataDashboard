
import pandas as pd
import ais.stream
import datetime
import serial
import yaml
import sys
import io
import os
import time
from pynmeagps import NMEAReader
from numpy import nan

class MessageLib:
    keys = set()

class COM:
    def __init__( self, name, thisAsset, bufflim = 10 ):
        self.name = name
        self.data = []
        with open("./config/ports.yaml") as f:
            self.port = yaml.safe_load(f)[ thisAsset ][ name ]
        if "ais" in name:
            return self.readAISPort( bufflim )
        elif "gps" in name:
            return self.readGPSPort( bufflim )
        
    def readAISPort(self, bufflim, verbose = False):
        read = 0
        self.data = pd.DataFrame(
            {key: [] for key in ['tlast','mmsi','name','pos','cog','sog']
             },
            dtype=object)
        with serial.Serial (self.port['path'],
                            self.port['baud'],
                            timeout=5) as ser:
            buffer = io.StringIO("")
            estimate = bufflim/self.port['pubHZ']
            if verbose:
                print(f"Seeding {bufflim} AIS message to start plot, should take ~{estimate}s.")
            while read <= bufflim:
                time.sleep(0.25)
                x = ser.readline()
                x = x.decode("utf-8")
                buffer.write(x)
                if not x:
                    continue
                for msg in ais.stream.decode( buffer.getvalue().split("\n") ):
                    if 'x' not in msg.keys():
                        continue
                    elif msg['x'] == 181:
                        continue
                    if 'cog' not in msg.keys():
                        msg['cog'] = None
                        msg['sog'] = None
                    if 'name' not in msg.keys():
                        msg['name'] = "Unknown"
                    self.data.loc[ len(self.data) ] = [
                        datetime.datetime.now(),
                        msg['mmsi'],
                        msg['name'],
                        [msg['y'],msg['x']],
                        msg['cog'],
                        msg['sog']]
                buffer.flush()
                read += 1
            return self.data

    def readGPSPort(self, bufflim, verbose = False):
        read = 0
        stream = serial.Serial( self.port['path'],
                                self.port['baud'],
                                timeout=3)
        estimate = bufflim/self.port['pubHZ']
        if verbose:
            print(f"Seeding {bufflim} GPS message to start plot, should take ~{estimate}s.")
        nmr = NMEAReader(stream)
        loop = True
        lat = []
        lon = []
        tstamp = []
        cog = []
        while read < bufflim:
            (raw_data, parsed_data) = nmr.read()
            if "cog" in dir(parsed_data): 
                self.data.append(
                    {'lat': parsed_data.lat,
                      "lon": parsed_data.lon,
                      "cog": parsed_data.cog,
                      "tstamp": parsed_data.time}
                    )
                read += 1 
        if bufflim == 1:
            print( f'Initial asset lat - long position is \n\t{self.data[0]["lat"]}N, {self.data[0]["lon"]}W, cog = {self.data[0]["cog"]}deg' )            
        return self.data
        
            
    def writeConverted( outName, buff_name):
        ''' Write buffer to specified position '''
        with open(buff_name,"r") as f:
            raw = f.readlines()
        switch = True
        for msg in ais.stream.decode( raw ):
            keys = [key for key in list(msg.keys())]
        sub = ''
        for key in keys:
            sub += str(key) +": " + str(msg[key]) +  ','
        os.system(f"echo '{sub}' >> {outName}")

    def flush(self):
        del self.data
        self.data = []


class GPS( COM ):
    def __init__(self, thisAsset, bufflim = 1):
        super().__init__( 'gps', thisAsset, bufflim)
        return

class AIS( COM ):
    def __init__( self, thisAsset, bufflim = 10 ):
        super().__init__( 'ais', thisAsset, bufflim);
        return 

    


if __name__ == "__main__":
    ## If running convertPort as a standalone script ##
    COM.readPort('/dev/ttyUSB3',  "AIS", baud = 38400, bufflim = 10 )

