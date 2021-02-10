import logging
import os
import sys


def setup_logging(enable_degbug=False):
    # set up logging to file - see previous section for more details
    logging_level = logging.DEBUG if enable_degbug else logging.INFO
    root_path = os.path.dirname(
        os.path.abspath(sys.modules["__main__"].__file__))
    log_path = os.path.join(root_path, "echo360Downloader.log")
    logging.basicConfig(
        level=logging_level,
        format="[%(levelname)s: %(asctime)s] %(name)-12s %(message)s",
        datefmt="%m-%d %H:%M",
        filename=log_path,
        filemode="w",
    )
    # define a Handler which writes INFO messages or higher to the sys.stderr
    console = logging.StreamHandler()
    console.setLevel(logging_level)
    console.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
    logging.getLogger("").addHandler(console)  # add handler to the root logger
