#!/usr/bin/env python3
"""PC-41 original-ROM continuation: unchanged PC-34 prefix and
historical PC-40 pre-ADC checkpoint checked by the native observer.

Final new run golden is pinned after independently observing CI output.
"""
import json
from pathlib import Path
import sys

from verify_pc40_route import verify

def check(*files):
    verify(*files,milestone="pc41")

if __name__=="__main__":
    try:
        if len(sys.argv)!=5:
            raise ValueError("usage: verify_pc41_route.py SOURCE.sms "
                             "PC41-source.json PC41-route.json PC34.json")
        check(*sys.argv[1:])
    except (AssertionError,ValueError,KeyError,TypeError,OSError) as error:
        sys.exit("FAIL PC-41 source route: "+str(error))
