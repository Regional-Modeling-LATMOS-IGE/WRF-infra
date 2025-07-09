"""Compile WRF.

Copyright (c) 2025 LATMOS (France, UMR 8190) and IGE (France, UMR 5001).

License: BSD 3-clause "new" or "revised" license (BSD-3-Clause).

"""

import os
import os.path
import argparse
import json
import subprocess
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
    return parser


def get_options():
    """Get and pre-process the installation options.

    Command-line arguments have priority over options specified in the
    (optional) option file.

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
    if repo_is_local(opts.repository):
        opts.repository = process_path(opts.repository)
    opts.destination = process_path(opts.destination)
    return opts


def repo_is_local(repository):
    """Return True iff given repository address is local.

    This function only looks at the format of the given character
    string. Whether the repository is local or remote, this function does not
    check if the repository exists or not.

    """
    return (not "@" in repository
            and not repository.startswith("http://")
            and not repository.startswith("https://"))


def process_path(path):
    """Return a (hopefully) unique absolute version of given path."""
    return os.path.abspath(os.path.expanduser(path))


def run(args, **kwargs):
    """Run given command+arguments as a subprocess, exception if problem."""
    out = subprocess.run(args, **kwargs)
    if out.returncode != 0:
        msg = "Command '%s' exited with non-zero return code." % " ".join(args)
        raise RuntimeError(msg)


def clone_and_checkout(opts):
    """Clone the WRF code and checkout the required commit.

    If the repository is local and if it is the same as the destination, then
    no git-cloning is done.

    """
    clone_it = (not repo_is_local(opts.repository)
                or opts.repository != opts.destination
                or not os.path.lexists(opts.destination))
    if clone_it:
        run([opts.git, "clone", opts.repository, opts.destination])
    run([opts.git, "checkout", opts.commit], cwd=opts.destination)


if __name__ == "__main__":

    host = identify_host_platform()
    print("Host platform is: %s" % host)

    opts = get_options()
    print("Options:", opts)

    clone_and_checkout(opts)
