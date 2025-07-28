"""Common resources for compilation scripts.

Copyright (c) 2025 LATMOS (France, UMR 8190) and IGE (France, UMR 5001).

License: BSD 3-clause "new" or "revised" license (BSD-3-Clause).

"""

import argparse

URL_GITHUB = "https://github.com"
URL_GROUP = "%s/Regional-Modeling-LATMOS-IGE" % URL_GITHUB
URL_WRFCHEMPOLAR = "%s/WRF-Chem-Polar.git" % URL_GROUP


class ConvertToBoolean(argparse.Action):
    """Action to convert command-line arguments to booleans."""

    def __call__(self, parser, namespace, values, option_string=None):
        """Convert command line option value to boolean.

        See https://docs.python.org/3/library/argparse.html#action-classes for
        more details about action classes and the corresponding API.

        """
        while option_string.startswith("-"):
            option_string = option_string[1:]
        option_string = option_string.replace("-", "_")
        if values.lower() in ("true", "t", "yes", "y"):
            values = True
        elif values.lower() in ("false", "f", "no", "n"):
            values = False
        else:
            raise ValueError('Could not convert "%s" to boolean.' % values)
        setattr(namespace, option_string, values)
