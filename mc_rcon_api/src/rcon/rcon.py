"""
Rcon Module - Abstraction layer which drives and constrains mcrcon, an executable
    which implements MC's RCON protocol

Kenneth Lopez 2026 lopezk38@gmail.com

"""

import json
import random
import subprocess
import re
import requests
import copy
import os

from ipaddress import ip_address
from enum import Enum
from pathlib import Path

"""
Dataclass to carry and validate connection parameters for the RconDriver class

"""
class RconConfig:

    """
    RconConfig Constructor - Accepts and validates connection parameters

    Args:
        serverRconIP: str - IP address to the MC server to make a connection to
        serverRconPort: int - RCON Port to the MC server
        serverRconPW: str - MC server's RCON password. Pass empty string for no PW (inadvisable)
    
    Raises:
        ValueError - If any of the given parameters are None or fail validation

    """
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
            if serverRconIP.lower().replace(' ', '') == 'localhost':
                serverRconIP = '0.0.0.0'

            else:
                print(f"Bad IP address for RCON given: {serverRconIP}")
                raise ValueError("Bad RCON IP")

        if type(serverRconPort) is not int:
            print("Given RCON port is not an integer")
            raise ValueError("Invalid RCON port")

        if serverRconPort < 0 or serverRconPort > 65535:
            print(f"Out of range port for RCON given: {serverRconPort}")
            raise ValueError("Out of range RCON port")

        if type(serverRconPW) is not str:
            print(f"Bad password for RCON given")
            raise ValueError("Bad RCON PW")

        self.serverRconIP = serverRconIP
        self.serverRconPort = serverRconPort
        self.serverRconPW = serverRconPW

        self.rconDep = Path(__file__).resolve().parent.parent.parent / 'deps' / 'mcrcon'

