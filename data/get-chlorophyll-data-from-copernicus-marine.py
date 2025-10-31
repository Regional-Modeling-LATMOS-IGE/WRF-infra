# Copyright (c) 2025 LATMOS (France, UMR 8190) and IGE (France, UMR 5001).
#
# License: BSD 3-clause "new" or "revised" license (BSD-3-Clause).

"""Get total chlorophyll ocean concentration data from Copernicus Marine.

To use this script, you must have an account at https://marine.copernicus.eu/.

The copernicusmarine package can be installed via pip or conda-forge.

This script is made to fit our typical usage for WRF-Chem-Polar, namely:

 - we extract data for only one variable (chl=total chlorophyll).
 - we extract data for the entire globe.
 - we extract data for the first depth layer only.

"""

import os
import argparse
import datetime
import copernicusmarine

# Command-line arguments

parser = argparse.ArgumentParser(
    description="Download total chlorophyll data from Copernicus Marine",
    formatter_class=argparse.RawDescriptionHelpFormatter,
)
parser.add_argument(
    "--start",
    help="Start date (format YYYY-MM-DD).",
    required=True,
)
parser.add_argument(
    "--end",
    help="End date, included (format YYYY-MM-DD).",
    required=True,
)
parser.add_argument(
    "--filename",
    help="Name of the output file (auto-generated if not specified).",
    default="",
)
parser.add_argument(
    "--temporal-resolution",
    help="Temporal resolution of the downloaded data.",
    choices=("monthly", "daily"),
    default="daily",
)
args = parser.parse_args()

start = datetime.datetime.strptime(args.start, "%Y-%m-%d")
end = datetime.datetime.strptime(args.end, "%Y-%m-%d")

if args.filename.strip() == "":
    args.filename = "copernicus-marine_total-chlorophyll_%s-%s_%s.nc" % (
        args.start,
        args.end,
        args.temporal_resolution,
    )

temporal_resolution = args.temporal_resolution[0].upper()

# Ask user for Copernicus Marine credentials if needed

credentials_file = os.path.join(
    os.path.expanduser("~"),
    ".copernicusmarine",
    ".copernicusmarine-credentials",
)
if not os.path.exists(credentials_file):
    print(
        "It looks like you have not registered your Copernicus Marine\n"
        "credentials on this machine, so let us do it now.\n"
        "Please log in with your Copernicus Marine credentials:"
    )
    copernicusmarine.login()

# Extract the data

depth_first_layer = 0.5057600140571594

info = copernicusmarine.subset(
    dataset_id="cmems_mod_glo_bgc_my_0.25deg_P1%s-m" % temporal_resolution,
    variables=["chl"],
    minimum_longitude=-180,
    maximum_longitude=180,
    minimum_latitude=-80,
    maximum_latitude=90,
    start_datetime=start.strftime("%Y-%m-%dT00:00:00"),
    end_datetime=end.strftime("%Y-%m-%dT23:59:59"),
    minimum_depth=depth_first_layer,
    maximum_depth=depth_first_layer,
    output_filename=args.filename,
)
