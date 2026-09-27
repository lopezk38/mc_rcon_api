"""
Cached Rcon Module - Caching wrapper for RCON module to reduce server load

Kenneth Lopez 2026 lopezk38@gmail.com

"""

from mc_rcon_api.src.rcon.rcon import RconDriver, RconConfig

import time

"""
CachedRconDriver - Wrapper class for RconDriver which caches requests for performance

    Available commands:
        checkUpCmd - Checks if MC server is reachable
        listCmd - Queries MC server for players online
        whitelistAddCmd - Adds the given player to the MC server's whitelist
        seedCmd - Queries the MC server for it's world seed
        ipCmd - Returns the MC server's external IP (usually)

"""
class CachedRconDriver:
    """
    CachedRconDriver default constructor - Loads parameters stored in environment vars or a config file
        If both valid environment vars and a config file are present, the environment vars will be used

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
        expTime: int | float (Optional, default 5 seconds) - Cached value lifetime in seconds
        rconConfig: RconConfig - RCON driver config dataclass to conform to

    Raises:
        ValueError if expTime is negative
        TypeError if expTime is not a number or rconConfig is not of type RconConfig or a descendent thereof

    """
    def __init__(self, expTime: int | float = 5, rconConfig: RconConfig = None):
        if type(expTime) is not int and type(expTime is not float):
            raise TypeError("Invalid expiration time type")

        if expTime < 0:
            raise ValueError("Expiration time must be a non-negative integer")

        if rconConfig is None:
            self._driver = RconDriver()

        elif not isinstance(rconConfig, RconConfig):
            raise TypeError("Invalid RCON config type")

        else:
            self._driver = RconDriver(rconConfig)

        self.cacheExpirationTime = expTime

        self._checkUpLUT = -1
        self._listLUT = -1
        self._seedCmdLUT = -1
        self._ipCmdLUT = -1

        self._checkUpCache = None
        self._listCache = None
        self._seedCmdCache = None
        self._ipCmdCache = None


    """
    checkUpCmd - Checks if the MC server is reachable or shut down

    Returns Boolean, True if up and False if down

    """
    def checkUpCmd(self):
        curTime = time.monotonic()

        if curTime - self._checkUpLUT > self.cacheExpirationTime or self._checkUpCache is None:
            # Cache is expired or uninitialized, hit server
            result = self._driver.checkUpCmd()
            self._checkUpCache = result
            self._checkUpLUT = time.monotonic()
            return result

        else:
            # Cache hit
            return self._checkUpCache

    """
    listCmd - Requests the names of online players on the MC server

    Returns a list<str> containing all online player names. Empty list if no players are on

    Raises:
        RuntimeError if the server is unreachable or if it returns a bad/unparsable response

    """
    def listCmd(self):
        curTime = time.monotonic()

        if curTime - self._listLUT > self.cacheExpirationTime or self._listCache is None:
            # Cache is expired or uninitialized, hit server
            result = self._driver.listCmd()
            self._listCache = result
            self._listLUT = time.monotonic()
            return result

        else:
            # Cache hit
            return self._listCache
        
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
        # Can't cache a write
        return self._driver.whitelistAddCmd(playerName)
        
    """
    seedCmd - Returns the server's seed value
        Currently is a hardcoded value

    Returns str containing the seed

    """
    def seedCmd(self):
        curTime = time.monotonic()

        if curTime - self._seedCmdLUT > self.cacheExpirationTime or self._seedCmdCache is None:
            # Cache is expired or uninitialized, hit server
            result = self._driver.seedCmd()
            self._seedCmdCache = result
            self._seedCmdLUT = time.monotonic()
            return result

        else:
            # Cache hit
            return self._seedCmdCache
            
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
        curTime = time.monotonic()

        if curTime - self._ipCmdLUT > self.cacheExpirationTime or self._ipCmdCache is None:
            # Cache is expired or uninitialized, hit server
            result = self._driver.ipCmd()
            self._ipCmdCache = result
            self._ipCmdLUT = time.monotonic()
            return result

        else:
            # Cache hit
            return self._ipCmdCache