# Copyright (c) 2025 LATMOS (France, UMR 8190) and IGE (France, UMR 5001).
#
# License: BSD 3-clause "new" or "revised" license (BSD-3-Clause).

"""Install the computing environment required for WRF-Chem-Polar.

This script is mostly a wrapper to run conda (or one of its sisters such as
mamba or micromamba) to install the computing environment specified in the
repository's pyproject.toml file.

"""

import os
import argparse
import tomllib
import commons

# Command-line arguments

# Default values
host = commons.identify_host_platform()
env_name = "WRF-Chem-Polar"
env_root_prefix = "~/conda-envs"
conda = "micromamba"
if host == "spirit":
    env_root_prefix = "/proju/wrf-chem/software/conda-envs/shared"
    conda = "/proju/wrf-chem/software/micromamba/micromamba"

parser = argparse.ArgumentParser(
    description="Install the environment to compile and run WRF-Chem-Polar.",
    formatter_class=argparse.RawDescriptionHelpFormatter,
)
parser.add_argument(
    "--env-root-prefix",
    help="Location of the root directory for conda environments.",
    default=env_root_prefix,
)
parser.add_argument(
    "--env-name",
    help="Name of the conda environment.",
    default=env_name,
)
parser.add_argument(
    "--conda",
    help="The conda-like program to use.",
    default=conda,
)
parser.add_argument(
    "--optional-dependencies",
    help=(
        "Comma-separated groups of optional dependencies to install "
        "(* to install all of them)."
    ),
    default="",
)
parser.add_argument(
    "--find",
    help="Path to the find command.",
    default="/usr/bin/find",
)
parser.add_argument(
    "--chmod",
    help="Path to the chmod command.",
    default="/usr/bin/chmod",
)
args = parser.parse_args()

# We refuse to overwrite an existing environment

env_dir = os.path.join(args.env_root_prefix, "envs", args.env_name)
if os.path.lexists(commons.process_path(env_dir)):
    raise RuntimeError(
        "The destination directory already exists. "
        "Please remove it manually and re-run this script."
    )

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
    args.env_root_prefix,
    "--name",
    args.env_name,
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

# Fix permissions:
#  - To current user and group members: read and execute acces.
#  - To others: no rights.


def exec_chmod(chmod, perm):
    """Return the piece of command to run chmod with "find ... -exec ...".

    Parameters
    ----------
    chmod: str
        The chmod command to use.
    perm: str
        The permissions to give (eg. "550", "u+x", etc.).

    Returns
    -------
    list
        The end of the find command, starting at "-exec", as a list of
        arguments.

    """
    return ["-exec", args.chmod, perm, "{}", ";"]


# Executable files
commons.run_stdout(
    [args.find, "-type", "f", "-perm", "-u=x"] + exec_chmod(args.chmod, "550"),
    cwd=args.env_root_prefix,
)

# Non-executable files
commons.run_stdout(
    [args.find, "-type", "f", "!", "-perm", "550"]
    + exec_chmod(args.chmod, "440"),
    cwd=args.env_root_prefix,
)

# Directories
commons.run_stdout(
    [args.find, "-type", "d"] + exec_chmod(args.chmod, "550"),
    cwd=args.env_root_prefix,
)
