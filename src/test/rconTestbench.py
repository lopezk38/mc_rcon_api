from src.rcon.rcon import RconConfig, RconDriver

import traceback

def rconTest():
    print("Loading RCON driver...")

    try:
        conf = RconConfig("0.0.0.0", 25575, "test")
        rconDriver = RconDriver(conf)

    except Exception as e:
        print(f"Failed to load RCON driver due to exception: {e}")
        print(traceback.print_exception(e))
        quit()

    print("Loaded driver successfully\n")

    print("\nTesting checkUpCmd")
    try:
        upOut = rconDriver.checkUpCmd()
        print(f"Got response: {upOut}")

    except Exception as e:
        print(f"Caught exception: {e}")
        print(traceback.print_exception(e))

    print("\nTesting listCmd")
    try:
        listOut = rconDriver.listCmd()
        print(f"Got response: {listOut}")

    except Exception as e:
        print(f"Caught exception: {e}")
        print(traceback.print_exception(e))

    print("\nTesting whitelistAddCmd")
    try:
        wlOut = rconDriver.whitelistAddCmd("test")
        print(f"Got response: {wlOut}")

    except Exception as e:
        print(f"Caught exception: {e}")
        print(traceback.print_exception(e))

    print("\nTesting seedCmd")
    try:
        seedOut = rconDriver.seedCmd()
        print(f"Got response: {seedOut}")

    except Exception as e:
        print(f"Caught exception: {e}")
        print(traceback.print_exception(e))

    print("\nTesting ipCmd")
    try:
        ipOut = rconDriver.ipCmd()
        print(f"Got response: {ipOut}")

    except Exception as e:
        print(f"Caught exception: {e}")
        print(traceback.print_exception(e))

    print("\n\nTests completed")

rconTest()