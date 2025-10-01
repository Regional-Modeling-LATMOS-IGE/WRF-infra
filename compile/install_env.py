# Copyright (c) 2025 LATMOS (France, UMR 8190) and IGE (France, UMR 5001).
#
# License: BSD 3-clause "new" or "revised" license (BSD-3-Clause).

"""Install the computing environment required for WRF-Chem-Polar.

This script is mostly a wrapper to run conda (or one of its sisters such as
mamba or micromamba) to install the computing environment specified in the
repository's pyproject.toml file.

"""

import argparse
import os.path
import tomllib
import commons

# Command-line arguments

parser = argparse.ArgumentParser(
    description="Install the environment to compile and run WRF-Chem-Polar.",
    formatter_class=argparse.RawDescriptionHelpFormatter,
)
parser.add_argument(
    "--destination",
    help=(
        "Directory that will host the environment. For security reasons, this"
        "directory will not be removed by this script. This script will stop "
        "prematurely if the destination directory already exists. "
    ),
    default="~/conda-environments/env_WRF-Chem-Polar",
)
parser.add_argument(
    "--conda",
    help="The conda-like program to use.",
    default="micromamba",
)
parser.add_argument(
    "--optional-dependencies",
    help=(
        "Comma-separated groups of optional dependencies to install "
        "(* to install all of them)."
    ),
    default="",
)
args = parser.parse_args()

# Location where the environment will be installed

destination = commons.process_path(args.destination)
if os.path.lexists(destination):
    raise RuntimeError(
        "The destination directory alreay exists. "
        "Please remove it manually and re-run this script."
    )
dir_envs, env_name = os.path.split(destination)

# Parse the pyproject.toml file

file_pyproject = os.path.join(commons.path_of_repo(), "pyproject.toml")
with open(file_pyproject, mode="rb") as f:
    pyproject = tomllib.load(f)
python = pyproject["project"]["requires-python"].replace(" ", "")
dependencies = pyproject["project"]["dependencies"]

# Prepare and run the conda-like command

cmd = [
    os.path.expanduser(args.conda),
    "create",
    "--no-rc",
    "--no-env",
    "--root-prefix",
    dir_envs,
    "--name",
    env_name,
    "--channel",
    "conda-forge",
    "--override-channels",
    "--strict-channel-priority",
    "--yes",
    "python%s" % python,
] + dependencies

# Add optional dependencies
known_groups = pyproject["project"]["optional-dependencies"]
for group in [g.strip() for g in args.optional_dependencies.split(",")]:
    if group == "":
        continue
    try:
        deps = known_groups[group]
    except KeyError:
        raise ValueError("Unknown group of optional dependencies: %s." % group)
    cmd += deps

commons.run(cmd)
