try:
    import copy
    import json
    import math
    from typing import Callable

    import flet
    import flet.canvas
    import pynput
except Exception as e:
    imports = {
        "flet": "pip install flet",
        "pynput": "pip install pynput",
    }
    res = ""
    name = str(e).split("'")[1]
    res += str(e)
    if name in imports:
        quit(f"{str(e)}\n\nPlease write [\n{imports[name]}\n] in the command line to install the package")
    quit()