"""Common resources for compilation scripts.

Copyright (c) 2025 LATMOS (France, UMR 8190) and IGE (France, UMR 5001).

License: BSD 3-clause "new" or "revised" license (BSD-3-Clause).

"""

import os
import functools
import argparse
import subprocess

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
