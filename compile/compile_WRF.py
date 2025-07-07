"""Compile WRF.

Copyright (c) 2025 LATMOS (France, UMR 8190) and IGE (France, UMR 5001).

License: BSD 3-clause "new" or "revised" license (BSD-3-Clause).

"""

import os
import argparse
import json
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


def get_argparser():
    """Return command-line arguments parser."""
    parser = argparse.ArgumentParser(
        description="Compile WRF.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--optfile",
        help="File containing compiling options (JSON format).",
        default=None,
    )
    parser.add_argument(
        "--repository",
        help="Git repository containing the WRF model code.",
        default=cms.URL_WRFCHEMPOLAR,
    )
    parser.add_argument(
        "--destination",
        help="Directory that will host the installation.",
        default="./WRF",
    )
    return parser


def get_options():
    """Get the installation options.

    Command-line arguments have priority over options specified in the
    (optional) option file.

    """
    parser = get_argparser()
    args = parser.parse_args()
    if args.optfile is not None:
        with open(args.optfile) as f:
            args_from_file = json.load(f)
        if not isinstance(args_from_file, dict):
            raise ValueError("Option file must represent a JSON dictionnary.")
        for optname in args_from_file:
            if optname not in args:
                raise ValueError("Unknown option in file: %s." % optname)
        parser.set_defaults(**args_from_file)
        args = parser.parse_args()
    return args


if __name__ == "__main__":

    host = identify_host_platform()
    print("Host platform is: %s" % host)
    print("Options:", get_options())
