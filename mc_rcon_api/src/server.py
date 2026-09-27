from mc_rcon_api.src.rcon.cachedRcon import CachedRconDriver

import traceback
import uvicorn

from fastapi import FastAPI, HTTPException

rconDriver = CachedRconDriver()
app = FastAPI()


@app.get("/api/mcrcon/status")
async def getServerStatus():
    try:
        result = rconDriver.checkUpCmd()
        return {"status": result}

    except Exception as e:
        print(f"ERROR: Caught exception {e} while serving server status")
        print(traceback.print_exception(e))

        raise HTTPException(status_code=500, detail="Admin check server console for details")

@app.get("/api/mcrcon/list")
async def getOnlinePlayers():
    try:
        result = rconDriver.listCmd()
        return {"onlinePlayers": result}

    except Exception as e:
        print(f"ERROR: Caught exception {e} while serving player list")
        print(traceback.print_exception(e))

        raise HTTPException(status_code=500, detail="Admin check server console for details")

@app.put("/api/mcrcon/whitelist/add/{name}")
async def addToWhitelist(name: str):
    try:
        result = rconDriver.whitelistAddCmd(name).value # This func returns an enum, cast to int
        return {"status": result}

    except Exception as e:
        print(f"ERROR: Caught exception {e} while adding player to whitelist")
        print(traceback.print_exception(e))

        raise HTTPException(status_code=500, detail="Admin check server console for details")

@app.get("/api/mcrcon/seed")
async def getSeed():
    try:
        result = rconDriver.seedCmd()
        return {"seed": result}

    except Exception as e:
        print(f"ERROR: Caught exception {e} while serving server seed")
        print(traceback.print_exception(e))

        raise HTTPException(status_code=500, detail="Admin check server console for details")

@app.get("/api/mcrcon/serverip")
async def getServerIP():
    try:
        result = rconDriver.ipCmd()
        return {"serverIP": result}

    except Exception as e:
        print(f"ERROR: Caught exception {e} while serving server IP")
        print(traceback.print_exception(e))

        raise HTTPException(status_code=500, detail="Admin check server console for details")



def start():
    uvicorn.run("mc_rcon_api.src.server:app", host='0.0.0.0', port=8000, reload=True)