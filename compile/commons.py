"""Common resources for compilation scripts.

Copyright (c) 2025 LATMOS (France, UMR 8190) and IGE (France, UMR 5001).

License: BSD 3-clause "new" or "revised" license (BSD-3-Clause).

"""

import os
import functools
import argparse
import subprocess
import json

URL_GITHUB = "https://github.com"
URL_GROUP_WRF = "%s/wrf-model" % URL_GITHUB
URL_WPS = "%s/WPS.git" % URL_GROUP_WRF
URL_GROUP_LATMOS_IGE = "%s/Regional-Modeling-LATMOS-IGE" % URL_GITHUB
URL_WRFCHEMPOLAR = "%s/WRF-Chem-Polar.git" % URL_GROUP_LATMOS_IGE


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


@functools.lru_cache
def identify_host_platform():
    """Return the identity of the host platform.

    Returns
    -------
    str
        The identity of the host platform.

    """
    known_plateforms = {
        "spirit1.ipsl.fr": "spirit",
        "spirit2.ipsl.fr": "spirit",
    }
    nodename = os.uname().nodename
    try:
        platform = known_plateforms[nodename]
    except KeyError:
        raise NotImplementedError("Unknown host platform: %s." % nodename)
    return platform


def process_path(path):
    """Return a unique absolute version of given path.

    Parameters
    ----------
    path: str | None
        The path to process.

    Returns
    -------
    str | None
        The unique and absolute version of given path (or None if given path is
        empty or None)

    """
    if path is None or path.strip() == "":
        return None
    else:
        return os.path.abspath(os.path.expanduser(path))


@functools.lru_cache
def path_of_repo():
    """Return the path to the root of the repository that contains this file.

    Returns
    -------
    str
        The path to the root of the repository that contains this file.

    """
    path = os.path.dirname(__file__)
    if path == "":
        path = "."
    return process_path(os.path.join(path, ".."))


def repo_is_local(repository):
    """Return whether given repository address is local.

    This function only looks at the format of the given character string.
    Whether the repository is local or remote, this function does not check if
    the repository exists or not.

    Returns
    -------
    bool
        True if given address is local, False otherwise.

    """
    return (
        "@" not in repository
        and not repository.startswith("http://")
        and not repository.startswith("https://")
    )


def run(args, **kwargs):
    """Run given command and arguments as a subprocess.

    Parameters
    ----------
    args: sequence
        The command to run and its arguments, eg. ["grep", "-v", "some text"].
    kwargs: dict
        These are passed "as is" to subprocess.run.

    Returns
    -------
    subprocess.CompletedProcess
        The result of running the command.

    Raises
    ------
    RuntimeError
        If the command returns a non-zero exit code.

    """
    out = subprocess.run(args, **kwargs)
    if out.returncode != 0:
        msg = "Command '%s' exited with non-zero return code." % " ".join(args)
        raise RuntimeError(msg)
    return out


def run_stdout(args, **kwargs):
    """Run given command and arguments as a subprocess and return stdout.

    Parameters
    ----------
    args: sequence
        The command to run and its arguments, eg. ["grep", "-v", "some text"].
    kwargs: dict
        These are passed "as is" to subprocess.run, but cannot contain
        "capture_output" nor "text".

    Returns
    -------
    [str]
        The standard output of the command (one string per line).

    Raises
    ------
    RuntimeError
        If the command returns a non-zero exit code.

    """
    for kwarg in ("capture_output", "text"):
        if kwarg in kwargs:
            raise ValueError("Keyword argument %s is forbidden." % kwarg)
    out = run(args, capture_output=True, text=True, **kwargs)
    return out.stdout[:-1].split("\n")


