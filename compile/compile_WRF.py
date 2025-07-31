"""Compile WRF.

Copyright (c) 2025 LATMOS (France, UMR 8190) and IGE (France, UMR 5001).

License: BSD 3-clause "new" or "revised" license (BSD-3-Clause).

"""

import sys
import os.path
import argparse
import json
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
        help="File containing compilation options (JSON format).",
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
        "--scheduler",
        help="Whether or not to compile in a scheduled job.",
        action=cms.ConvertToBoolean,
        default=False,
    )
    parser.add_argument(
        "--executable",
        help="Which WRF executable to compile.",
        default="em_real",
    )
    parser.add_argument(
        "--wrfoptions",
        help="A comma-separated list of WRF options.",
        default="kpp,chem",
    )
    parser.add_argument(
        "--patches",
        help="Path to directory containing patches.",
        default=None,
    )
    parser.add_argument(
        "--sources",
        help="Path to directory containing extra sources.",
        default=None,
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
    if opts.wrfoptions.strip() == "":
        opts.wrfoptions = []
    else:
        opts.wrfoptions = [i.strip() for i in opts.wrfoptions.split(",")]
    opts.patches = cms.process_path(opts.patches)
    opts.sources = cms.process_path(opts.sources)
    return opts


def clone_and_checkout(opts):
    """Clone the WRF repository and checkout the required commit.

    Parameters
    ----------
    opts: Namespace
        The pre-processed user-defined installation options.

    Raises
    ------
    RuntimeError
        If the destination already exists.

    """
    if os.path.exists(opts.destination):
        raise RuntimeError("Destination directory already exists.")
    cms.run([opts.git, "clone", opts.repository, opts.destination])
    cms.run([opts.git, "checkout", opts.commit], cwd=opts.destination)


def slurm_options():
    """Prepare slurm options.

    Returns
    -------
    [str]
        The lines of text that contain the slurm options.

    """
    host = cms.identify_host_platform()
    slurm = {
        "ntasks": "1",
        "ntasks-per-node": "1",
        "time": "02:30:00",
    }
    if host == "spirit":
        slurm["partition"] = "zen16"
        slurm["mem"] = "12GB"
    return ["#SBATCH --%s=%s" % (key, value) for key, value in slurm.items()]


def wrf_options(opts):
    """Prepare WRF options.

    Parameters
    ----------
    opts: Namespace
        The pre-processed user-defined installation options.

    Returns
    -------
    str
        The WRF options, formatted to be passed to the configure script.

    """
    config_file = os.path.join(opts.destination, "configure")
    valid_options = cms.run(
        ["grep", "-E", "^      [a-zA-Z0-9]+).+=.+;;$", config_file],
        cwd=opts.destination,
        capture_output=True,
        text=True,
    ).stdout
    valid_options = valid_options[:-1].split("\n")
    valid_options = [option.split(")")[0].strip() for option in valid_options]
    if any(option not in valid_options for option in opts.wrfoptions):
        raise RuntimeError("There are some invalid WRF options.")
    options = " ".join(opts.wrfoptions)
    return options if len(options) == 0 else " " + options


def environment_variables(opts):
    """Prepare the compilation environment variables.

    Parameters
    ----------
    opts: Namespace
        The pre-processed user-defined installation options.

    Returns
    -------
    [str]
        The lines setting environment variables (to prepend to installation
        scripts, namely configure and compile).

    """
    host = cms.identify_host_platform()
    env_vars = dict(
        NETCDF=dict(spirit="$NETCDF_FORTRAN_ROOT")[host],
        HDF5=dict(spirit="$HDF5_ROOT")[host],
    )
    # For some reason, just using the kpp option is not enough, one also has to
    # explicitly set the WRF_KPP variable
    if "kpp" in opts.wrfoptions:
        env_vars["WRF_KPP"] = "1"
    # If non-standard, specify the location of the flex library explicitly
    if host == "spirit":
        env_vars["FLEX_LIB_DIR"] = "/usr/lib/x86_64-linux-gnu"
    # For KPP, we want header files to also be generated by (b)yacc (option -d)
    env_vars["YACC"] = "byacc -d"
    return ['%s="%s" \\' % (k, v) for k, v in env_vars.items()]


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
    script = os.path.join(opts.destination, "compile.job")

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
    env_vars = environment_variables(opts)
    setup = dict(spirit=34)[host]
    nesting = 1

    # Add the call to ./configure
    lines.append("echo %d %d | \\" % (setup, nesting))
    lines += env_vars
    lines.append("./configure%s" % wrf_options(opts))

    # Add the call to ./compile
    lines += env_vars
    lines.append("./compile %s" % opts.executable)

    # Write the script
    with open(script, mode="x") as f:
        f.write("\n".join(lines))
        f.write("\n")
    cms.run(["chmod", "744", script], cwd=opts.destination)


def write_options(opts):
    """Write installation options into file for future reproducibility.

    Parameters
    ----------
    opts: Namespace
        The pre-processed user-defined installation options.

    """
    opts_dict = dict((key, value) for key, value in vars(opts).items())
    opts_dict.pop("optfile")
    opts_dict.pop("destination")
    opts_dict["commit"] = cms.run(
        ["git", "rev-parse", "HEAD"],
        cwd=opts.destination,
        capture_output=True,
        text=True,
    ).stdout[:-1]
    opts_dict["wrfoptions"] = ",".join(opts_dict["wrfoptions"])
    optfile = os.path.join(opts.destination, "compile.json")
    with open(optfile, mode="x") as f:
        json.dump(opts_dict, f, sort_keys=True, indent=4)
        f.write("\n")


def process_patches(opts):
    """Apply patches, if any.

    Parameters
    ----------
    opts: Namespace
        The pre-processed user-defined installation options.

    """
    if opts.patches is None:
        return
    patches = cms.run(
        ["find", opts.patches, "-type", "f", "-name", "*.patch"],
        capture_output=True,
        text=True,
    ).stdout[:-1]
    patches = [cms.process_path(patch) for patch in patches.split("\n")]
    n = len(opts.patches) + 1
    for patch in patches:
        path_in_repo = os.path.join(opts.destination, patch[n:-6])
        if os.path.exists(path_in_repo):
            cms.run(["patch", path_in_repo, patch])
        else:
            msg = "Warning: file %s does not exist so cannot be patched."
            print(msg % path_in_repo)


def process_extra_sources(opts):
    """Copy extra source files, if any, to the repository.

    Parameters
    ----------
    opts: Namespace
        The pre-processed user-defined installation options.

    """
    if opts.sources is None:
        return
    sources = cms.run(
        ["find", opts.sources, "-type", "f"],
        capture_output=True,
        text=True,
    ).stdout[:-1]
    sources = [cms.process_path(src) for src in sources.split("\n")]
    n = len(opts.sources) + 1
    for src in sources:
        path_in_repo = os.path.join(opts.destination, src[n:])
        cms.run(["cp", "-v", src, path_in_repo])


if __name__ != "__main__":
    sys.exit(0)

host = cms.identify_host_platform()
print("Host platform is: %s" % host)

opts = get_options()
print("Options:", opts)

clone_and_checkout(opts)

write_options(opts)

prepare_job_script(opts)

process_patches(opts)

process_extra_sources(opts)

if opts.scheduler:
    cmd = [dict(spirit="sbatch")[host], "compile.job"]
else:
    cmd = ["./compile.job"]
cms.run(cmd, cwd=opts.destination)
