import json
import random
import subprocess
import re
import requests
import copy
import os

from ipaddress import ip_address
from enum import Enum

class RconConfig:
    def __init__(self, serverRconIP: str, serverRconPort: int, serverRconPW: str):
        if serverRconIP is None:
            raise ValueError("Given RCON IP is None")

        if serverRconPort is None:
            raise ValueError("Given RCON port is None")

        if serverRconPW is None:
            raise ValueError("Given RCON PW is None")

        try:
            ip_address(serverRconIP)

        except ValueError:
            print(f"Bad IP address for RCON given: {serverRconIP}")
            raise ValueError("Bad RCON IP")

        if serverRconPort < 0 or serverRconPort 65535:
            print(f"Bad port for RCON given: {serverRconPort}")
            raise ValueError("Bad RCON port")

        if serverRconPW is not str:
            print(f"Bad password for RCON given")
            raise ValueError("Bad RCON PW")

        self.serverRconIP = serverRconIP
        self.serverRconPort = serverRconPort
        self.serverRconPW = serverRconPW

        self.rconDep = '../../deps/mcrcon'


class RconDriver:
    class ErrCode(Enum):
        SUCCESS = 0
        BAD_NAME = 1
        ALREADY_EXISTS = 2
        UNKNOWN = -1

    def __init__(self):
        self._config = self._loadSettings()

    def __init__(self, rconConfig: RconConfig):
        self._config = copy.deepcopy(rconConfig)


    def checkUpCmd():
        #Call version and see if we get a response
        try:
            output = subprocess.run([self._config.rconDep, 
                                        "-H", self._config.serverRconIP,
                                        "-P", self._config.serverRconPort,
                                        "-p", self._config.serverRconPW, "version"], 
                                        check=True, capture_output=True, text=True)
            
        except subprocess.CalledProcessError as e:
            #Server is down
            return False
            
        #If we got here, server is up
        return True

    def listCmd():
        #Call list
        output = None
        try:
            output = subprocess.run([self._config.rconDep,
                                        "-H", self._config.serverRconIP,
                                        "-P", self._config.serverRconPort, "-p",
                                        self._config.serverRconPW, "list"],
                                        check=True, capture_output=True, text=True)
            
        except subprocess.CalledProcessError as e:
            #Server is down
            raise RuntimeError("Could not reach MC server")
            
        if (output is None):
            raise RuntimeError("Reached MC Server but got bad response")
        
        listStr = output.stdout
        
        #Validate response prefix
        print(f"Got reply from server for list: {listStr}")
        match = re.match("There are \\d* of a max of \\d* players online:", listStr)
        
        if (match is None):
            print("WARNING: Failed to find list data in response from server")
            raise RuntimeError("Reached MC Server but got bad response")
        
        #Isolate player names to comma seperated string
        players = listStr[len(match.group(0)):-5]
        if (len(players) < 2):
            #No players online
            return []

        #Tokenize string to isolate player names
        playerList = players.replace(' ', '').split(',')   

        return playerList;
        
    def whitelistAddCmd(playerName: str):  
        if (len(playerName) < 3):
            #Name is too short
            raise ValueError("Name is too short")
        
        if (len(playerName) > 16):
            #Name is too long
            raise ValueError("Name is too long")
        
        #Sanitize name
        matches = re.findall('([A-z]|\\d|_)', playerName[0:16])
        name = ''.join(matches)
        print("Sanitized name for whitelist: " + name)
        
        if (len(name) != len(rawName)):
            #Name had bad chars in it. Reject
            raise ValueError("Rejected name")
        
        #Run whitelist add
        output = None
        try:
            output = subprocess.run([self._config.rconDep,
                                        "-H", self._config.serverRconIP,
                                        "-P", self._config.serverRconPort,
                                        "-p", self._config.serverRconPW,
                                        (f"whitelist add {name}")],
                                        check=True, capture_output=True, text=True)
            
        except subprocess.CalledProcessError as e:
            #Server is down
            raise RuntimeError("Could not reach MC server")
            
        if (output is None):
            raise RuntimeError("Reached MC Server but got bad response")
        
        respStr = output.stdout
        
        #Classify response and reply appropriately
        print(f"Got reply from server for whitelist add: {respStr}")
        
        match = re.match("Added .* to the whitelist", respStr)
        if (match is not None):
            #Success
            return self.ErrCodes.SUCCESS
            
        else:
            match = re.match("Player is already whitelisted", respStr)
            if (match is not None):
                #Already whitelisted
                return self.ErrCodes.ALREADY_EXISTS
                
            else:
                match = re.match("That player does not exist", respStr)
                if (match is not None):
                    #Invalid name
                    return self.ErrCodes.BAD_NAME
                    
                else:
                    #Unknown response from server. New state is indeterminable, may or not have succeeded
                    print(f"WARNING: Got unrecognized whitelist response from server: {respStr}")
                    return self.ErrCodes.UNKNOWN
        
        assert False, 'Whitelist add command reached impossible instruction, halting'
        
    def seedCmd():
        return "2055796538" #TODO fetch from server instead of hardcoding
            
    def ipCmd():
        #Get IP from akamai
        resp = None
        try:
            resp = requests.get("http://whatismyip.akamai.com")
            if (resp is None): raise ValueError("Got invalid response from Akamai")
        
        #Validate response
        ipRaw = resp.text[:15]
        match = re.match('^\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}.\\d{1,3}$', ipRaw)
        
        if (match is None):
            print("WARNING: Got invalid IP from Akamai: " + ipRaw)
            raise ValueError("Got invalid response from Akamai")
        
        #IP validated, send it
        print("Got external IP from Akamai: " + match.group(0))
        
        return match.group(0) # str containing IP
        

    def _loadSettings(pathStr: str = '../../config/rcon_config.json'):
        #Attempt to retrieve from env vars
        try:
            settingsObj = RconConfig(os.getenv("MC_RCON_ADDR", None), os.getenv("MC_RCON_PORT", None), os.getenv("MC_RCON_PW", None))

        except (ValueError, KeyError):
            print("RCON env vars not present or invalid, looking for config json...")

        #Load JSON file
        try:
            file = open(pathStr)
            
        except:
            print("Failed to open RCON settings file")
            raise FileNotFoundError("No RCON settings file found")
        
        jsonStr = file.read()
        file.close()
        
        #Parse JSON
        try:
            loadedSettingsObj = json.loads(jsonStr)

        except json.JSONDecodeError:
            print ("Failed to parse loaded RCON settings file")
            raise ValueError("Bad RCON settings JSON")
        
        #Attempt to extract all settings from it           
        try:
            settingsObj = RconConfig(loadedSettingsObj["rconIP"], loadedSettingsObj["rconPort"], loadedSettingsObj["rconPW"])
            
        except ValueError:
            print("RCON settings file was parsed but contained invalid data")
            raise ValueError("Bad RCON settings JSON")

        except KeyError as e:
            print(f"RCON settings file was parsed but is missing '{e.args[0]}' field")
            raise ValueError("Bad RCON settings JSON")
        
        return settingsObj