"""
RconDriver - Implements an interface for calling mcrcon safely

    Available commands:
        checkUpCmd - Checks if MC server is reachable
        listCmd - Queries MC server for players online
        whitelistAddCmd - Adds the given player to the MC server's whitelist
        seedCmd - Queries the MC server for it's world seed
        ipCmd - Returns the MC server's external IP (usually)

"""
class RconDriver:
    class ErrCode(Enum):
        SUCCESS = 0
        BAD_NAME = 1
        ALREADY_EXISTS = 2
        UNKNOWN = -1

    """
    RconDriver constructor - Loads given parameters or those stored in environment vars or a config file
        If rconConfig parameter is used, those parameters will be used. Otherwise, if both valid environment
        vars and a config file are present, the environment vars will be used

        The following environment vars should be used if not using a config file:
            MC_RCON_ADDR
            MC_RCON_PORT
            MC_RCON_PW

        Config file should be located in the config/rcon_config.json file if desired.
        Config file should have the following keys in any order:
            rconIP (string)
            rconPort (integer)
            rconPW (string)

    Args:
        rconConfig: RconConfig (Optional) - Config to use, overriding env vars or config files

    """
    def __init__(self, rconConfig: RconConfig = None):
        if rconConfig is None:
            self._config = self._loadSettings()
            
        else:
            self._config = copy.deepcopy(rconConfig)


    """
    checkUpCmd - Checks if the MC server is reachable or shut down

    Returns Boolean, True if up and False if down

    """
    def checkUpCmd(self):
        #Call version and see if we get a response
        try:
            output = subprocess.run([self._config.rconDep, 
                                        "-H", str(self._config.serverRconIP),
                                        "-P", str(self._config.serverRconPort),
                                        "-p", str(self._config.serverRconPW), "version"], 
                                        check=True, capture_output=True, text=True)
            
        except subprocess.CalledProcessError as e:
            #Server is down
            return False
            
        #If we got here, server is up
        return True

    """
    listCmd - Requests the names of online players on the MC server

    Returns a list<str> containing all online player names. Empty list if no players are on

    Raises:
        RuntimeError if the server is unreachable or if it returns a bad/unparsable response

    """
    def listCmd(self):
        #Call list
        output = None
        try:
            output = subprocess.run([self._config.rconDep,
                                        "-H", str(self._config.serverRconIP),
                                        "-P", str(self._config.serverRconPort),
                                        "-p", str(self._config.serverRconPW), "list"],
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
        
    """
    whitelistAddCmd - Validates and adds the given account name to the server whitelist

    Args:
        playerName: str - The name of the account to add to the whitelist
            Must be between 3 and 16 characters long
            Must contain only chars which are allowed for a valid account name

    Returns RconDriver.ErrCode enum value specifying the result
        ErrCode.SUCCESS if succeeded
        ErrCode.ALREADY_EXISTS if the account is already on the whitelist
        ErrCode.BAD_NAME if the given name failed validation or is not a real account name
        ErrCode.UNKNOWN if the server's response could not be parsed. New whitelist state
            becomes unknown

    Raises:
        RuntimeError if the server could not be reached or gives a bad response

    """
    def whitelistAddCmd(self, playerName: str):  
        if (len(playerName) < 3):
            #Name is too short
            return self.ErrCode.BAD_NAME
        
        if (len(playerName) > 16):
            #Name is too long
            return self.ErrCode.BAD_NAME
        
        #Sanitize name
        matches = re.findall('([A-z]|\\d|_)', playerName[0:16])
        name = ''.join(matches)
        print("Sanitized name for whitelist: " + name)
        
        if (len(name) != len(playerName)):
            #Name had bad chars in it. Reject
            return self.ErrCode.BAD_NAME
        
        #Run whitelist add
        output = None
        try:
            output = subprocess.run([self._config.rconDep,
                                        "-H", str(self._config.serverRconIP),
                                        "-P", str(self._config.serverRconPort),
                                        "-p", str(self._config.serverRconPW),
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
            return self.ErrCode.SUCCESS
            
        else:
            match = re.match("Player is already whitelisted", respStr)
            if (match is not None):
                #Already whitelisted
                return self.ErrCode.ALREADY_EXISTS
                
            else:
                match = re.match("That player does not exist", respStr)
                if (match is not None):
                    #Invalid name
                    return self.ErrCode.BAD_NAME
                    
                else:
                    #Unknown response from server. New state is indeterminable, may or not have succeeded
                    print(f"WARNING: Got unrecognized whitelist response from server: {respStr}")
                    return self.ErrCode.UNKNOWN
        
        assert False, 'Whitelist add command reached impossible instruction, halting'
        
    """
    seedCmd - Returns the server's seed value
        Currently is a hardcoded value

    Returns str containing the seed

    """
    def seedCmd(self):
        return "2055796538" #TODO fetch from server instead of hardcoding
            
    """
    ipCmd - Returns the IP address for the MC server
        If MC server is running on the same machine as this program (aka if RCON IP is 0.0.0.0/localhost)
            the machine's external IP will be queried using Akamai's IP service
            Otherwise, it just returns the RCON IP hoping it's an external IP since we don't have
                code execution on the MC server machine to query it's external IP

    Returns str containing the IP address for the MC server (see above note)

    Raises:
        RuntimeError if Akamai could not be reached
        ValueError if Akamai could be reached but gave an invalid response

    """
    def ipCmd(self):
        if self._config.serverRconIP == '0.0.0.0':
            # Server is on the same machine, need to get external IP
            # Get IP from akamai
            resp = None
            try:
                resp = requests.get("http://whatismyip.akamai.com")
                if (resp is None): raise ValueError("Got invalid response from Akamai")

            except:
                raise RuntimeError("Could not reach Akamai")
            
            #Validate response
            ipRaw = resp.text[:15]
            match = re.match('^\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}.\\d{1,3}$', ipRaw)
            
            if (match is None):
                print("WARNING: Got invalid IP from Akamai: " + ipRaw)
                raise ValueError("Got invalid response from Akamai")
            
            #IP validated, send it
            print("Got external IP from Akamai: " + match.group(0))
            
            return match.group(0) # str containing IP

        else:
            # Server is on an external machine, best we can do is return the RCON IP
            return self._config.serverRconIP;
        

    """
    _loadSettings - Private function which is used to load environment variables or config file values
        You should never need to call this

    Args:
        path: Path - Path to look for the config file. Optional parameter
            By default, looks for a config file at config/rcon_config.json

    Raises:
        FileNotFoundError if no environment vars could be found and a config file also could not be found
        ValueError if config file is missing keys or contains invalid values
            If you get this while you were trying to use environment variables, they also could either
            not be found or failed validation

    """
    def _loadSettings(self, path: Path = None):
        #Attempt to retrieve from env vars
        try:
            settingsObj = RconConfig(os.getenv("MC_RCON_ADDR", None), os.getenv("MC_RCON_PORT", None), os.getenv("MC_RCON_PW", None))

        except (ValueError, KeyError):
            print("RCON env vars not present or invalid, looking for config json...")

        #Load JSON file
        if path is None:
            path = Path(__file__).resolve().parent.parent.parent / 'config' / 'rcon_config.json'

        try:
            file = open(path)
            
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