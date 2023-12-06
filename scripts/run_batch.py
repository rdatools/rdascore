#!/usr/bin/env python3

"""

DEBUG DISTRICT SHAPE CREATION

To run:

$ scripts/run_batch.py

"""

import os
from typing import List

from rdadata import data_dir
from rdafn import *

states: List[str] = [
    "SC",
    "NM",
    "AL",
    "GA",
    "PA",
    "MI",
    "OH",
    "MD",
    "WI",
    "TX",
    "VA",
    "IL",
    "FL",
]

for xx in states:
    full_path: str = os.path.expanduser(f"{data_dir}/{xx}/{xx}_2020_metadata.json")
    command: str = f"rm {full_path}"
    print(command)
    os.system(command)


### END ###
