"""Compile WRF.

Copyright (c) 2025 LATMOS (France, UMR 8190) and IGE (France, UMR 5001).

License: BSD 3-clause "new" or "revised" license (BSD-3-Clause).

"""

import sys
import os.path
import argparse
import json
import subprocess
import commons as cms


def get_argparser():
    """Return the object that parses command-line arguments.

    Returns
    -------
    argparse.ArgumentParser
        The object that parses command-line arguments.

    """
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
        "--commit",
        help="Git commit to use.",
        default="polar/main",
    )
    parser.add_argument(
        "--destination",
        help="Directory that will host the installation.",
        default="./WRF",
    )
    parser.add_argument(
        "--git",
        help="Git command (useful to use a non-default installation).",
        default="git",
    )
    parser.add_argument(
        "--script",
        help="Name of the installation script.",
        default="compile.job",
    )
    parser.add_argument(
        "--scheduler",
        help="Whether or not to compile in a scheduled job.",
        action=cms.ConvertToBoolean,
        default=False,
    )
    return parser


def get_options():
    """Return the pre-processed installation options.

    Options are read from the command line, and optionally from an "option
    file" (--optfile=/path/to/this/file at the command line). Command-line
    arguments have priority over the option file.

    Returns
    -------
    Namespace
        The pre-processed user-defined installation options.

    """
    parser = get_argparser()
    opts = parser.parse_args()
    if opts.optfile is not None:
        with open(opts.optfile) as f:
            opts_from_file = json.load(f)
        if not isinstance(opts_from_file, dict):
            raise ValueError("Option file must represent a JSON dictionnary.")
        for optname in opts_from_file:
            if optname not in opts:
                raise ValueError("Unknown option in file: %s." % optname)
        parser.set_defaults(**opts_from_file)
        opts = parser.parse_args()
    if opts.repository.startswith("http://"):
        raise ValueError("We do not allow http connections (not secure).")
    if cms.repo_is_local(opts.repository):
        opts.repository = cms.process_path(opts.repository)
    opts.destination = cms.process_path(opts.destination)
    return opts


def run(args, **kwargs):
    """Run given command and arguments as a subprocess.

    Parameters
    ----------
    args: sequence
        The command to run and its arguments, eg. ["grep", "-v", "some text"].
    kwargs: dict
        These are passed "as is" to subprocess.run.

    Raises
    ------
    RuntimeError
        If the command returns a non-zero exit code.

    """
    out = subprocess.run(args, **kwargs)
    if out.returncode != 0:
        msg = "Command '%s' exited with non-zero return code." % " ".join(args)
        raise RuntimeError(msg)


def clone_and_checkout(opts):
    """Clone the WRF repository and checkout the required commit.

    If the repository is local and if it is the same as the destination, then
    no git-cloning is done.

    Parameters
    ----------
    opts: Namespace
        The pre-processed user-defined installation options.

    """
    clone_it = (
        not cms.repo_is_local(opts.repository)
        or opts.repository != opts.destination
        or not os.path.lexists(opts.destination)
    )
    if clone_it:
        run([opts.git, "clone", opts.repository, opts.destination])
    run([opts.git, "checkout", opts.commit], cwd=opts.destination)


def slurm_options():
    """Prepare slurm options.

    Returns
    -------
    [str]
        The lines of text that contain the slurm options.

    """
    slurm = {
        "ntasks": "1",
        "ntasks-per-node": "1",
        "time": "01:00:00",
    }
    return ["#SBATCH --%s=%s" % (key, value) for key, value in slurm.items()]


def prepare_job_script(opts):
    """Create the job script.

    Parameters
    ----------
    opts: Namespace
        The pre-processed user-defined installation options.

    """
    # Platform, directories, and files
    host = cms.identify_host_platform()
    infra = cms.process_path(os.path.join(os.path.dirname(__file__), ".."))
    envfile = os.path.join(infra, "env", "%s.sh" % host)
    script = os.path.join(opts.destination, opts.script)

    # Prepare header of file (hash bang and scheduler options)
    lines = ["#!/bin/bash"]
    if opts.scheduler:
        if host in ("spirit",):
            lines += slurm_options()
        else:
            raise NotImplementedError("Unsupported host: %s." % host)

    # Platform-specific environment
    with open(envfile) as f:
        env = [line.strip() for line in f.readlines()]
    lines += [line for line in env if line != "" and not line.startswith("#")]
    netcdf = dict(spirit="$NETCDF_FORTRAN_ROOT")[host]
    hdf5 = dict(spirit="$HDF5_ROOT")[host]
    setup = dict(spirit=34)[host]
    nesting = 1

    # Add the call to ./configure
    lines += [
        "echo %d %d |\\" % (setup, nesting),
        "NETCDF=%s \\" % netcdf,
        "HDF5=%s \\" % hdf5,
        "./configure",
    ]

    # Add the call to ./compile
    lines += ["./compile em_real"]

    # Write the script
    with open(script, mode="x") as f:
        f.write("\n".join(lines))
        f.write("\n")
    run(["chmod", "744", opts.script], cwd=opts.destination)


if __name__ != "__main__":
    sys.exit(0)

host = cms.identify_host_platform()
print("Host platform is: %s" % host)

opts = get_options()
print("Options:", opts)

clone_and_checkout(opts)

prepare_job_script(opts)

if opts.scheduler:
    cmd = [dict(spirit="sbatch")[host], opts.script]
else:
    cmd = ["./%s" % opts.script]
run(cmd, cwd=opts.destination)
