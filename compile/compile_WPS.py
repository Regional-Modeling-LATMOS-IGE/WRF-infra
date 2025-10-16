"""Compile WPS.

Copyright (c) 2025 LATMOS (France, UMR 8190) and IGE (France, UMR 5001).

License: BSD 3-clause "new" or "revised" license (BSD-3-Clause).

"""

import sys
import os.path
import commons as cms


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
    env_vars = dict(
        NETCDF="$NETCDF_FORTRAN_ROOT",
        HDF5="$HDF5_ROOT",
        WRF_DIR=cms.process_path(opts.wrf_dir),
    )
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
    envfile = os.path.join(cms.path_of_repo(), "env", "%s.sh" % host)
    script = os.path.join(opts.destination, "compile.job")

    # Prepare header of file (hash bang and scheduler options)
    lines = ["#!/bin/bash"]
    if opts.scheduler:
        if host in ("spirit",):
            lines += cms.prepare_slurm_options("00:30:00")
        else:
            raise NotImplementedError("Unsupported host: %s." % host)

    # Platform-specific environment
    with open(envfile) as f:
        env = [line.strip() for line in f.readlines()]
    lines += [line for line in env if line != "" and not line.startswith("#")]
    lines += prepare_environment_variables(opts)
    setup = dict(spirit=1)[host]

    # Add the call to ./configure and ./compile
    lines.append('echo -e "%d" | \\' % setup)
    lines.append("$CONDA_RUN ./configure --build-grib2-libs")
    lines.append("$CONDA_RUN ./compile")

    # Write the script
    with open(script, mode="x") as f:
        f.write("\n".join(lines))
        f.write("\n")
    cms.run(["chmod", "744", script], cwd=opts.destination)


if __name__ == "__main__":
    # Actually do the work (parse user options, checkout, compile)

    host = cms.identify_host_platform()
    opts = cms.get_options("WPS")

    cms.clone_and_checkout(opts)
    cms.write_options(opts)
    cms.process_patches(opts)
    cms.process_extra_sources(opts)
    write_job_script(opts)

    if opts.dry:
        sys.exit(0)

    if opts.scheduler:
        cmd = [dict(spirit="sbatch")[host], "compile.job"]
    else:
        cmd = ["./compile.job"]
    cms.run(cmd, cwd=opts.destination)
