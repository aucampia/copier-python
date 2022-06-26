import logging
import os
import sys


def test_something() -> None:
    logging.info("entry: ...")
    assert sys.path[0] != os.name
