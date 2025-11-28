#!/bin/sh
#
# Copyright (c) 2025 LATMOS (France, UMR 8190) and IGE (France, UMR 5001).
#
# License: BSD 3-clause "new" or "revised" license (BSD-3-Clause).
#
# Environment for WRF on Spirit.

CONDA_EXE="/proju/wrf-chem/software/micromamba/micromamba"
CONDA_ROOT_PREFIX="/proju/wrf-chem/software/conda-envs/shared"
CONDA_ENV_NAME="WRF-Chem-Polar_2025-10-21"
CONDA_RUN="$CONDA_EXE run --root-prefix=$CONDA_ROOT_PREFIX --name=$CONDA_ENV_NAME"

NETCDF_FORTRAN_ROOT="$CONDA_ROOT_PREFIX/envs/$CONDA_ENV_NAME"
HDF5_ROOT="$CONDA_ROOT_PREFIX/envs/$CONDA_ENV_NAME"