def prepare_argparser(which):
    """Return the object that parses command-line arguments.

    Parameters
    ----------
    which: "WPS" | "WRF"
        Which model are we trying to compile here?

    Returns
    -------
    argparse.ArgumentParser
        The object that parses command-line arguments.

    """
    # "which"-dependent default values
    if which == "WPS":
        repository = URL_WPS
        commit = "master"
        patches = os.path.join(path_of_repo(), "compile", "patches_WPS")
    elif which == "WRF":
        repository = URL_WRFCHEMPOLAR
        commit = "polar/main"
        patches = None
    else:
        raise Exception("Invalid choice: %s." % which)

    # Common command-line arguments
    parser = argparse.ArgumentParser(
        description="Compile %s." % which,
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
        default=repository,
    )
    parser.add_argument(
        "--commit",
        help="Git commit to use.",
        default=commit,
    )
    parser.add_argument(
        "--destination",
        help="Directory that will host the installation.",
        default="./%s" % which,
    )
    parser.add_argument(
        "--git",
        help="Git command (useful to use a non-default installation).",
        default="git",
    )
    parser.add_argument(
        "--scheduler",
        help="Whether or not to compile in a scheduled job.",
        action=ConvertToBoolean,
        default=False,
    )
    parser.add_argument(
        "--patches",
        help="Path to directory containing patches.",
        default=patches,
    )
    parser.add_argument(
        "--sources",
        help="Path to directory containing extra sources.",
        default=None,
    )
    parser.add_argument(
        "--dry",
        help="Whether this is a dry run.",
        action=ConvertToBoolean,
        default=False,
    )

    # "which"-dependent command-line arguments
    if which == "WPS":
        parser.add_argument(
            "--wrf-dir",
            help="Directory where WRF is installed.",
            default="./WRF",
        )
    elif which == "WRF":
        parser.add_argument(
            "--executable",
            help="Which WRF executable to compile.",
            default="em_real",
        )
        parser.add_argument(
            "--components",
            help="A comma-separated list of extra WRF components to compile.",
            default="kpp,chem",
        )
    else:
        raise Exception("Invalid choice: %s." % which)

    return parser


def get_options(which):
    """Return the pre-processed installation options.

    Options are read from the command line, and optionally from an "option
    file" (--optfile=/path/to/this/file at the command line). Command-line
    arguments have priority over the option file.

    Parameters
    ----------
    which: "WPS" | "WRF"
        Which model are we trying to compile here?

    Returns
    -------
    Namespace
        The pre-processed user-defined installation options.

    """
    parser = prepare_argparser(which)
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
    if repo_is_local(opts.repository):
        opts.repository = process_path(opts.repository)
    opts.destination = process_path(opts.destination)
    if "components" in opts:
        if opts.components.strip() == "":
            opts.components = []
        else:
            opts.components = [
                comp.strip() for comp in opts.components.split(",")
            ]
    opts.patches = process_path(opts.patches)
    opts.sources = process_path(opts.sources)
    return opts


def clone_and_checkout(opts):
    """Clone the repository and checkout the required commit.

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
    run([opts.git, "clone", "--quiet", opts.repository, opts.destination])
    run([opts.git, "checkout", "--quiet", opts.commit], cwd=opts.destination)


def prepare_slurm_options(time):
    """Prepare slurm options.

    Parameters
    ----------
    time: str
        The wall time requested for the job with format HH:MM:SS.

    Returns
    -------
    [str]
        The lines of text that contain the slurm options.

    """
    host = identify_host_platform()
    slurm = {
        "ntasks": "1",
        "ntasks-per-node": "1",
        "time": time,
    }
    if host == "spirit":
        slurm["partition"] = "zen16"
        slurm["mem"] = "12GB"
    return ["#SBATCH --%s=%s" % (key, value) for key, value in slurm.items()]


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
    opts_dict["commit"] = run_stdout(cmd, cwd=opts.destination)[0]
    if "components" in opts_dict:
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
    patches = [process_path(patch) for patch in run_stdout(cmd)]
    n = len(opts.patches) + 1
    for patch in patches:
        path_in_repo = os.path.join(opts.destination, patch[n:-6])
        if os.path.exists(path_in_repo):
            run(["patch", path_in_repo, patch])
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
    sources = [process_path(src) for src in run_stdout(cmd)]
    n = len(opts.sources) + 1
    for src in sources:
        path_in_repo = os.path.join(opts.destination, src[n:])
        run(["cp", "-v", src, path_in_repo])
