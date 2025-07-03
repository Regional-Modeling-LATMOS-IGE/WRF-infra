"""Compile WRF.

Copyright (c) 2025 LATMOS (France, UMR 8190) and IGE (France, UMR 5001).

License: BSD 3-clause "new" or "revised" license (BSD-3-Clause).

"""

import os
import commons as cms

def identify_host_platform():
    """Return a character string that identifies the host platform."""
    known_plateforms = {
        "spirit1.ipsl.Fr": "spirit",
        "spirit2.ipsl.fr": "spirit",
    }
    nodename = os.uname().nodename
    try:
        platform = known_plateforms[nodename]
    except KeyError:
        raise NotImplementedError("Unknown host platform: %s." % nodename)
    return platform

def get_options(filepath):
    opts = dict(
        repo=cms.URL_WRFCHEMPOLAR,
    )

if __name__ == "__main__":

    host = identify_host_platform()
    print("Host platform is: %s" % host)
