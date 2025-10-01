"""Compile WRF.

Copyright (c) 2025 LATMOS (France, UMR 8190) and IGE (France, UMR 5001).

License: BSD 3-clause "new" or "revised" license (BSD-3-Clause).

"""

import sys
import os.path
import argparse
import json
import commons as cms


def prepare_argparser():
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
        "--components",
        help="A comma-separated list of additional WRF components to compile.",
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
    parser.add_argument(
        "--dry",
        help="Whether this is a dry run.",
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
    parser = prepare_argparser()
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
    if opts.components.strip() == "":
        opts.components = []
    else:
        opts.components = [comp.strip() for comp in opts.components.split(",")]
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


def prepare_slurm_options():
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


def prepare_components(opts):
    """Prepare WRF components.

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
    cmd = ["grep", "-E", "^      [a-zA-Z0-9]+).+=.+;;$", config_file]
    valid_comps = cms.run_stdout(cmd, cwd=opts.destination)
    valid_comps = [comp.split(")")[0].strip() for comp in valid_comps]
    if any(comp not in valid_comps for comp in opts.components):
        raise RuntimeError("There are some invalid WRF extra components.")
    components = " ".join(opts.components)
    return components if len(components) == 0 else " " + components


def prepare_environment_variables(opts):
    """Prepare the compilation environment variables.

    Parameters
    ----------
    opts: Namespace
        The pre-processed user-defined installation options.

    Returns
    -------
    [str]
        The lines setting environment variables.

    """
    host = cms.identify_host_platform()
    env_vars = dict(
        EM_CORE=1,
        NMM_CORE=0,
        NETCDF=dict(spirit="$NETCDF_FORTRAN_ROOT")[host],
        HDF5=dict(spirit="$HDF5_ROOT")[host],
    )
    # For some reason, just using the chem and kpp options is not enough, one
    # also has to explicitly set the corresponding environment variables
    if "chem" in opts.components:
        env_vars["WRF_CHEM"] = 1
    if "kpp" in opts.components:
        env_vars["WRF_KPP"] = 1
    # If non-standard, specify the location of the flex library explicitly
    if host == "spirit":
        env_vars["FLEX_LIB_DIR"] = "/usr/lib/x86_64-linux-gnu"
    # For KPP, we want header files to also be generated by (b)yacc (option -d)
    env_vars["YACC"] = "byacc -d"
    format_ = lambda v: str(v) if isinstance(v, int) else '"%s"' % v
    return ["export %s=%s" % (k, format_(v)) for k, v in env_vars.items()]


def write_job_script(opts):
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
            lines += prepare_slurm_options()
        else:
            raise NotImplementedError("Unsupported host: %s." % host)

    # Platform-specific environment
    with open(envfile) as f:
        env = [line.strip() for line in f.readlines()]
    lines += [line for line in env if line != "" and not line.startswith("#")]
    lines += prepare_environment_variables(opts)
    setup = dict(spirit=34)[host]
    nesting = 1

    # Add the call to ./configure
    lines.append('echo -e "%d\\n%d" | \\' % (setup, nesting))
    lines.append("./configure%s" % prepare_components(opts))

    # Add the call to ./compile
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
    cmd = ["git", "rev-parse", "HEAD"]
    opts_dict["commit"] = cms.run_stdout(cmd, cwd=opts.destination)[0]
    opts_dict["components"] = ",".join(opts_dict["components"])
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
    cmd = ["find", opts.patches, "-type", "f", "-name", "*.patch"]
    patches = [cms.process_path(patch) for patch in cms.run_stdout(cmd)]
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
    cmd = ["find", opts.sources, "-type", "f"]
    sources = [cms.process_path(src) for src in cms.run_stdout(cmd)]
    n = len(opts.sources) + 1
    for src in sources:
        path_in_repo = os.path.join(opts.destination, src[n:])
        cms.run(["cp", "-v", src, path_in_repo])


if __name__ == "__main__":
    # Actually do the work (parse user options, checkout, compile)

    host = cms.identify_host_platform()
    opts = get_options()

    clone_and_checkout(opts)
    write_options(opts)
    process_patches(opts)
    process_extra_sources(opts)
    write_job_script(opts)

    if opts.dry:
        sys.exit(0)

    if opts.scheduler:
        cmd = [dict(spirit="sbatch")[host], "compile.job"]
    else:
        cmd = ["./compile.job"]
    cms.run(cmd, cwd=opts.destination)
